from __future__ import annotations

from copy import deepcopy
import concurrent.futures
import gc
import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import RLock
from typing import Any

from ..config import AppSettings
from ..database import Database
from ..models.registry import ModelRegistry
from ..schemas import ModelChatRequest, ModelDownloadRequest, ModelLoadRequest, ModelRunRequest, ModelTagSelectionRequest
from .gpu_service import detect_devices
from .media_service import MediaService
from .model_lifecycle import ModelLifecycleTracker
from .tag_service import TagService


class ModelService:
    def __init__(self, db: Database, registry: ModelRegistry, media: MediaService, tags: TagService, settings: AppSettings | None = None):
        self.db = db
        self.registry = registry
        self.media = media
        self.tags = tags
        self.settings = settings
        self.lifecycle = ModelLifecycleTracker()
        self._placement_lock = RLock()
        self._placements: dict[str, dict[str, Any]] = {}
        self._pending_placements: dict[str, dict[str, Any]] = {}
        # Shared VRAM-reservation state for placement planning, active loads,
        # loaded models, and the UI status panel.
        self._resource_lock = self._placement_lock
        self._loading_reservations = self._pending_placements
        self._catalog_cache_rows: list[dict[str, Any]] | None = None
        self._catalog_cache_ts: float = 0.0
        self._catalog_cache_ttl: float = 20.0
        self.ensure_chat_tables()

    def ensure_chat_tables(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS chat_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'Untitled conversation',
                model_name TEXT NOT NULL DEFAULT 'dataset-assistant',
                dataset_id INTEGER,
                state_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                archived INTEGER NOT NULL DEFAULT 0
            )"""
        )
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                model_name TEXT NOT NULL DEFAULT '',
                context_json TEXT NOT NULL DEFAULT '{}',
                response_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id, id)")

    @staticmethod
    def _parse_device_indices(value: Any) -> list[int]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            raw_items = value
        else:
            raw_items = re.split(r"[;,\s]+", str(value or ""))
        out: list[int] = []
        for item in raw_items:
            text = str(item).strip().lower().replace("cuda:", "")
            if not text:
                continue
            try:
                idx = int(text)
            except Exception:
                continue
            if idx >= 0 and idx not in out:
                out.append(idx)
        return out

    @staticmethod
    def _parse_memory_gb(value: Any) -> float | None:
        if value is None:
            return None
        text = str(value).strip().lower().replace("gib", "gb").replace("mib", "mb")
        if not text:
            return None
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*([a-z]+)?$", text)
        if not m:
            return None
        amount = float(m.group(1))
        unit = m.group(2) or "gb"
        if unit in {"mb", "m"}:
            return round(amount / 1024.0, 3)
        if unit in {"tb", "t"}:
            return round(amount * 1024.0, 3)
        return round(amount, 3)

    def _gpu_device_map(self) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
        payload = detect_devices()
        devices: dict[int, dict[str, Any]] = {}
        for dev in payload.get("devices", []):
            dev_id = str(dev.get("id") or "")
            if not dev_id.startswith("cuda:"):
                continue
            try:
                idx = int(dev_id.split(":", 1)[1])
            except Exception:
                idx = int(dev.get("index")) if str(dev.get("index", "")).isdigit() else len(devices)
            item = dict(dev)
            item.setdefault("index", idx)
            devices[idx] = item
        return devices, payload

    def _selected_gpu_ids(self, request: Any, record: Any | None = None, gpu_map: dict[int, dict[str, Any]] | None = None) -> list[int]:
        gpu_map = gpu_map or self._gpu_device_map()[0]
        available = sorted(gpu_map)
        raw = self._parse_device_indices(getattr(request, "device_ids", None))
        if raw:
            return raw
        device = str(getattr(request, "device", "auto") or "auto").strip().lower()
        parsed_from_device = self._parse_device_indices(device) if ("cuda" in device or "," in device or ";" in device) else []
        if parsed_from_device:
            return parsed_from_device
        if device == "cpu" or not available:
            return []
        placement_warning = ""
        strategy = str(getattr(request, "sharding_strategy", "none") or "none").lower()
        min_gpus = max(1, int(getattr(record, "min_gpus", 1) or 1)) if record else 1
        if strategy != "none":
            return available[: max(min_gpus, 1)] if min_gpus > 1 else available
        if min_gpus > 1:
            return available[:min_gpus]
        return [available[0]]

    def _model_memory_profiles(self, record: Any) -> dict[str, float]:
        profiles = dict(getattr(record, "runtime_vram_profiles", {}) or {})
        out: dict[str, float] = {}
        for key, value in profiles.items():
            try:
                v = float(value)
            except Exception:
                continue
            if v > 0:
                out[str(key).lower()] = round(v, 3)
        return out

    def _profiled_vram_estimate_gb(self, record: Any, request: Any | None = None) -> float | None:
        profiles = self._model_memory_profiles(record)
        if not profiles:
            return None
        quant = str(getattr(request, "quantization", "none") or "none").lower() if request is not None else "none"
        dtype = str(getattr(request, "torch_dtype", "auto") or "auto").lower().replace("torch.", "") if request is not None else "auto"
        if quant in {"4bit", "int4", "q4", "q4_0"}:
            return profiles.get("4bit") or profiles.get("q4_0") or profiles.get("int4")
        if quant in {"8bit", "int8", "sfp8", "fp8"}:
            return profiles.get("8bit") or profiles.get("sfp8") or profiles.get("fp8") or profiles.get("int8")
        if dtype in {"bfloat16", "bf16"}:
            return profiles.get("bf16") or profiles.get("bfloat16") or profiles.get("fp16")
        if dtype in {"float16", "fp16", "half"}:
            return profiles.get("fp16") or profiles.get("float16") or profiles.get("bf16")
        if dtype in {"float32", "fp32"}:
            base = profiles.get("fp32") or profiles.get("float32")
            if base:
                return base
            half = profiles.get("bf16") or profiles.get("fp16")
            return round(half * 1.85, 3) if half else None
        # Auto defaults to the catalog's official/default 16-bit runtime value
        # when available. Alternatives are exposed in UI/errors.
        return profiles.get("bf16") or profiles.get("fp16") or profiles.get("bfloat16") or profiles.get("float16")

    def _model_vram_estimate_gb(self, record: Any, request: Any) -> float:
        if not record or getattr(record, "cloud", False) or getattr(record, "provider", "") in {"builtin", "cloud", "openai", "openrouter", "anthropic"}:
            return 0.0
        device = str(getattr(request, "device", "auto") or "auto").strip().lower()
        if device == "cpu":
            return 0.0
        profiled = self._profiled_vram_estimate_gb(record, request)
        if profiled is not None:
            return round(max(0.0, float(profiled)), 3)
        base = getattr(record, "vram_gb", None)
        if base is None:
            base = getattr(record, "size_gb", None)
        try:
            est = float(base or 0.0)
        except Exception:
            est = 0.0
        quant = str(getattr(request, "quantization", "none") or "none").lower()
        dtype = str(getattr(request, "torch_dtype", "auto") or "auto").lower()
        if quant == "4bit" and est:
            est *= 0.40
        elif quant == "8bit" and est:
            est *= 0.62
        elif dtype in {"float32", "fp32"} and est:
            est *= 1.55
        return round(max(0.0, est), 3)

    def _placement_request_snapshot(self, request: Any) -> dict[str, Any]:
        return {
            "device": getattr(request, "device", "auto"),
            "device_ids": list(getattr(request, "device_ids", []) or []),
            "sharding_strategy": getattr(request, "sharding_strategy", "none"),
            "device_map": getattr(request, "device_map", None),
            "max_memory": dict(getattr(request, "max_memory", {}) or {}),
            "torch_dtype": getattr(request, "torch_dtype", "auto"),
            "quantization": getattr(request, "quantization", "none"),
            "runtime_engine": getattr(request, "runtime_engine", "transformers"),
            "tensor_parallel_size": getattr(request, "tensor_parallel_size", 1),
        }

    def _tracked_gpu_gb(self, *, include_pending: bool = True, exclude_model: str | None = None) -> dict[int, dict[str, float]]:
        by_gpu: dict[int, dict[str, float]] = {}
        with self._placement_lock:
            groups = [("loaded", self._placements)]
            if include_pending:
                groups.append(("pending", self._pending_placements))
            for group_name, placements in groups:
                for model_name, placement in placements.items():
                    if exclude_model and model_name == exclude_model:
                        continue
                    for key, value in (placement.get("per_device_gb") or {}).items():
                        try:
                            idx = int(key)
                            amount = float(value or 0.0)
                        except Exception:
                            continue
                        row = by_gpu.setdefault(idx, {"loaded_gb": 0.0, "pending_gb": 0.0, "reserved_gb": 0.0})
                        bucket = "pending_gb" if group_name == "pending" else "loaded_gb"
                        row[bucket] += amount
                        row["reserved_gb"] += amount
        for row in by_gpu.values():
            for key in list(row):
                row[key] = round(row[key], 3)
        return by_gpu

    def validate_placement(self, request: Any, *, reserve: bool = False, job_id: int | None = None) -> dict[str, Any]:
        model_name = str(getattr(request, "model_name", "") or "").strip()
        record = self.registry.get_record(model_name)
        gpu_map, device_payload = self._gpu_device_map()
        gpu_ids = self._selected_gpu_ids(request, record=record, gpu_map=gpu_map)
        placement_warning = ""
        strategy = str(getattr(request, "sharding_strategy", "none") or "none").lower()
        estimate = self._model_vram_estimate_gb(record, request)
        errors: list[str] = []
        warnings: list[str] = []
        per_device: dict[str, float] = {}
        reserve_per_gpu = 0.75
        if estimate <= 0.0:
            placement = {
                "model_name": model_name,
                "label": getattr(record, "label", model_name),
                "state": "planned",
                "device": getattr(request, "device", "auto"),
                "device_ids": [],
                "sharding_strategy": strategy,
                "estimated_vram_gb": 0.0,
                "per_device_gb": {},
                "request": self._placement_request_snapshot(request),
                "warnings": warnings,
                "errors": errors,
                "ok": True,
                "job_id": job_id,
                "updated_at": self._now(),
            }
            if reserve:
                with self._placement_lock:
                    self._pending_placements[model_name] = dict(placement, state="loading")
            return {"ok": True, "placement": placement, "devices": device_payload, "warnings": warnings, "errors": errors}
        if not gpu_map:
            errors.append("No CUDA GPUs were detected. Select CPU or install/repair CUDA-enabled PyTorch before loading this model on GPU.")
        unknown = [idx for idx in gpu_ids if idx not in gpu_map]
        if unknown:
            errors.append(f"Selected GPU id(s) are not detected: {', '.join(map(str, unknown))}.")
        if not gpu_ids and gpu_map:
            gpu_ids = [sorted(gpu_map)[0]]
        min_gpus = max(1, int(getattr(record, "min_gpus", 1) or 1))
        if len(gpu_ids) < min_gpus:
            errors.append(f"{getattr(record, 'label', model_name)} requires at least {min_gpus} GPU(s); selected {len(gpu_ids)}.")
        if len(gpu_ids) > 1 and strategy == "none":
            warnings.append("Multiple GPU ids were selected while sharding is 'none'; only the first selected GPU will be used. Choose auto/balanced/sequential/custom to shard across all selected GPUs.")
        tracked = self._tracked_gpu_gb(include_pending=True, exclude_model=model_name)
        def available_for(idx: int) -> float:
            dev = gpu_map.get(idx, {})
            total = float(dev.get("total_memory_gb") or 0.0)
            loaded = float(tracked.get(idx, {}).get("loaded_gb") or 0.0)
            pending = float(tracked.get(idx, {}).get("pending_gb") or 0.0)
            by_total = max(0.0, total - loaded - pending - reserve_per_gpu) if total else 0.0
            free = dev.get("free_memory_gb")
            if free is not None:
                try:
                    by_free = max(0.0, float(free) - pending - reserve_per_gpu)
                    return round(min(by_total, by_free) if total else by_free, 3)
                except Exception:
                    pass
            return round(by_total, 3)
        effective_ids = list(gpu_ids)
        if strategy == "none" and effective_ids:
            effective_ids = [effective_ids[0]]
        if effective_ids:
            if strategy == "none":
                per_device[str(effective_ids[0])] = round(estimate, 3)
            else:
                share = round(estimate / max(1, len(effective_ids)), 3)
                per_device = {str(idx): share for idx in effective_ids}
        capacity_rows = []
        selected_total_available = 0.0
        for idx in sorted(set(gpu_ids)):
            dev = gpu_map.get(idx, {"id": f"cuda:{idx}", "name": "unknown"})
            avail = available_for(idx)
            selected_total_available += avail
            required = float(per_device.get(str(idx)) or 0.0)
            max_mem_override = None
            raw_max = (getattr(request, "max_memory", {}) or {}).get(str(idx)) or (getattr(request, "max_memory", {}) or {}).get(idx)
            if raw_max:
                max_mem_override = self._parse_memory_gb(raw_max)
                if max_mem_override is not None:
                    avail = min(avail, max(0.0, float(max_mem_override) - float(tracked.get(idx, {}).get("loaded_gb") or 0.0) - float(tracked.get(idx, {}).get("pending_gb") or 0.0)))
            capacity_rows.append({
                "id": f"cuda:{idx}",
                "index": idx,
                "name": dev.get("name"),
                "total_memory_gb": dev.get("total_memory_gb"),
                "free_memory_gb": dev.get("free_memory_gb"),
                "tracked_loaded_gb": round(float(tracked.get(idx, {}).get("loaded_gb") or 0.0), 3),
                "tracked_pending_gb": round(float(tracked.get(idx, {}).get("pending_gb") or 0.0), 3),
                "available_for_new_model_gb": round(avail, 3),
                "required_by_this_model_gb": round(required, 3),
                "max_memory_override_gb": max_mem_override,
            })
            if required > 0 and avail + 1e-6 < required:
                errors.append(f"cuda:{idx} has about {avail:.2f} GB available but this placement needs about {required:.2f} GB.")
        if estimate > 0 and effective_ids:
            usable_total = sum(row["available_for_new_model_gb"] for row in capacity_rows if row["index"] in set(effective_ids))
            if strategy != "none" and usable_total + 1e-6 < estimate:
                errors.append(f"Selected GPUs have about {usable_total:.2f} GB available, but the model is estimated to need about {estimate:.2f} GB.")
            if strategy == "none" and len(gpu_ids) > 1 and not errors:
                first = effective_ids[0]
                first_avail = next((row["available_for_new_model_gb"] for row in capacity_rows if row["index"] == first), 0.0)
                if first_avail + 1e-6 < estimate:
                    errors.append(f"The model is estimated at {estimate:.2f} GB VRAM but sharding is off and cuda:{first} cannot fit it. Select multiple GPUs and sharding='auto' or 'balanced'.")
        required_gpu_count = 0
        if gpu_map and estimate > 0:
            sorted_avail = sorted((available_for(idx) for idx in gpu_map), reverse=True)
            acc = 0.0
            for count, avail in enumerate(sorted_avail, start=1):
                acc += max(0.0, avail)
                if acc >= estimate:
                    required_gpu_count = count
                    break
            if required_gpu_count == 0:
                required_gpu_count = len(sorted_avail) + 1
        placement = {
            "model_name": model_name,
            "label": getattr(record, "label", model_name),
            "state": "planned",
            "device": getattr(request, "device", "auto"),
            "device_ids": gpu_ids,
            "effective_device_ids": effective_ids,
            "sharding_strategy": strategy,
            "estimated_vram_gb": round(estimate, 3),
            "per_device_gb": per_device,
            "required_gpu_count_estimate": required_gpu_count,
            "request": self._placement_request_snapshot(request),
            "capacity": capacity_rows,
            "warnings": warnings,
            "errors": errors,
            "ok": not errors,
            "job_id": job_id,
            "updated_at": self._now(),
        }
        if reserve and not errors:
            with self._placement_lock:
                self._pending_placements[model_name] = dict(placement, state="loading")
        return {"ok": not errors, "placement": placement, "devices": device_payload, "warnings": warnings, "errors": errors}

    def _commit_model_placement(self, model_name: str, placement: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, Any]:
        committed = dict(placement or {})
        committed.update({"state": "loaded", "loaded": True, "result_device": (result or {}).get("device"), "updated_at": self._now()})
        with self._placement_lock:
            self._pending_placements.pop(model_name, None)
            self._placements[model_name] = committed
        return committed

    def _release_model_placement(self, model_name: str | None = None) -> None:
        with self._placement_lock:
            if model_name:
                self._pending_placements.pop(model_name, None)
                self._placements.pop(model_name, None)
            else:
                self._pending_placements.clear()
                self._placements.clear()

    def model_placement(self, model_name: str | None) -> dict[str, Any] | None:
        if not model_name:
            return None
        name = str(model_name)
        with self._resource_lock:
            pending = deepcopy(self._loading_reservations.get(name)) if name in self._loading_reservations else None
        if pending:
            pending.setdefault("state", "loading")
            return pending
        try:
            loaded = self.registry.loaded_placement(name) if hasattr(self.registry, "loaded_placement") else None
            if loaded:
                loaded.setdefault("state", "loaded")
                return loaded
        except Exception:
            pass
        with self._placement_lock:
            fallback = dict(self._placements.get(name) or self._pending_placements.get(name) or {}) or None
        return fallback

    def placement_summary(self) -> dict[str, Any]:
        summary = self.model_resource_status()
        # Backward-compatible aliases for frontend code that was reading the
        # v5.37/v5.40 lifecycle placement payload directly.
        summary.setdefault("pending_models", summary.get("loading_reservations", []))
        summary.setdefault("device_detection", summary.get("raw_devices", {}))
        return summary

    def _empty_torch_cache(self) -> None:
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                try:
                    torch.cuda.ipc_collect()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            gc.collect()
        except Exception:
            pass

    def _cuda_memory_snapshot(self) -> dict[str, Any]:
        devices: list[dict[str, Any]] = []
        try:
            import torch
            if torch.cuda.is_available():
                for idx in range(torch.cuda.device_count()):
                    try:
                        free_b, total_b = torch.cuda.mem_get_info(idx)
                        devices.append({
                            "id": f"cuda:{idx}",
                            "index": idx,
                            "free_gb": round(free_b / (1024 ** 3), 3),
                            "total_gb": round(total_b / (1024 ** 3), 3),
                            "used_gb": round(max(0, total_b - free_b) / (1024 ** 3), 3),
                            "torch_allocated_gb": round(torch.cuda.memory_allocated(idx) / (1024 ** 3), 3),
                            "torch_reserved_gb": round(torch.cuda.memory_reserved(idx) / (1024 ** 3), 3),
                            "torch_max_allocated_gb": round(torch.cuda.max_memory_allocated(idx) / (1024 ** 3), 3),
                        })
                    except Exception as exc:
                        devices.append({"id": f"cuda:{idx}", "error": str(exc)})
                return {"ok": True, "cuda_available": True, "devices": devices}
        except Exception as exc:
            return {"ok": False, "cuda_available": False, "error": str(exc), "devices": devices}
        return {"ok": True, "cuda_available": False, "devices": devices}

    def _settings_bool(self, name: str, default: bool) -> bool:
        return bool(getattr(self.settings, name, default)) if self.settings is not None else default

    def _settings_float(self, name: str, default: float) -> float:
        try:
            return float(getattr(self.settings, name, default) if self.settings is not None else default)
        except Exception:
            return default

    def _settings_str(self, name: str, default: str) -> str:
        value = getattr(self.settings, name, default) if self.settings is not None else default
        return str(value or default)

    def _maybe_disable_generation_cache_for_pressure(self, model_name: str, prompt: str, context: dict[str, Any], runtime: dict[str, Any], options: dict[str, Any] | None = None) -> None:
        """Lower temporary KV-cache VRAM growth for long/high-pressure prompts.

        `use_cache=False` is slower, but for local Transformers generation it can
        prevent a long chat context from exhausting VRAM even when model weights
        themselves fit. This is opt-in by setting/default and only applied when
        context pressure is high or the caller explicitly requests it.
        """
        opts = dict(options or {})
        if opts.get("use_cache") is not None:
            runtime["use_cache"] = bool(opts.get("use_cache"))
            return
        if not self._settings_bool("model_vram_disable_generation_cache_on_pressure", True):
            return
        try:
            threshold = self._settings_float("model_vram_context_pressure_threshold", 0.70)
            budget = self._context_budget_payload(model_name=model_name, prompt=prompt, context=context, options=opts)
            if float(budget.get("percent_used") or 0.0) >= threshold:
                runtime["use_cache"] = False
                context.setdefault("runtime_memory_policy", {})["use_cache"] = False
                context["runtime_memory_policy"]["reason"] = f"context pressure {budget.get('percent_used')} >= {threshold}"
        except Exception:
            pass

    def _system_ram_guard(self, *, label: str = "runtime", model_name: str | None = None) -> dict[str, Any]:
        snap = self._system_memory_snapshot()
        percent = snap.get("percent")
        try:
            percent_f = float(percent) if percent is not None else 0.0
        except Exception:
            percent_f = 0.0
        warn = self._settings_float("model_system_ram_cleanup_warning_percent", 88.0)
        critical = self._settings_float("model_system_ram_critical_percent", 94.0)
        actions: list[str] = []
        if percent_f >= warn:
            try:
                gc.collect()
                actions.append("gc.collect")
            except Exception:
                pass
            try:
                if hasattr(self.registry, "cleanup_cuda_memory"):
                    self.registry.cleanup_cuda_memory(reset_peak_stats=True)
                    actions.append("registry.cleanup_cuda_memory")
            except Exception:
                pass
        return {
            "label": label,
            "model_name": model_name,
            "system_ram": snap,
            "warning_threshold_percent": warn,
            "critical_threshold_percent": critical,
            "warning": percent_f >= warn,
            "critical": percent_f >= critical,
            "actions": actions,
            "note": "System-RAM guard prevents unbounded assistant/chat payload growth and skips CPU offload when RAM is pressured.",
        }

    def _cleanup_after_model_call(self, model_name: str, stage: str = "inference", *, device: str = "auto", before: dict[str, Any] | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        opts = dict(options or {})
        cleanup_enabled = opts.get("cleanup_vram_after_inference")
        if cleanup_enabled is None:
            cleanup_enabled = self._settings_bool("model_vram_cleanup_after_inference", True)
        ram_guard_before_offload = self._system_ram_guard(label=f"before_{stage}_cleanup", model_name=model_name)
        if not cleanup_enabled:
            return {"cleanup_enabled": False, "before": before, "after": self._cuda_memory_snapshot(), "system_ram_guard": ram_guard_before_offload}
        reset_peak = self._settings_bool("model_vram_reset_peak_stats_after_inference", True)
        try:
            cleanup = self.registry.cleanup_cuda_memory(reset_peak_stats=reset_peak) if hasattr(self.registry, "cleanup_cuda_memory") else {}
        except Exception as exc:
            cleanup = {"ok": False, "error": str(exc)}
        after = self._cuda_memory_snapshot()
        policy = str(opts.get("auto_cpu_offload_policy") or self._settings_str("model_vram_auto_cpu_offload_policy", "on_pressure")).lower()
        auto_offload = bool(opts.get("auto_cpu_offload", self._settings_bool("model_vram_auto_cpu_offload_enabled", False)))
        offload_result: dict[str, Any] | None = None
        ram_snap = ram_guard_before_offload.get("system_ram") or {}
        try:
            ram_percent = float(ram_snap.get("percent") or 0.0)
        except Exception:
            ram_percent = 0.0
        skip_ram_threshold = self._settings_float("model_vram_skip_cpu_offload_when_system_ram_percent", 82.0)
        if auto_offload and ram_percent >= skip_ram_threshold:
            offload_result = {
                "skipped": True,
                "reason": f"system RAM pressure {ram_percent:.1f}% >= {skip_ram_threshold:.1f}%",
                "note": "CPU offload was skipped because moving model weights/KV state into system RAM could exhaust RAM.",
            }
            auto_offload = False
        if auto_offload and policy != "disabled" and self.registry.is_loaded(model_name):
            should = policy in {"after_chat", "after_every_inference"}
            reason = policy
            if not should and policy == "on_pressure":
                threshold = self._settings_float("model_vram_auto_cpu_offload_threshold", 0.82)
                # Offload if any device is above the configured usage ratio.
                for row in after.get("devices") or []:
                    total = float(row.get("total_gb") or 0.0)
                    used = float(row.get("used_gb") or 0.0)
                    if total > 0 and used / total >= threshold:
                        should = True
                        reason = f"vram_pressure {used:.2f}/{total:.2f}GB >= {threshold:.0%}"
                        break
            if should and hasattr(self.registry, "offload_to_cpu"):
                try:
                    offload_result = self.registry.offload_to_cpu(model_name, reason=reason)
                    self.lifecycle.update(model_name, "load", state="completed", progress=1.0, message="Model offloaded to CPU RAM to free VRAM", result=offload_result)
                    after = self._cuda_memory_snapshot()
                except Exception as exc:
                    offload_result = {"ok": False, "error": str(exc)}
        result = {"cleanup_enabled": True, "model_name": model_name, "stage": stage, "before": before, "cleanup": cleanup, "after": after, "cpu_offload": offload_result, "system_ram_guard": ram_guard_before_offload}
        return result

    def _registry_chat_with_vram_guard(self, model_name: str, prompt: str, *, context: dict[str, Any], device: str = "auto", options: dict[str, Any] | None = None, **runtime: Any) -> dict[str, Any]:
        # VLM/LLM tag selection still reaches the concrete model adapter; legacy audit marker: self.registry.chat(request.model_name, prompt
        self._maybe_disable_generation_cache_for_pressure(model_name, prompt, context, runtime, options)
        before = self._cuda_memory_snapshot()
        try:
            return self.registry.chat(model_name, prompt, context=context, device=device, **runtime)
        finally:
            context.setdefault("runtime_memory_cleanup", []).append(self._cleanup_after_model_call(model_name, "chat", device=device, before=before, options=options))

    def _registry_predict_with_vram_guard(self, model_name: str, image_path: Path, *, device: str = "auto", options: dict[str, Any] | None = None, **runtime: Any):
        before = self._cuda_memory_snapshot()
        try:
            return self.registry.predict(model_name, image_path, device=device, **runtime)
        finally:
            self._cleanup_after_model_call(model_name, "predict", device=device, before=before, options=options)

    def cleanup_runtime_memory(self, model_name: str | None = None, *, offload_to_cpu: bool = False) -> dict[str, Any]:
        before = self._cuda_memory_snapshot()
        offload = None
        if offload_to_cpu and hasattr(self.registry, "offload_to_cpu"):
            offload = self.registry.offload_to_cpu(model_name, reason="manual cleanup button")
        cleanup = self.registry.cleanup_cuda_memory(reset_peak_stats=True) if hasattr(self.registry, "cleanup_cuda_memory") else {}
        after = self._cuda_memory_snapshot()
        return {"ok": True, "model_name": model_name, "offload_to_cpu": offload_to_cpu, "offload": offload, "cleanup": cleanup, "before": before, "after": after}

    def _now(self) -> str:
        from ..database import now_iso
        return now_iso()

    def _cuda_inventory(self) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
        """Return detected CUDA devices keyed by numeric id.

        nvidia-smi may see GPUs before torch is correctly installed.  The planner
        still shows those GPUs so the user has feedback, but load-time execution
        remains governed by the adapter/torch runtime.
        """
        payload = detect_devices()
        devices: dict[int, dict[str, Any]] = {}
        for row in payload.get("devices") or []:
            raw_id = str(row.get("id") or "")
            if not raw_id.startswith("cuda:"):
                continue
            try:
                idx = int(raw_id.split(":", 1)[1])
            except Exception:
                idx = row.get("index")
                try:
                    idx = int(idx)
                except Exception:
                    continue
            devices[idx] = dict(row)
        return devices, payload

    def _parse_device_ids_value(self, value: Any) -> list[int]:
        if value in (None, "", [], {}):
            return []
        raw = value
        if isinstance(raw, str):
            parts = re.split(r"[,;\s]+", raw.strip())
        else:
            parts = list(raw)
        ids: list[int] = []
        seen: set[int] = set()
        for part in parts:
            text = str(part).strip().lower().replace("cuda:", "")
            if not text:
                continue
            try:
                idx = int(text)
            except ValueError:
                continue
            if idx >= 0 and idx not in seen:
                ids.append(idx)
                seen.add(idx)
        return ids

    def _request_device_ids(self, request: Any, available: dict[int, dict[str, Any]] | None = None) -> list[int]:
        ids = self._parse_device_ids_value(getattr(request, "device_ids", None))
        device = str(getattr(request, "device", "auto") or "auto").strip().lower()
        explicit_ids = self._parse_device_ids_value(device) if device.startswith("cuda:") else []
        explicit_id = explicit_ids[0] if explicit_ids else None
        if ids and explicit_id is not None and explicit_id not in ids:
            raise RuntimeError(
                f"GPU selection conflict: device={device!r} but device_ids={ids}. "
                "Use matching values so the selected model cannot be placed on a different GPU."
            )
        if not ids and explicit_id is not None:
            ids = [explicit_id]
        if not ids and device not in {"cpu", "mps"}:
            ids = self._parse_device_ids_value(getattr(self.settings, "default_model_device_ids", []) if self.settings else [])
        if not ids and device not in {"cpu", "mps"} and available:
            ids = [sorted(available.keys())[0]]
        return ids

    def _estimate_model_vram_gb(self, record: Any, request: Any) -> float:
        if not record or getattr(record, "cloud", False) or getattr(record, "provider", "") in {"builtin", "openai", "openrouter", "anthropic", "cloud"}:
            return 0.0
        base = getattr(record, "vram_gb", None)
        if base is None:
            base = getattr(record, "size_gb", None)
        try:
            estimate = float(base or 0.0)
        except Exception:
            estimate = 0.0
        quant = str(getattr(request, "quantization", "none") or "none").lower()
        dtype = str(getattr(request, "torch_dtype", "auto") or "auto").lower()
        # Model rows generally already contain practical VRAM estimates.  Only
        # down-adjust obvious quantized cases and up-adjust explicit float32.
        if estimate > 0:
            if quant == "4bit":
                estimate = max(0.5, estimate * 0.45)
            elif quant == "8bit":
                estimate = max(0.75, estimate * 0.65)
            elif dtype in {"float32", "fp32"}:
                estimate *= 1.65
        return round(max(0.0, estimate), 3)

    def _parse_memory_gb(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        text = str(value).strip().lower().replace(" ", "")
        try:
            if text.endswith("gib"):
                return float(text[:-3])
            if text.endswith("gb"):
                return float(text[:-2])
            if text.endswith("mib"):
                return float(text[:-3]) / 1024.0
            if text.endswith("mb"):
                return float(text[:-2]) / 1024.0
            return float(text)
        except Exception:
            return None

    def _loaded_reservations_by_gpu(self, exclude_model: str | None = None) -> dict[int, float]:
        reservations: dict[int, float] = {}
        try:
            loaded_rows = self.registry.loaded_details() if hasattr(self.registry, "loaded_details") else []
        except Exception:
            loaded_rows = []
        loaded = {row.get("model_name"): row for row in loaded_rows if row.get("model_name")}
        for name, meta in (loaded or {}).items():
            if exclude_model and name == exclude_model:
                continue
            if isinstance(meta, dict) and meta.get("offloaded_to_cpu"):
                # CPU-offloaded adapters keep processors/state alive but no longer
                # reserve VRAM for placement planning. They will reactivate on
                # the requested GPU at next use and be revalidated then.
                continue
            placement = meta.get("placement") or {}
            by_gpu = (
                placement.get("reservation_by_gpu")
                or placement.get("per_gpu_reserved_gb")
                or placement.get("per_device_gb")
                or meta.get("reservation_by_gpu")
                or meta.get("per_gpu_reserved_gb")
                or meta.get("per_device_gb")
                or {}
            )
            for key, value in by_gpu.items():
                try:
                    idx = int(str(key).replace("cuda:", ""))
                    reservations[idx] = reservations.get(idx, 0.0) + float(value or 0.0)
                except Exception:
                    continue
        return {k: round(v, 3) for k, v in reservations.items()}

    def model_residency_status(self) -> dict[str, Any]:
        devices, raw = self._cuda_inventory()
        reservations = self._loaded_reservations_by_gpu()
        safety = self._vram_fraction()
        rows: list[dict[str, Any]] = []
        for idx in sorted(devices):
            dev = dict(devices[idx])
            total = self._parse_memory_gb(dev.get("total_memory_gb")) or 0.0
            reserved = float(reservations.get(idx, 0.0))
            usable = round(total * safety, 3) if total else None
            free_after_reserved = round(max(0.0, (usable or total or 0.0) - reserved), 3) if total else None
            dev.update(
                {
                    "index": idx,
                    "reserved_by_loaded_models_gb": round(reserved, 3),
                    "usable_memory_gb": usable,
                    "free_after_reservations_gb": free_after_reserved,
                    "safety_fraction": safety,
                }
            )
            rows.append(dev)
        loaded = self.registry.loaded_details() if hasattr(self.registry, "loaded_details") else []
        return {
            "devices": rows,
            "loaded_models": loaded,
            "reservations_by_gpu_gb": reservations,
            "safety_fraction": safety,
            "raw_detect": raw,
        }

    def placement_plan(self, request: Any, *, strict: bool = False, exclude_loaded_model: bool = True) -> dict[str, Any]:
        model_name = str(getattr(request, "model_name", "") or "").strip()
        record = self.registry.get_record(model_name) if model_name else None
        devices, raw = self._cuda_inventory()
        requested_ids = self._request_device_ids(request, record, devices)
        device = str(getattr(request, "device", "auto") or "auto").strip()
        device_lower = device.lower()
        placement_warning = ""
        strategy = str(getattr(request, "sharding_strategy", "none") or "none").lower()
        if strategy not in {"none", "auto", "balanced", "balanced_low_0", "sequential", "custom"}:
            strategy = "none"
        warnings: list[str] = []
        errors: list[str] = []
        uses_gpu = device_lower not in {"cpu", "mps"} and self._estimate_model_vram_gb(record, request) > 0
        selected_ids = list(requested_ids) if uses_gpu else []
        if uses_gpu and not selected_ids:
            errors.append("No CUDA GPU was selected or detected. Choose CPU or select at least one CUDA device.")
        missing = [idx for idx in selected_ids if idx not in devices]
        if missing:
            errors.append("Selected CUDA device(s) were not detected: " + ", ".join(f"cuda:{idx}" for idx in missing))
        if uses_gpu and strategy == "none" and len(selected_ids) > 1:
            warnings.append("Sharding is disabled, so the model will be placed on the first selected GPU only. Choose auto/balanced/sequential to split a large model across multiple GPUs.")
            selected_ids = selected_ids[:1]
        min_gpus = int(getattr(record, "min_gpus", 1) or 1) if record else 1
        max_gpus = getattr(record, "max_gpus", None) if record else None
        if uses_gpu and strategy != "none":
            if len(selected_ids) < min_gpus:
                errors.append(f"{getattr(record, 'label', model_name)} expects at least {min_gpus} GPU(s) for this sharding mode.")
            if max_gpus is not None:
                try:
                    max_gpus_i = int(max_gpus)
                    if len(selected_ids) > max_gpus_i:
                        errors.append(f"This model metadata caps sharding at {max_gpus_i} GPU(s).")
                except Exception:
                    pass
            if record and not getattr(record, "supports_sharding", False):
                warnings.append("This catalog row is not explicitly marked as sharding-tested. The adapter will still receive the selected device map, but compatibility depends on the runtime/model.")
        estimate = self._estimate_model_vram_gb(record, request)
        reservations = self._loaded_reservations_by_gpu(exclude_model=model_name if exclude_loaded_model else None)
        safety = self._vram_fraction()
        max_memory = getattr(request, "max_memory", {}) or {}
        reservation_by_gpu: dict[int, float] = {}
        effective_device = device
        if uses_gpu and selected_ids:
            if strategy == "none":
                reservation_by_gpu[selected_ids[0]] = estimate
                effective_device = f"cuda:{selected_ids[0]}" if device_lower in {"auto", "auto_cuda", "cuda"} else device
            else:
                per_gpu = round(estimate / max(1, len(selected_ids)), 3)
                reservation_by_gpu = {idx: per_gpu for idx in selected_ids}
                effective_device = device if device_lower not in {"cuda"} else "auto"
        elif device_lower == "cpu" or not uses_gpu:
            effective_device = "cpu" if device_lower == "cpu" else device
        device_rows: list[dict[str, Any]] = []
        for idx in sorted(set(list(devices.keys()) + selected_ids)):
            dev = devices.get(idx, {"id": f"cuda:{idx}", "index": idx, "name": f"CUDA {idx}", "total_memory_gb": None})
            selected = idx in selected_ids
            if uses_gpu and selected and not bool(dev.get("torch_ready")):
                errors.append(
                    f"cuda:{idx} is visible to NVIDIA tools but PyTorch CUDA is not ready/cannot use that CUDA id in this app environment. "
                    "The launch/install scripts now clear accidental CUDA_VISIBLE_DEVICES masking by default; run install.bat/update.bat after deleting the env, then verify torch sees all GPUs."
                )
            total = self._parse_memory_gb(dev.get("total_memory_gb"))
            usable = self._parse_memory_gb(max_memory.get(str(idx)) if isinstance(max_memory, dict) else None)
            if usable is None and isinstance(max_memory, dict):
                usable = self._parse_memory_gb(max_memory.get(idx))
            if usable is None and total is not None:
                usable = total * safety
            free_detected = self._memory_value_gb(dev.get("free_memory_gb"))
            driver_limited_usable = min(usable, free_detected * safety) if usable is not None and free_detected is not None else usable
            driver_free_warning = bool(usable is not None and driver_limited_usable is not None and driver_limited_usable + 0.25 < usable)
            reserved = float(reservations.get(idx, 0.0))
            planned = float(reservation_by_gpu.get(idx, 0.0))
            after = None
            fits = True
            if usable is not None:
                after = round(usable - reserved - planned, 3)
                fits = after >= -0.05
            if selected and not fits:
                errors.append(f"cuda:{idx} would exceed the usable VRAM budget: reserved {reserved:.2f} GB + planned {planned:.2f} GB > usable {usable:.2f} GB.")
            device_rows.append(
                {
                    "id": f"cuda:{idx}",
                    "index": idx,
                    "name": dev.get("name") or f"CUDA {idx}",
                    "selected": selected,
                    "total_memory_gb": round(total, 3) if total is not None else None,
                    "driver_used_memory_gb": dev.get("used_memory_gb"),
                    "driver_free_memory_gb": dev.get("free_memory_gb"),
                    "usable_memory_gb": round(usable, 3) if usable is not None else None,
                    "driver_limited_usable_memory_gb": round(driver_limited_usable, 3) if driver_limited_usable is not None else None,
                    "availability_basis": "app_reservation_budget",
                    "driver_free_memory_warning": driver_free_warning,
                    "reserved_by_loaded_models_gb": round(reserved, 3),
                    "planned_reservation_gb": round(planned, 3),
                    "free_after_plan_gb": after,
                    "will_fit": fits,
                    "torch_ready": bool(dev.get("torch_ready")),
                }
            )
        if uses_gpu and selected_ids and estimate > 0:
            selected_capacity = 0.0
            unknown_capacity = False
            for row in device_rows:
                if not row["selected"]:
                    continue
                if row.get("usable_memory_gb") is None:
                    unknown_capacity = True
                    continue
                selected_capacity += max(0.0, float(row["usable_memory_gb"]) - float(row.get("reserved_by_loaded_models_gb") or 0.0))
            if not unknown_capacity and estimate > selected_capacity + 0.05:
                profile_hint = ""
                if record is not None:
                    profiles = self._model_memory_profiles(record)
                    alts = [f"{k}: ~{v:.2f} GB" for k, v in profiles.items() if k in {"8bit", "sfp8", "4bit", "q4_0"}]
                    if alts:
                        profile_hint = " Alternatives: " + ", ".join(alts) + "."
                errors.append(f"Estimated model VRAM ({estimate:.2f} GB) exceeds selected free reservation budget ({selected_capacity:.2f} GB). Select more/larger GPUs, unload other models, set quantization to 8bit/4bit where supported, or use CPU/cloud.{profile_hint}")
        already_loaded = self.registry.is_loaded(model_name) if model_name else False
        loaded_meta = self.registry.loaded_placement(model_name) if already_loaded and hasattr(self.registry, "loaded_placement") else None
        plan = {
            "model_name": model_name,
            "label": getattr(record, "label", model_name) if record else model_name,
            "provider": getattr(record, "provider", None) if record else None,
            "cloud": bool(getattr(record, "cloud", False)) if record else False,
            "device": device,
            "effective_device": effective_device,
            "device_ids": selected_ids,
            "requested_device_ids": requested_ids,
            "sharding_strategy": strategy,
            "supports_sharding": bool(getattr(record, "supports_sharding", False)) if record else False,
            "min_gpus": min_gpus,
            "max_gpus": max_gpus,
            "estimated_vram_gb": estimate,
            "runtime_vram_profiles": self._model_memory_profiles(record) if record is not None else {},
            "memory_note": getattr(record, "memory_note", None) if record is not None else None,
            "reservation_by_gpu": {str(k): round(v, 3) for k, v in reservation_by_gpu.items()},
            "devices": device_rows,
            "warnings": warnings,
            "errors": errors,
            "can_load": not errors,
            "already_loaded": already_loaded,
            "loaded": loaded_meta,
            "raw_device_detect_warnings": raw.get("warnings") or [],
        }
        if strict and errors:
            raise RuntimeError("Model GPU placement would exceed the available/selected VRAM budget. " + " ".join(errors))
        return plan

    def invalidate_model_catalog_cache(self) -> None:
        self._catalog_cache_rows = None
        self._catalog_cache_ts = 0.0

    def _static_model_catalog_rows(self, *, force: bool = False) -> list[dict[str, Any]]:
        now = time.monotonic()
        if (not force) and self._catalog_cache_rows is not None and (now - self._catalog_cache_ts) < self._catalog_cache_ttl:
            return deepcopy(self._catalog_cache_rows)
        self.reconcile_local_assets()
        rows = self.registry.list()
        self._catalog_cache_rows = deepcopy(rows)
        self._catalog_cache_ts = now
        return deepcopy(rows)

    def reconcile_local_assets(self) -> dict[str, Any]:
        """Rescan local model folders and reconcile lifecycle download circles."""
        reconciled: list[str] = []
        rows = self.registry.list()
        for row in rows:
            name = row.get("name")
            if not name:
                continue
            self.lifecycle.ensure_model(name)
            if not row.get("downloaded"):
                continue
            stage = self.lifecycle.model_status(name).get("stages", {}).get("download", {})
            state = str(stage.get("state") or "idle").lower()
            if stage.get("active") or state in {"queued", "running"}:
                continue
            if state != "completed" or float(stage.get("progress") or 0.0) < 1.0:
                self.lifecycle.complete(
                    name,
                    "download",
                    message="Local model files found; download marked complete",
                    result={"downloaded": True, "local_path": row.get("local_path"), "reconciled": True},
                )
                reconciled.append(name)
        return {"reconciled_models": reconciled, "count": len(reconciled)}

    def reconcile_model_local_asset(self, model_name: str, *, job_id: int | None = None) -> dict[str, Any]:
        """Rescan one model row and patch its download lifecycle immediately.

        This is intentionally narrower than ``/api/models?force=true``.  A full
        catalog scan can be slow when the user has migrated many large model
        folders.  The frontend calls this endpoint right after a download job
        reaches a terminal state so badges such as NOT DOWNLOADED and
        INCOMPLETE/CORRUPT disappear without waiting for the next full refresh.
        """
        name = self.lifecycle.normalize_model_name(model_name)
        record = self.registry.get_record(name)
        row = record.to_dict(self.registry.model_root, self.registry.external_model_roots)
        self.lifecycle.ensure_model(name)
        stage = self.lifecycle.model_status(name).get("stages", {}).get("download", {})
        state = str(stage.get("state") or "idle").lower()
        if row.get("downloaded"):
            self.lifecycle.complete(
                name,
                "download",
                message="Local model payload verified; download status refreshed",
                job_id=job_id or stage.get("job_id"),
                result={"downloaded": True, "local_path": row.get("local_path"), "reconciled_single_model": True},
            )
            self.invalidate_model_catalog_cache()
        elif state == "completed":
            issues = (row.get("download_integrity") or {}).get("issues") or row.get("local_integrity_issues") or []
            if issues:
                self.lifecycle.update(
                    name,
                    "download",
                    state="failed",
                    progress=1.0,
                    job_id=job_id or stage.get("job_id"),
                    message="Download finished but local integrity validation still reports: " + "; ".join(str(x) for x in issues),
                    error="; ".join(str(x) for x in issues),
                )
        statuses = self.lifecycle.all_statuses().get("models", {})
        row = self._augment_model_row_status(row, statuses)
        return {"ok": bool(row.get("downloaded")), "model_name": name, "model": row, "lifecycle": self.lifecycle.model_status(name)}

    def _complete_active_download_if_local_payload_ready(self, model_name: str | None = None) -> list[str]:
        """Unstick active download circles when the local model payload is already usable.

        Hugging Face downloads can occasionally leave the browser seeing a
        running lifecycle row after the files are already present, especially
        for small ONNX/tagger repos that complete between polling cycles.  The
        model loader should not remain blocked when the registry's own integrity
        checks say the local payload is complete.
        """
        names: list[str]
        if model_name:
            names = [self.lifecycle.normalize_model_name(model_name)]
        else:
            names = list((self.lifecycle.all_statuses().get("models") or {}).keys())
        completed: list[str] = []
        for name in names:
            try:
                record = self.registry.get_record(name)
            except Exception:
                continue
            if getattr(record, "cloud", False) or not getattr(record, "download_supported", False):
                continue
            stage = self.lifecycle.model_status(name).get("stages", {}).get("download", {})
            state = str(stage.get("state") or "idle").lower()
            if not (stage.get("active") or state in {"queued", "running"}):
                continue
            try:
                local = record.complete_local_dir(self.registry.model_root, self.registry.external_model_roots)
            except Exception:
                local = None
            if local and local.exists():
                self.lifecycle.complete(
                    name,
                    "download",
                    message="Local model payload detected; download marked complete",
                    job_id=stage.get("job_id"),
                    result={"downloaded": True, "local_path": str(local), "reconciled_active_download": True},
                )
                completed.append(name)
        if completed:
            self.invalidate_model_catalog_cache()
        return completed

    def _assistant_model_candidates(self) -> list[dict[str, Any]]:
        candidates = []
        for row in self.registry.list():
            caps = set(row.get("capabilities") or [])
            kind = str(row.get("kind") or "")
            if caps.intersection({"chat", "vlm", "assistant", "image_text_to_text", "tag_suggestions", "caption_suggestions"}) or kind in {"assistant", "llm", "vlm"}:
                candidates.append(row)
        return candidates

    def default_assistant_model_name(self) -> str:
        return str(getattr(self.settings, "assistant_model_name", "dataset-assistant") or "dataset-assistant")

    def default_orchestrator_model_name(self) -> str:
        return str(getattr(self.settings, "orchestrator_model_name", None) or self.default_assistant_model_name() or "dataset-assistant")

    def resolve_assistant_model_name(self, requested: str | None = None, *, purpose: str = "assistant") -> str:
        requested_text = str(requested or "").strip()
        default_name = self.default_orchestrator_model_name() if purpose == "orchestrator" else self.default_assistant_model_name()
        if requested_text in {"", "__assistant__", "assistant-default", "default-assistant"}:
            return default_name or "dataset-assistant"
        if purpose == "orchestrator" and requested_text == "dataset-assistant":
            return default_name or "dataset-assistant"
        return requested_text

    def validate_assistant_model_name(self, model_name: str | None) -> str:
        name = str(model_name or "dataset-assistant").strip() or "dataset-assistant"
        record = self.registry.get_record(name)
        caps = set(getattr(record, "capabilities", []) or [])
        kind = str(getattr(record, "kind", "") or "")
        if not (caps.intersection({"chat", "vlm", "assistant", "image_text_to_text", "tag_suggestions", "caption_suggestions"}) or kind in {"assistant", "llm", "vlm"}):
            raise ValueError(f"{getattr(record, 'label', name)} is not an assistant/chat/VLM-capable model.")
        return name

    def assistant_config(self) -> dict[str, Any]:
        assistant_name = self.default_assistant_model_name()
        orchestrator_name = self.default_orchestrator_model_name()
        return {
            "assistant_model_name": assistant_name,
            "orchestrator_model_name": orchestrator_name,
            "assistant_model_auto_load": bool(getattr(self.settings, "assistant_model_auto_load", False)) if self.settings else False,
            "assistant_allow_orchestration": bool(getattr(self.settings, "assistant_allow_orchestration", True)) if self.settings else True,
            "assistant_loaded": self.registry.is_loaded(assistant_name),
            "orchestrator_loaded": self.registry.is_loaded(orchestrator_name),
            "assistant_status": self.lifecycle.model_status(assistant_name),
            "orchestrator_status": self.lifecycle.model_status(orchestrator_name),
            "available_models": self._assistant_model_candidates(),
        }

    def _orchestrator_task_list(self, goal: str, requested: list[str] | None = None) -> list[str]:
        tasks: list[str] = []
        for item in requested or []:
            text = str(item or "").strip().lower()
            if text and text not in tasks:
                tasks.append(text)
        goal_text = str(goal or "").lower()
        keyword_map = [
            ("tag_select", ["select tag", "validate tag", "prune tag", "tag selection", "existing tags"]),
            ("tag", ["tag", "label", "classification label"]),
            ("caption", ["caption", "describe", "description"]),
            ("rating", ["rating", "safety", "nsfw"]),
            ("detection", ["detect", "bbox", "box", "object"]),
            ("segmentation", ["segment", "mask", "sam"]),
        ]
        for task, keys in keyword_map:
            if any(key in goal_text for key in keys) and task not in tasks:
                tasks.append(task)
        if not tasks:
            tasks.append("tag_select")
        return tasks[:6]

    def _model_matches_orchestrator_task(self, row: dict[str, Any], task: str) -> bool:
        caps = set(row.get("capabilities") or [])
        kind = str(row.get("kind") or "")
        if task in {"tag_select", "tag"}:
            return bool(caps.intersection({"vlm", "chat", "tag", "auto_tag", "classify", "rating", "caption"}) or kind in {"vlm", "llm", "assistant", "tagger", "classifier", "rating", "captioner"})
        if task == "caption":
            return bool(caps.intersection({"caption", "vlm", "image_text_to_text"}) or kind in {"captioner", "vlm"})
        if task == "rating":
            return bool(caps.intersection({"rating", "classify"}) or kind in {"rating", "classifier", "tagger"})
        if task == "detection":
            return bool(caps.intersection({"detect", "bbox", "open_vocabulary"}) or kind in {"detection", "vlm"})
        if task == "segmentation":
            return bool(caps.intersection({"segment", "mask", "video_mask"}) or kind in {"segmentation", "vlm"})
        return True

    def _rank_orchestrator_candidate(self, row: dict[str, Any], task: str) -> tuple[int, int, str]:
        caps = set(row.get("capabilities") or [])
        kind = str(row.get("kind") or "")
        cloud_penalty = 100 if row.get("cloud") or row.get("provider") in {"openai", "openrouter", "anthropic"} else 0
        loaded_bonus = -20 if row.get("loaded") else 0
        downloaded_bonus = -10 if row.get("downloaded") else 0
        if task == "tag_select":
            group = 0 if kind == "vlm" or "vlm" in caps else 1 if kind in {"llm", "assistant"} or "chat" in caps else 2
        elif task == "caption":
            group = 0 if kind == "vlm" else 1 if kind == "captioner" or "caption" in caps else 2
        elif task == "detection":
            group = 0 if kind == "detection" else 1 if "detect" in caps else 2
        elif task == "segmentation":
            group = 0 if kind == "segmentation" else 1 if "segment" in caps else 2
        else:
            group = 0 if self._model_matches_orchestrator_task(row, task) else 9
        return (cloud_penalty + group * 10 + loaded_bonus + downloaded_bonus, int(row.get("vram_gb") or 0), str(row.get("label") or row.get("name") or "").lower())

    def _recommended_request_for_model(self, model_name: str) -> ModelLoadRequest:
        row = next((m for m in self.list_models() if m.get("name") == model_name), {})
        estimate = float(row.get("vram_gb") or 0.0)
        resources = self.model_resource_status()
        cuda_rows = []
        for dev in resources.get("devices") or []:
            raw_id = str(dev.get("id") or "")
            if not raw_id.startswith("cuda:"):
                continue
            try:
                idx = int(raw_id.split(":", 1)[1])
            except Exception:
                continue
            available = float(dev.get("estimated_available_gb") or dev.get("usable_memory_gb") or dev.get("total_memory_gb") or 0.0)
            cuda_rows.append((idx, available))
        cuda_rows.sort(key=lambda x: x[1], reverse=True)
        selected: list[int] = []
        if estimate > 0 and cuda_rows:
            total = 0.0
            for idx, available in cuda_rows:
                selected.append(idx)
                total += max(0.0, available)
                if total >= estimate:
                    break
        elif cuda_rows:
            selected = [cuda_rows[0][0]]
        min_gpus = int(row.get("min_gpus") or 1) if row else 1
        if cuda_rows and len(selected) < min_gpus:
            selected = [idx for idx, _ in cuda_rows[:min_gpus]]
        strategy = "none"
        if len(selected) > 1 or (estimate and cuda_rows and selected and estimate > max(available for _, available in cuda_rows)):
            strategy = "balanced"
        dtype = "auto"
        precision = str(row.get("precision") or "").lower()
        if "bf16" in precision:
            dtype = "bfloat16"
        elif "fp16" in precision or "float16" in precision:
            dtype = "float16"
        backend = str(row.get("recommended_backend") or "transformers").split("/", 1)[0] if row else "transformers"
        if backend not in {"transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"}:
            backend = "transformers"
        return ModelLoadRequest(
            model_name=model_name,
            device="auto" if selected else "cpu",
            device_ids=selected,
            sharding_strategy=strategy,
            torch_dtype=dtype,
            quantization="none",
            runtime_engine=backend,
            tensor_parallel_size=max(1, len(selected)) if strategy != "none" else 1,
            options={"tag_profile": getattr(self.settings, "default_tag_profile", "e621") if self.settings else "e621"},
        )

    def orchestrator_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        goal = str(payload.get("goal") or payload.get("prompt") or "").strip()
        tasks = self._orchestrator_task_list(goal, payload.get("requested_tasks") or payload.get("tasks") or [])
        orchestrator_name = self.resolve_assistant_model_name(payload.get("orchestrator_model_name"), purpose="orchestrator")
        rows = self.list_models()
        by_name = {row.get("name"): row for row in rows}
        allow_cloud = bool(payload.get("allow_cloud", False))
        steps: list[dict[str, Any]] = []
        for task in tasks:
            candidates = [row for row in rows if self._model_matches_orchestrator_task(row, task)]
            if not allow_cloud:
                candidates = [row for row in candidates if not (row.get("cloud") or row.get("provider") in {"openai", "openrouter", "anthropic"})]
            candidates.sort(key=lambda row: self._rank_orchestrator_candidate(row, task))
            top = candidates[: int(payload.get("candidates_per_task") or 4)]
            if not top:
                steps.append({"task": task, "approved": False, "reason": "No matching local model rows were found.", "candidates": []})
                continue
            selected = top[0]
            req = self._recommended_request_for_model(str(selected.get("name")))
            try:
                placement = self.placement_plan(req, strict=False)
            except Exception as exc:
                placement = {"can_load": False, "errors": [str(exc)], "model_name": selected.get("name")}
            run_task = "tag" if task in {"tag", "tag_select"} else "segment" if task == "segmentation" else "classify" if task == "detection" else task
            if run_task not in {"tag", "caption", "classify", "rating", "embed", "segment", "caption_split"}:
                run_task = "tag"
            steps.append({
                "task": task,
                "run_task": run_task,
                "approved": False,
                "requires_user_approval": True,
                "model_name": selected.get("name"),
                "label": selected.get("label"),
                "kind": selected.get("kind"),
                "provider": selected.get("provider"),
                "reason": f"Recommended for {task} from available model categories; user must approve before any run is queued.",
                "placement_request": req.model_dump(),
                "placement": placement,
                "candidates": [{"name": row.get("name"), "label": row.get("label"), "kind": row.get("kind"), "provider": row.get("provider"), "downloaded": row.get("downloaded"), "loaded": row.get("loaded"), "vram_gb": row.get("vram_gb"), "cloud": row.get("cloud")} for row in top],
            })
        return {
            "orchestrator_model_name": orchestrator_name,
            "assistant_model_name": self.default_assistant_model_name(),
            "goal": goal,
            "media_ids": payload.get("media_ids") or [],
            "user_approval_required": True,
            "message": "This is a recommended plan only. Nothing runs until the user approves/queues specific steps.",
            "steps": steps,
            "resource_status": self.model_resource_status(),
            "runtime_planning_context": self.model_runtime_planning_context(limit=80),
            "selected_orchestrator": by_name.get(orchestrator_name, {"name": orchestrator_name}),
        }



    def model_runtime_planning_context(self, limit: int = 250) -> dict[str, Any]:
        """Compact live resource context for assistant/orchestrator placement decisions."""
        resources = self.model_resource_status()
        rows = self.list_models()
        compact_models: list[dict[str, Any]] = []
        for row in rows[: max(1, int(limit or 250))]:
            compact_models.append({
                "name": row.get("name"),
                "label": row.get("label"),
                "kind": row.get("kind"),
                "provider": row.get("provider"),
                "downloaded": row.get("downloaded"),
                "loaded": row.get("loaded"),
                "loaded_instance_count": row.get("loaded_instance_count"),
                "vram_gb": row.get("vram_gb"),
                "size_gb": row.get("size_gb"),
                "supports_sharding": row.get("supports_sharding"),
                "min_gpus": row.get("min_gpus"),
                "max_gpus": row.get("max_gpus"),
                "recommended_backend": row.get("recommended_backend"),
                "capabilities": row.get("capabilities") or [],
                "cloud": row.get("cloud"),
            })
        return {
            "resource_status": resources,
            "loaded_models": resources.get("loaded_models") or [],
            "available_models": compact_models,
            "placement_policy": {
                "strict_gpu_assignment": True,
                "no_silent_cpu_fallback_for_explicit_cuda": True,
                "user_can_select_device_ids": True,
                "assistant_can_select_device_ids": True,
                "assistant_can_request_sharding": True,
                "supported_sharding_strategies": ["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"],
                "supported_runtime_engines": ["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"],
                "guidance": "Use resource_status.devices actual_used/free plus app_reserved/planning_available to choose device_ids. Use balanced/auto sharding for models larger than one selected GPU budget or when the registry marks supports_sharding=true. Never queue a local load on CPU when the user explicitly requested cuda:N unless the user changes placement.",
            },
        }

    def add_custom_model(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        category = str(data.get("category") or "").strip()
        if not category:
            raise ValueError("Custom model category is required. Choose classifier, tagger, llm, vlm, detection, segmentation, pose2d, pose3d, etc.")
        record = self.registry.register_custom_model(data)
        row_payload = self.registry.custom_model_payload(record) if hasattr(self.registry, "custom_model_payload") else data
        existing = []
        if self.settings is not None:
            existing = list(getattr(self.settings, "custom_models", []) or [])
            existing = [r for r in existing if str(r.get("name") or "") != record.name]
            existing.insert(0, row_payload)
            self.settings.custom_models = existing
        self.lifecycle.ensure_model(record.name)
        self.invalidate_model_catalog_cache()
        if record.is_downloaded(self.registry.model_root):
            self.lifecycle.complete(record.name, "download", message="Custom model files found; marked downloaded", result={"downloaded": True, "custom": True})
        return record.to_dict(self.registry.model_root)

    def delete_custom_model(self, model_name: str) -> dict[str, Any]:
        record = self.registry.get_record(model_name)
        if not getattr(record, "user_custom", False):
            raise ValueError(f"{getattr(record, 'label', model_name)} is not a user-added custom model.")
        if self.registry.is_loaded(model_name):
            self.registry.unload(model_name)
        self.registry._records.pop(model_name, None)
        if self.settings is not None:
            self.settings.custom_models = [r for r in (getattr(self.settings, "custom_models", []) or []) if str(r.get("name") or "") != model_name]
        self.invalidate_model_catalog_cache()
        return {"deleted": model_name, "remaining": len(getattr(self.settings, "custom_models", []) or []) if self.settings else None}

    def _augment_model_row_status(self, row: dict[str, Any], statuses: dict[str, Any] | None = None) -> dict[str, Any]:
        name = row.get("name")
        if not name:
            return row
        lifecycle = (statuses or {}).get(name) or self.lifecycle.model_status(name).get("stages", {})
        loaded = bool(self.registry.is_loaded(name))
        loaded_count = 0
        loaded_instances: list[dict[str, Any]] = []
        offloaded_to_cpu = False
        try:
            loaded_count = int(self.registry.loaded_instance_count(name)) if hasattr(self.registry, "loaded_instance_count") else (1 if loaded else 0)
            loaded_instances = self.registry.loaded_instances(name) if hasattr(self.registry, "loaded_instances") else ([self.registry.loaded_placement(name) or {"model_name": name, "loaded": True}] if loaded else [])
        except Exception:
            loaded_count = 1 if loaded else 0
            loaded_instances = []
        offloaded_to_cpu = any(bool(item.get("offloaded_to_cpu")) for item in loaded_instances if isinstance(item, dict))
        download_stage = lifecycle.get("download", {}) if isinstance(lifecycle, dict) else {}
        load_stage = lifecycle.get("load", {}) if isinstance(lifecycle, dict) else {}
        inference_stage = lifecycle.get("inference", {}) if isinstance(lifecycle, dict) else {}
        downloaded = bool(row.get("downloaded"))
        integrity = row.get("download_integrity") or {}
        issues = list(integrity.get("issues") or []) if isinstance(integrity, dict) else []

        def active_state(stage_row: dict[str, Any]) -> str:
            state = str(stage_row.get("state") or "").lower() if isinstance(stage_row, dict) else ""
            if stage_row.get("active") or state in {"queued", "running", "unloading"}:
                return state or "running"
            return ""

        download_state = active_state(download_stage) or ("downloaded" if downloaded else ("incomplete" if issues else "not_downloaded"))
        load_state = active_state(load_stage) or ("cpu_offloaded" if offloaded_to_cpu else ("loaded" if loaded else "not_loaded"))
        inference_state = active_state(inference_stage) or "idle"
        badges: list[str] = []
        if downloaded:
            badges.append("downloaded")
        elif row.get("download_supported"):
            badges.append("not downloaded")
        if issues:
            badges.append("needs repair/update")
        access = str(row.get("hf_access") or "").lower()
        if row.get("requires_hf_token") or access in {"gated", "restricted"}:
            badges.append("hf token/terms required")
        elif access in {"hf_token_recommended", "token_recommended", "token-recommended"}:
            badges.append("hf token recommended")
        if loaded_count:
            badges.append((f"cpu offloaded x{loaded_count}" if offloaded_to_cpu else f"loaded x{loaded_count}"))
        if download_state in {"queued", "running"}:
            pct = int(round(float(download_stage.get("progress") or 0.0) * 100))
            badges.append(f"download {download_state} {pct}%")
        if load_state in {"queued", "running", "unloading"}:
            pct = int(round(float(load_stage.get("progress") or 0.0) * 100))
            badges.append(f"load {load_state} {pct}%")
        if inference_state in {"queued", "running"}:
            pct = int(round(float(inference_stage.get("progress") or 0.0) * 100))
            badges.append(f"inference {inference_state} {pct}%")
        row.update({
            "loaded": loaded,
            "loaded_instance_count": loaded_count,
            "loaded_instances": loaded_instances,
            "offloaded_to_cpu": offloaded_to_cpu,
            "download_state": download_state,
            "load_state": load_state,
            "inference_state": inference_state,
            "status_badges": badges,
            "status_summary": " · ".join(badges) if badges else ("built-in/API" if row.get("cloud") or not row.get("download_supported") else "not downloaded"),
            "lifecycle": lifecycle,
            "placement": self.model_placement(name),
        })
        return row

    def list_models(self, *, force: bool = False) -> list[dict[str, Any]]:
        self._complete_active_download_if_local_payload_ready(None)
        # The model page can call this endpoint frequently.  A full registry.list()
        # scans large model folders to determine downloaded/integrity status; doing
        # that on every button press makes the UI feel frozen.  Cache the static
        # catalog briefly and always layer live lifecycle/loaded status over it.
        rows = self._static_model_catalog_rows(force=force)
        statuses = self.lifecycle.all_statuses().get("models", {})
        for row in rows:
            name = row.get("name")
            self.lifecycle.ensure_model(name)
            self._augment_model_row_status(row, statuses)
        return rows

    def lifecycle_status(self, model_name: str | None = None) -> dict[str, Any]:
        # /api/models/status is polled frequently by the UI.  Do not rescan large
        # model folders here; that made model-page interactions feel frozen and
        # also delayed visible state changes until the user switched tabs.  The
        # static catalog cache is refreshed by /api/models?force=true, explicit
        # rescans, downloads, and load/unload operations; status polling only
        # overlays live lifecycle/placement state.
        if model_name:
            self.lifecycle.ensure_model(model_name)
        else:
            # Avoid ModelRecord.to_dict()/filesystem checks on the hot status
            # endpoint.  The registry keeps the static record map in memory.
            for name in list(getattr(self.registry, "_records", {}) or {}):
                self.lifecycle.ensure_model(name)
        self._sync_lifecycle_from_jobs(model_name)
        self._complete_active_download_if_local_payload_ready(model_name)
        if model_name:
            status = self.lifecycle.model_status(model_name)
            try:
                status["loaded"] = self.registry.is_loaded(model_name)
                status["loaded_instance_count"] = self.registry.loaded_instance_count(model_name) if hasattr(self.registry, "loaded_instance_count") else (1 if status["loaded"] else 0)
                status["loaded_instances"] = self.registry.loaded_instances(model_name) if hasattr(self.registry, "loaded_instances") else []
                status["placement"] = self.registry.loaded_placement(model_name) if hasattr(self.registry, "loaded_placement") else None
            except Exception:
                status["loaded"] = False
            status["placement"] = self.model_placement(model_name)
            return status
        payload = self.lifecycle.all_statuses()
        for name, stages in payload.get("models", {}).items():
            stages["loaded"] = self.registry.is_loaded(name)
            stages["loaded_instance_count"] = self.registry.loaded_instance_count(name) if hasattr(self.registry, "loaded_instance_count") else (1 if stages["loaded"] else 0)
            stages["loaded_instances"] = self.registry.loaded_instances(name) if hasattr(self.registry, "loaded_instances") else []
            stages["placement"] = self.registry.loaded_placement(name) if hasattr(self.registry, "loaded_placement") else None
            stages["placement"] = self.model_placement(name)
        payload["placement"] = self.placement_summary()
        return payload

    def _sync_lifecycle_from_jobs(self, model_name: str | None = None) -> None:
        """Reconcile live lifecycle rows with the durable Jobs table.

        Browser refreshes and periodic UI polling should never be required to
        make model load/run state visible.  This method also cleans up stale
        queued/running lifecycle rows when a worker finished but the final
        lifecycle update was missed by an exception path or process timing.
        """
        payload = self.lifecycle.all_statuses()
        names = [self.lifecycle.normalize_model_name(model_name)] if model_name else list(payload.get("models", {}).keys())
        for name in names:
            stages = payload.get("models", {}).get(name) or self.lifecycle.model_status(name).get("stages", {})
            for stage, row in stages.items():
                job_id = row.get("job_id")
                if not job_id:
                    continue
                try:
                    job = self.db.query_one("SELECT type, status, progress, message, result_json, error FROM jobs WHERE id=?", (int(job_id),))
                except Exception:
                    job = None
                if not job:
                    continue
                status = str(job.get("status") or "").lower()
                progress_value = float(job.get("progress") or 0.0)
                message = job.get("message") or row.get("message") or status
                job_type = str(job.get("type") or "").lower()
                is_unload_job = job_type == "model_unload" or "unload" in message.lower()
                if status in {"queued", "running"}:
                    next_state = "unloading" if stage == "load" and is_unload_job else status
                    if row.get("state") != next_state or abs(float(row.get("progress") or 0.0) - progress_value) > 0.0001:
                        self.lifecycle.update(name, stage, state=next_state, progress=progress_value, message=message, job_id=int(job_id))
                elif status == "completed":
                    result = None
                    try:
                        result = json.loads(job.get("result_json") or "null")
                    except Exception:
                        result = None
                    if stage == "load" and is_unload_job:
                        self.lifecycle.reset(name, "load", message="Model unloaded from RAM/VRAM")
                        self.lifecycle.reset(name, "inference", message="Inference idle after unload")
                    elif row.get("state") != "completed" or float(row.get("progress") or 0.0) < 1.0:
                        self.lifecycle.complete(name, stage, message=message or "Completed", job_id=int(job_id), result=result if isinstance(result, dict) else None)
                elif status == "failed":
                    error = job.get("error") or message or "Failed"
                    if row.get("state") != "failed" or not row.get("error"):
                        self.lifecycle.fail(name, stage, error, job_id=int(job_id))
                elif status in {"cancelled", "canceled"}:
                    self.lifecycle.update(name, stage, state="cancelled", progress=progress_value, message=message or "Cancelled", job_id=int(job_id))


    def _as_float(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def _memory_value_gb(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().lower().replace(" ", "")
        if not text:
            return None
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)(gib|gb|gi|g)?$", text)
        if m:
            return float(m.group(1))
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)(mib|mb|mi|m)$", text)
        if m:
            return float(m.group(1)) / 1024.0
        try:
            return float(text)
        except Exception:
            return None

    def _gpu_index_from_id(self, value: Any) -> int | None:
        # Preserve numeric GPU id 0.  Using ``value or ""`` silently turns
        # device 0 into an empty string, which makes cuda:0 look unselected
        # in placement checks and load/unload controls.
        text = "" if value is None else str(value)
        text = text.strip().lower()
        if text.startswith("cuda:"):
            text = text.split(":", 1)[1]
        try:
            idx = int(text)
            return idx if idx >= 0 else None
        except Exception:
            return None

    def _detected_cuda_devices(self) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
        payload = detect_devices()
        devices: dict[int, dict[str, Any]] = {}
        for row in payload.get("devices") or []:
            idx = self._gpu_index_from_id(row.get("id") if row.get("id") is not None else row.get("index"))
            if idx is None:
                continue
            devices[idx] = {
                **dict(row),
                "index": idx,
                "id": f"cuda:{idx}",
                "total_memory_gb": self._as_float(row.get("total_memory_gb"), 0.0),
                "used_memory_gb": row.get("used_memory_gb"),
                "free_memory_gb": row.get("free_memory_gb"),
            }
        return devices, payload

    def _vram_fraction(self) -> float:
        try:
            if self.settings and bool(getattr(self.settings, "model_vram_use_full_physical_capacity", True)):
                return 1.0
            profile = (self.settings.device_profiles or {}).get("default", {}) if self.settings else {}
            return max(0.50, min(1.0, float(profile.get("max_vram_fraction", 0.92))))
        except Exception:
            return 1.0

    def _runtime_provider_uses_local_vram(self, record: Any, request: Any | None = None) -> bool:
        if not record:
            return False
        provider = str(getattr(record, "provider", "") or "").lower()
        caps = {str(cap).lower() for cap in (getattr(record, "capabilities", []) or [])}
        # Built-in/no-model adapters are pure Python helpers.  They should never
        # reserve cuda:0 or fail when no CUDA runtime is installed.
        if provider == "builtin" or "no-model-download" in caps:
            return False
        if getattr(record, "cloud", False) or provider in {"openai", "openrouter", "anthropic", "cloud"}:
            return False
        runtime = str(getattr(request, "runtime_engine", "") or "").lower()
        if runtime == "cloud":
            return False
        return True

    def _estimate_model_vram_gb(self, record: Any, request: Any | None = None) -> float:
        opts = dict(getattr(request, "options", {}) or {}) if request is not None else {}
        override = opts.get("estimated_vram_gb") or opts.get("vram_gb")
        if override is not None:
            value = self._as_float(override, 0.0)
            if value > 0:
                return value
        if not self._runtime_provider_uses_local_vram(record, request):
            return 0.0
        profiled = self._profiled_vram_estimate_gb(record, request)
        if profiled is not None:
            return round(max(0.0, float(profiled)), 2)
        base = self._as_float(getattr(record, "vram_gb", None), 0.0) or self._as_float(getattr(record, "size_gb", None), 0.0)
        if getattr(record, "provider", "") == "builtin" and not base:
            return 0.05
        quant = str(getattr(request, "quantization", "none") or "none").lower() if request is not None else "none"
        dtype = str(getattr(request, "torch_dtype", "auto") or "auto").lower() if request is not None else "auto"
        if quant == "4bit":
            base *= 0.35
        elif quant == "8bit":
            base *= 0.60
        elif dtype in {"float32", "fp32", "torch.float32"}:
            base *= 1.85
        return round(max(0.0, base), 2)

    def _current_app_reservations_by_gpu(self, *, exclude_model: str | None = None) -> dict[int, list[dict[str, Any]]]:
        reservations: dict[int, list[dict[str, Any]]] = {}
        loaded = []
        try:
            loaded = self.registry.loaded_details()
        except Exception:
            loaded = []
        candidates = [("loaded", row) for row in loaded]
        with self._resource_lock:
            candidates.extend(("loading", deepcopy(row)) for row in self._loading_reservations.values())
        for source, row in candidates:
            name = row.get("model_name")
            if exclude_model and name == exclude_model:
                continue
            if source == "loaded" and isinstance(row, dict) and row.get("offloaded_to_cpu"):
                continue
            per_gpu = row.get("per_gpu_reserved_gb") or {}
            if isinstance(per_gpu, dict) and per_gpu:
                for key, amount in per_gpu.items():
                    idx = self._gpu_index_from_id(key)
                    if idx is None:
                        continue
                    reservations.setdefault(idx, []).append({
                        "model_name": name,
                        "label": row.get("label") or name,
                        "source": source,
                        "reserved_gb": round(self._as_float(amount, 0.0), 2),
                        "sharding_strategy": row.get("sharding_strategy") or "none",
                    })
                continue
            ids = [self._gpu_index_from_id(x) for x in row.get("device_ids") or []]
            ids = [idx for idx in ids if idx is not None]
            estimate = self._as_float(row.get("estimated_vram_gb"), 0.0)
            if ids and estimate > 0:
                share = round(estimate / max(1, len(ids)), 2)
                for idx in ids:
                    reservations.setdefault(idx, []).append({"model_name": name, "label": row.get("label") or name, "source": source, "reserved_gb": share, "sharding_strategy": row.get("sharding_strategy") or "none"})
        return reservations


    def _system_memory_snapshot(self) -> dict[str, Any]:
        """Return a lightweight system-RAM snapshot without requiring psutil.

        The frontend polls model resource state while models are loading or being
        used.  Keep this best-effort and dependency-free so it cannot block the
        model lifecycle UI if psutil is not installed.
        """
        try:
            try:
                import psutil  # type: ignore
                vm = psutil.virtual_memory()
                return {
                    "ok": True,
                    "source": "psutil",
                    "total_gb": round(float(vm.total) / (1024 ** 3), 3),
                    "available_gb": round(float(vm.available) / (1024 ** 3), 3),
                    "used_gb": round(float(vm.used) / (1024 ** 3), 3),
                    "percent": float(vm.percent),
                }
            except Exception:
                pass
            import os
            if hasattr(os, "sysconf"):
                names = os.sysconf_names
                if "SC_PAGE_SIZE" in names and "SC_PHYS_PAGES" in names:
                    page = float(os.sysconf("SC_PAGE_SIZE"))
                    total = page * float(os.sysconf("SC_PHYS_PAGES"))
                    available = None
                    if "SC_AVPHYS_PAGES" in names:
                        available = page * float(os.sysconf("SC_AVPHYS_PAGES"))
                    used = max(0.0, total - float(available or 0.0)) if available is not None else None
                    return {
                        "ok": True,
                        "source": "os.sysconf",
                        "total_gb": round(total / (1024 ** 3), 3),
                        "available_gb": round(float(available or 0.0) / (1024 ** 3), 3) if available is not None else None,
                        "used_gb": round(float(used or 0.0) / (1024 ** 3), 3) if used is not None else None,
                        "percent": round((float(used or 0.0) / total) * 100, 2) if used is not None and total else None,
                    }
            # Windows fallback using GlobalMemoryStatusEx.
            try:
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total = float(stat.ullTotalPhys)
                    available = float(stat.ullAvailPhys)
                    used = max(0.0, total - available)
                    return {
                        "ok": True,
                        "source": "GlobalMemoryStatusEx",
                        "total_gb": round(total / (1024 ** 3), 3),
                        "available_gb": round(available / (1024 ** 3), 3),
                        "used_gb": round(used / (1024 ** 3), 3),
                        "percent": float(stat.dwMemoryLoad),
                    }
            except Exception:
                pass
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": False, "error": "System RAM snapshot unavailable"}

    def model_resource_status(self) -> dict[str, Any]:
        gpu_devices, raw = self._detected_cuda_devices()
        torch_snapshot = self._cuda_memory_snapshot()
        torch_by_index = {
            int(d.get("index")): d
            for d in torch_snapshot.get("devices", [])
            if isinstance(d, dict) and d.get("index") is not None
        }
        fraction = self._vram_fraction()
        reservations = self._current_app_reservations_by_gpu()
        device_rows: list[dict[str, Any]] = []
        for idx in sorted(gpu_devices):
            row = dict(gpu_devices[idx])
            torch_row = torch_by_index.get(idx, {})
            total = self._as_float(row.get("total_memory_gb"), 0.0) or self._as_float(torch_row.get("total_gb"), 0.0)
            app_rows = reservations.get(idx, [])
            app_reserved = round(sum(self._as_float(r.get("reserved_gb"), 0.0) for r in app_rows), 2)
            physical_available = max(0.0, round(total - app_reserved, 2)) if total else 0.0
            usable = round(total * fraction, 2) if total else 0.0
            app_available = max(0.0, round(usable - app_reserved, 2))
            free_detected = self._memory_value_gb(row.get("free_memory_gb"))
            driver_limited = app_available
            if free_detected is not None and total:
                driver_limited = max(0.0, round(min(app_available, free_detected * fraction), 2))
            strict_driver = bool(getattr(self.settings, "strict_driver_free_memory_checks", False)) if self.settings else False
            estimated_available = driver_limited if strict_driver else app_available
            driver_used = self._memory_value_gb(row.get("used_memory_gb"))
            driver_free = free_detected
            torch_used = self._memory_value_gb(torch_row.get("used_gb"))
            torch_free = self._memory_value_gb(torch_row.get("free_gb"))
            actual_used = driver_used if driver_used is not None else (torch_used if torch_used is not None else app_reserved)
            actual_free = driver_free if driver_free is not None else (torch_free if torch_free is not None else max(0.0, total - actual_used))
            actual_source = "nvidia-smi" if driver_used is not None or driver_free is not None else ("torch" if torch_row else "app_reservation")
            row.update({
                "physical_total_memory_gb": total,
                "physical_available_gb": physical_available,
                "usable_memory_gb": usable,
                "app_reserved_gb": app_reserved,
                "app_available_gb": app_available,
                "driver_limited_available_gb": driver_limited,
                "estimated_available_gb": estimated_available,
                "availability_basis": "driver_free_strict" if strict_driver else "app_reservation_budget",
                "strict_driver_free_memory_checks": strict_driver,
                "driver_free_memory_warning": (free_detected is not None and driver_limited + 0.25 < app_available),
                "driver_used_memory_gb": driver_used,
                "driver_free_memory_gb": driver_free,
                "torch_free_gb": torch_free,
                "torch_used_gb": torch_used,
                "torch_allocated_gb": self._memory_value_gb(torch_row.get("torch_allocated_gb")),
                "torch_reserved_gb": self._memory_value_gb(torch_row.get("torch_reserved_gb")),
                "torch_max_allocated_gb": self._memory_value_gb(torch_row.get("torch_max_allocated_gb")),
                "actual_used_memory_gb": round(float(actual_used or 0.0), 3),
                "actual_free_memory_gb": round(float(actual_free or 0.0), 3),
                "actual_memory_source": actual_source,
                "reservations": app_rows,
                "reservation_count": len(app_rows),
            })
            device_rows.append(row)
        loaded = self.registry.loaded_details() if hasattr(self.registry, "loaded_details") else []
        with self._resource_lock:
            loading = list(deepcopy(self._loading_reservations).values())
        return {
            "devices": device_rows,
            "raw_devices": raw,
            "cuda_visible_devices": raw.get("cuda_visible_devices"),
            "vram_fraction": fraction,
            "loaded_models": loaded,
            "loading_reservations": loading,
            "system_ram": self._system_memory_snapshot(),
            "torch_cuda_snapshot": torch_snapshot,
            "actual_memory_poll_at": time.time(),
            "warnings": raw.get("warnings") or [],
        }

    def _request_device_ids(self, request: Any, record: Any, gpu_devices: dict[int, dict[str, Any]]) -> list[int]:
        device = str(getattr(request, "device", "auto") or "auto").strip().lower()
        if device == "cpu" or not self._runtime_provider_uses_local_vram(record, request):
            return []
        explicit_idx = self._gpu_index_from_id(device)
        raw_ids = list(getattr(request, "device_ids", []) or [])
        if raw_ids:
            parsed = [self._gpu_index_from_id(x) for x in raw_ids]
            ids: list[int] = []
            for idx in parsed:
                if idx is not None and idx not in ids:
                    ids.append(idx)
            if explicit_idx is not None and explicit_idx not in ids:
                raise RuntimeError(
                    f"GPU selection conflict: device={device!r} but device_ids={ids}. "
                    "Use matching values so the selected model cannot be placed on a different GPU."
                )
            return ids
        if explicit_idx is not None:
            return [explicit_idx]
        default_ids = list(getattr(self.settings, "default_model_device_ids", []) or []) if self.settings else []
        if default_ids:
            ids: list[int] = []
            for value in default_ids:
                idx = self._gpu_index_from_id(value)
                if idx is not None and idx not in ids:
                    ids.append(idx)
            return ids
        return [sorted(gpu_devices.keys())[0]] if gpu_devices else []

    def _placement_for_request(self, request: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
        model_name = request.model_name
        record = self.registry.get_record(model_name)
        gpu_devices, _raw = self._detected_cuda_devices()
        estimate = self._estimate_model_vram_gb(record, request)
        local_vram = self._runtime_provider_uses_local_vram(record, request)
        selected_ids = self._request_device_ids(request, record, gpu_devices)
        requested_device = str(getattr(request, "device", "auto") or "auto").strip() or "auto"
        if local_vram and requested_device.lower().startswith("cuda") and not gpu_devices:
            raise RuntimeError("No CUDA GPUs were detected. Select CPU/auto or install a CUDA-enabled torch/runtime first.")
        if local_vram:
            missing = [idx for idx in selected_ids if idx not in gpu_devices]
            if missing:
                detected = ", ".join(f"cuda:{idx}" for idx in sorted(gpu_devices)) or "none"
                raise RuntimeError(f"Requested GPU(s) {missing} were not detected. Detected CUDA devices: {detected}.")
            not_torch_ready = [idx for idx in selected_ids if not bool(gpu_devices.get(idx, {}).get("torch_ready"))]
            if not_torch_ready:
                raise RuntimeError(
                    "Selected GPU(s) are visible to NVIDIA tools but PyTorch CUDA is not ready in this app environment: "
                    + ", ".join(f"cuda:{idx}" for idx in not_torch_ready)
                    + ". The launch/install scripts clear accidental CUDA_VISIBLE_DEVICES masking by default; run install.bat/update.bat after deleting the env, then verify torch sees all GPUs."
                )
        placement_warning = ""
        strategy = str(getattr(request, "sharding_strategy", "none") or "none").lower()
        if strategy not in {"none", "auto", "balanced", "balanced_low_0", "sequential", "custom"}:
            strategy = "none"
        if len(selected_ids) > 1 and strategy == "none":
            strategy = "balanced"
        if local_vram and selected_ids and strategy != "none":
            min_gpus = int(getattr(record, "min_gpus", 1) or 1)
            max_gpus = getattr(record, "max_gpus", None)
            if len(selected_ids) < min_gpus:
                raise RuntimeError(
                    f"{getattr(record, 'label', model_name)} needs at least {min_gpus} selected GPU(s) for the requested sharding mode."
                )
            if max_gpus is not None:
                try:
                    max_gpus_i = int(max_gpus)
                    if len(selected_ids) > max_gpus_i:
                        raise RuntimeError(f"{getattr(record, 'label', model_name)} is capped at {max_gpus_i} selected GPU(s).")
                except RuntimeError:
                    raise
                except Exception:
                    pass
            if len(selected_ids) > 1 and not getattr(record, "supports_sharding", False) and strategy != "custom":
                provider = str(getattr(record, "provider", "") or "").lower()
                runtime_engine = str(getattr(request, "runtime_engine", "") or "").lower()
                caps = {str(cap).lower() for cap in (getattr(record, "capabilities", []) or [])}
                hf_like = provider in {"huggingface", "hf", "transformers"} or (runtime_engine in {"transformers", "auto", ""} and caps.intersection({"llm", "vlm", "chat", "caption", "vision-language"}))
                if not hf_like:
                    raise RuntimeError(
                        f"{getattr(record, 'label', model_name)} is not marked as sharding-compatible in the registry. "
                        "Use one GPU, choose custom only if you know the adapter supports your device map, or update the registry metadata."
                    )
                placement_warning = (
                    f"{getattr(record, 'label', model_name)} is not explicitly marked sharding-compatible, but it is HF/Transformers-like. "
                    "The app will try Accelerate/Transformers device_map sharding with the selected GPUs."
                )
        device = "cpu" if not selected_ids and (requested_device.lower() == "cpu" or not gpu_devices or not local_vram) else (f"cuda:{selected_ids[0]}" if selected_ids else requested_device)
        runtime_opts: dict[str, Any] = {}
        if selected_ids:
            runtime_opts["device_ids"] = selected_ids
            runtime_opts["sharding_strategy"] = strategy
        max_memory_raw = dict(getattr(request, "max_memory", {}) or {})
        max_memory_gb: dict[int, float] = {}
        for key, value in max_memory_raw.items():
            idx = self._gpu_index_from_id(key)
            parsed = self._memory_value_gb(value)
            if idx is not None and parsed is not None:
                max_memory_gb[idx] = parsed
        if max_memory_raw:
            runtime_opts["max_memory"] = max_memory_raw
        per_gpu: dict[int, float] = {}
        if selected_ids and estimate > 0:
            if strategy == "none" or len(selected_ids) == 1:
                per_gpu[selected_ids[0]] = estimate
            else:
                share = round(estimate / max(1, len(selected_ids)), 2)
                for idx in selected_ids:
                    per_gpu[idx] = share
        if selected_ids and strategy != "none" and not max_memory_raw:
            fraction = self._vram_fraction()
            generated: dict[int, str] = {}
            for idx in selected_ids:
                total = self._as_float(gpu_devices.get(idx, {}).get("total_memory_gb"), 0.0)
                generated[idx] = f"{max(1.0, math.floor(total * fraction * 10) / 10):.1f}GiB" if total else "22GiB"
            runtime_opts["max_memory"] = generated
        placement = {
            "model_name": model_name,
            "label": getattr(record, "label", model_name),
            "device": device,
            "device_ids": selected_ids,
            "sharding_strategy": strategy,
            "requested_device": requested_device,
            "estimated_vram_gb": estimate,
            "per_gpu_reserved_gb": {str(k): round(v, 2) for k, v in per_gpu.items()},
            "torch_dtype": getattr(request, "torch_dtype", "auto"),
            "quantization": getattr(request, "quantization", "none"),
            "runtime_engine": getattr(request, "runtime_engine", "transformers"),
            "tensor_parallel_size": int(getattr(request, "tensor_parallel_size", 1) or 1),
            "max_memory": runtime_opts.get("max_memory") or max_memory_raw,
            "warnings": [placement_warning] if placement_warning else [],
            "sharding_runtime_support": {"multi_gpu_selected": len(selected_ids) > 1, "device_map_strategy": strategy if len(selected_ids) > 1 else "none", "uses_transformers_device_map": bool(selected_ids and strategy != "none")},
        }
        return device, runtime_opts, placement

    def _validate_and_reserve_placement(self, request: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
        with self._resource_lock:
            device, runtime_opts, placement = self._placement_for_request(request)
            selected_ids = list(placement.get("device_ids") or [])
            per_gpu = {self._gpu_index_from_id(k): self._as_float(v, 0.0) for k, v in (placement.get("per_gpu_reserved_gb") or {}).items()}
            per_gpu = {k: v for k, v in per_gpu.items() if k is not None and v > 0}
            if per_gpu:
                resources = self.model_resource_status()
                available = {self._gpu_index_from_id(d.get("id")): self._as_float(d.get("estimated_available_gb"), 0.0) for d in resources.get("devices") or []}
                available = {k: v for k, v in available.items() if k is not None}
                failures = []
                resource_rows = {self._gpu_index_from_id(d.get("id")): d for d in resources.get("devices") or []}
                for idx, needed in per_gpu.items():
                    allowed_by_max = None
                    max_mem = placement.get("max_memory") or {}
                    if isinstance(max_mem, dict):
                        allowed_by_max = self._memory_value_gb(max_mem.get(idx) if idx in max_mem else max_mem.get(str(idx)))
                    cap = available.get(idx, 0.0)
                    if allowed_by_max is not None:
                        cap = min(cap, allowed_by_max)
                    if needed > cap + 0.01:
                        row = resource_rows.get(idx) or {}
                        detail = f"cuda:{idx} needs ~{needed:.2f} GB but has ~{cap:.2f} GB available"
                        if row:
                            detail += (
                                f" (budget={row.get('availability_basis')}; total={self._as_float(row.get('total_memory_gb'), 0.0):.2f} GB; "
                                f"usable={self._as_float(row.get('usable_memory_gb'), 0.0):.2f} GB; app_reserved={self._as_float(row.get('app_reserved_gb'), 0.0):.2f} GB; "
                                f"driver_free={self._memory_value_gb(row.get('free_memory_gb')) if row.get('free_memory_gb') is not None else 'unknown'} GB)"
                            )
                        failures.append(detail)
                if failures:
                    record = self.registry.get_record(request.model_name)
                    profiles = self._model_memory_profiles(record)
                    alternatives = []
                    if profiles:
                        for key in ("8bit", "sfp8", "4bit", "q4_0"):
                            val = profiles.get(key)
                            if val:
                                alternatives.append(f"{key}: ~{val:.2f} GB")
                    note = f" Memory profiles for {getattr(record, 'label', request.model_name)}: " + ", ".join(alternatives) + "." if alternatives else ""
                    memory_note = getattr(record, "memory_note", None)
                    if memory_note:
                        note += f" {memory_note}"
                    raise RuntimeError(
                        "Estimated VRAM placement would exceed available capacity: "
                        + "; ".join(failures)
                        + ". Select more GPUs, unload another model, set quantization to 8bit/4bit where supported, choose CPU/cloud, or lower the max-memory reservation."
                        + note
                    )
            self._loading_reservations[request.model_name] = deepcopy(placement)
            return device, runtime_opts, placement

    def _release_loading_reservation(self, model_name: str | None) -> None:
        if not model_name:
            return
        with self._resource_lock:
            self._loading_reservations.pop(str(model_name), None)

    def _assert_loaded_placement_compatible(self, request: Any) -> None:
        model_name = getattr(request, "model_name", None)
        if not model_name or not self.registry.is_loaded(model_name):
            return
        opts = getattr(request, "options", {}) or {}
        if isinstance(opts, dict) and opts.get("use_loaded_model_placement"):
            # Quick Tag/agent queues can intentionally ignore newly selected
            # placement controls and use the already-loaded residency for this
            # model. This prevents a stale cuda:# control from blocking a run
            # against a model the user already loaded elsewhere.
            return
        placement = self.registry.loaded_placement(model_name) if hasattr(self.registry, "loaded_placement") else None
        if not placement:
            return
        requested_ids = [self._gpu_index_from_id(x) for x in (getattr(request, "device_ids", []) or [])]
        requested_ids = [idx for idx in requested_ids if idx is not None]
        loaded_ids = [self._gpu_index_from_id(x) for x in (placement.get("device_ids") or [])]
        loaded_ids = [idx for idx in loaded_ids if idx is not None]
        if requested_ids and loaded_ids and set(requested_ids) != set(loaded_ids):
            raise RuntimeError(
                f"{model_name} is already loaded on {', '.join('cuda:'+str(i) for i in loaded_ids)}. "
                f"Unload it before changing placement to {', '.join('cuda:'+str(i) for i in requested_ids)}."
            )
        requested_device = str(getattr(request, "device", "") or "").lower()
        loaded_device = str(placement.get("device") or "").lower()
        if requested_device.startswith("cuda:") and loaded_device.startswith("cuda:") and requested_device != loaded_device and not requested_ids:
            raise RuntimeError(f"{model_name} is already loaded on {loaded_device}. Unload it before changing placement to {requested_device}.")

    def is_model_loaded(self, model_name: str | None) -> bool:
        if not model_name:
            return False
        try:
            return self.registry.is_loaded(model_name)
        except Exception:
            return False

    def mark_already_loaded(self, model_name: str | None) -> dict[str, Any]:
        name = str(model_name or "").strip()
        residency = self.registry.loaded_placement(name) if name and hasattr(self.registry, "loaded_placement") else None
        result = {"model_name": name, "loaded": bool(name), "already_loaded": True, "residency": residency, "placement": residency}
        if name:
            self.lifecycle.update(name, "load", state="completed", progress=1.0, message="Model already loaded in memory", result=result)
        return result


    def _path_size_gb(self, path: Path | None) -> float:
        if not path:
            return 0.0
        try:
            if path.is_file():
                return round(path.stat().st_size / (1024**3), 3)
            total = 0
            for f in path.rglob("*"):
                if f.is_file():
                    try:
                        total += f.stat().st_size
                    except OSError:
                        pass
            return round(total / (1024**3), 3)
        except Exception:
            return 0.0

    def model_download_size_estimate(self, model_name: str | None) -> dict[str, Any]:
        if not model_name:
            return {"model_name": model_name, "estimated_total_gb": None, "local_existing_gb": 0.0, "estimated_remaining_gb": None}
        try:
            record = self.registry.get_record(str(model_name))
        except Exception:
            return {"model_name": model_name, "estimated_total_gb": None, "local_existing_gb": 0.0, "estimated_remaining_gb": None}
        total = self._as_float(getattr(record, "size_gb", None), 0.0) or None
        local = record.local_dir(self.registry.model_root, self.registry.external_model_roots) if hasattr(record, "local_dir") else None
        existing = self._path_size_gb(local if local and local.exists() else None)
        remaining = None if total is None else max(0.0, round(total - existing, 3))
        return {"model_name": model_name, "label": getattr(record, "label", model_name), "estimated_total_gb": total, "local_existing_gb": existing, "estimated_remaining_gb": remaining, "target_path": str(local) if local else None}

    def _download_status_name(self, request: ModelDownloadRequest) -> str:
        return request.model_name or request.repo_id or request.local_dir or "custom-model-download"

    def download(self, request: ModelDownloadRequest, progress=None, job_id: int | None = None) -> dict[str, Any]:
        model_name = self._download_status_name(request)
        if request.dry_run:
            self.lifecycle.update(model_name, "download", state="running", progress=0.05, message="Planning model download", job_id=job_id)
        else:
            self.lifecycle.update(model_name, "download", state="running", progress=0.0, message="Downloading model weights", job_id=job_id)
        tracker = self.lifecycle.progress_callback(model_name, "download", progress, job_id=job_id)
        try:
            result = self.registry.download_model(
                name=request.model_name,
                repo_id=request.repo_id,
                token=request.token or ((self.settings.resolve_api_token("huggingface") if hasattr(self.settings, "resolve_api_token") else self.settings.huggingface_token) if self.settings else None),
                revision=request.revision,
                local_dir=request.local_dir,
                allow_patterns=request.allow_patterns or None,
                ignore_patterns=request.ignore_patterns or None,
                dry_run=request.dry_run,
                force_download=request.force_download,
                progress=tracker,
                parallel_downloads=request.parallel_downloads,
            )
            if tracker:
                tracker(0.98, "Finalizing local model catalog entry")
            try:
                self.reconcile_local_assets()
            except Exception:
                pass
            self.invalidate_model_catalog_cache()
            self.lifecycle.complete(model_name, "download", message="Download dry-run completed" if request.dry_run else "Model download completed", job_id=job_id, result=result)
            return result
        except Exception as exc:
            self.lifecycle.fail(model_name, "download", exc, job_id=job_id)
            raise

    def load(self, request: ModelLoadRequest, progress=None, job_id: int | None = None) -> dict[str, Any]:
        self._complete_active_download_if_local_payload_ready(request.model_name)
        if self.lifecycle.is_active(request.model_name, "download"):
            raise RuntimeError(f"{request.model_name} is still downloading. Wait for the download status circle to finish before loading it.")
        if self.registry.is_loaded(request.model_name):
            result = self.mark_already_loaded(request.model_name)
            if progress:
                progress(1.0, f"{request.model_name}: already loaded")
            return result
        return self._load_model_from_request(request, progress=progress, job_id=job_id)

    def _load_model_from_request(self, request: Any, progress=None, job_id: int | None = None) -> dict[str, Any]:
        model_name = request.model_name
        if self.registry.is_loaded(model_name):
            result = self.mark_already_loaded(model_name)
            if progress:
                progress(1.0, f"{model_name}: already loaded")
            return result
        current_load = self.lifecycle.model_status(model_name).get("stages", {}).get("load", {})
        current_state = str(current_load.get("state") or "idle")
        current_job_id = current_load.get("job_id")
        active_load = bool(current_load.get("active")) or current_state in {"queued", "running"}
        same_queued_worker = current_state == "queued" and job_id is not None and current_job_id in (None, job_id)
        if active_load and not same_queued_worker:
            raise RuntimeError(f"{model_name} is already loading. Wait for the load status circle to complete before using it.")

        placement: dict[str, Any] | None = None
        try:
            # This reserves the selected GPUs before the adapter starts allocating
            # memory, so simultaneous load jobs cannot overcommit the same VRAM.
            effective_device, runtime_opts, placement = self._validate_and_reserve_placement(request)
            summary = "CPU/API" if not placement.get("device_ids") else ",".join(f"cuda:{idx}" for idx in placement.get("device_ids") or [])
            self.lifecycle.update(
                model_name,
                "load",
                state="running",
                progress=0.02,
                message=f"Loading model into memory on {summary}",
                job_id=job_id,
                result={"placement": placement},
            )
            if progress:
                progress(0.02, f"{model_name}: loading model into memory on {summary}")
            opts = self._runtime_options(request)
            opts.update(runtime_opts)
            opts["placement"] = placement
            try:
                record_for_load = self.registry.get_record(model_name)
            except Exception:
                record_for_load = None
            if record_for_load is not None and not getattr(record_for_load, "cloud", False) and getattr(record_for_load, "download_supported", False):
                local_ready = False
                local_path = None
                try:
                    local = record_for_load.complete_local_dir(self.registry.model_root, self.registry.external_model_roots)
                    # A migrated install may have just been copied in while the
                    # app is already running.  If the cached catalog did not know
                    # about it, reconcile once before deciding Load is impossible.
                    if not local:
                        self.invalidate_model_catalog_cache()
                        try:
                            self.reconcile_local_assets()
                        except Exception:
                            pass
                        local = record_for_load.complete_local_dir(self.registry.model_root, self.registry.external_model_roots)
                    local_ready = bool(local and local.exists())
                    local_path = str(local) if local else None
                    if local_ready and local_path:
                        # Force every adapter/HF helper to use the exact local
                        # snapshot/file.  Without this, Transformers can fall
                        # through to repo_id and silently redownload weights.
                        opts.setdefault("model_id", local_path)
                        opts.setdefault("dct_resolved_local_model_path", local_path)
                        opts.setdefault("local_files_only", True)
                        opts.setdefault("allow_support_file_repair", False)
                        opts.setdefault("prevent_automatic_download", True)
                except Exception:
                    local_ready = False
                allow_remote = bool(opts.get("allow_remote_load") or opts.get("download_on_load") or opts.get("allow_download_on_load"))
                if not local_ready and not allow_remote:
                    candidates = []
                    try:
                        for candidate in record_for_load.candidate_local_dirs(self.registry.model_root, self.registry.external_model_roots)[:12]:
                            candidates.append(str(candidate))
                    except Exception:
                        candidates = []
                    raise RuntimeError(
                        f"No complete local model payload was found for {getattr(record_for_load, 'label', model_name)} ({model_name}). "
                        "Load is local-only by default and will not download model weights implicitly. "
                        "Use Models > Rescan after migration, add the old install/models folder as an external model root, "
                        "or use Queue Download/Update explicitly. "
                        f"Checked: {candidates}."
                    )
            try:
                result = self.registry.load_model(model_name, device=effective_device, **opts)
            except Exception as load_exc:
                try:
                    record = self.registry.get_record(model_name)
                    label = getattr(record, "label", model_name)
                    repo = getattr(record, "repo_id", None) or getattr(record, "api_model_id", None) or model_name
                except Exception:
                    label, repo = model_name, model_name
                raise RuntimeError(
                    f"Load failed for {label} ({model_name}). Source/repo/local path: {repo}. "
                    f"Effective device: {effective_device}. Placement plan: {placement}. "
                    "The load button should now surface this message in the job/lifecycle error instead of silently doing nothing. "
                    f"Underlying error: {load_exc}"
                ) from load_exc
            self._release_loading_reservation(model_name)
            self._commit_model_placement(model_name, placement, result)
            result.setdefault("placement", placement)
            try:
                result["resource_after"] = self.model_resource_status()
            except Exception:
                pass
            self.lifecycle.complete(model_name, "load", message=f"Model loaded into memory on {summary}", job_id=job_id, result=result)
            if progress:
                progress(1.0, f"{model_name}: loaded into memory")
            return result
        except Exception as exc:
            self._release_loading_reservation(model_name)
            self.lifecycle.fail(model_name, "load", exc, job_id=job_id)
            raise

    def unload(self, model_name: str | None = None, progress=None, job_id: int | None = None) -> dict[str, Any]:
        targets = [model_name] if model_name else self.registry.loaded_names()
        targets = [str(t) for t in targets if t]
        if not targets:
            return {"unloaded": [], "message": "No model adapters were loaded."}
        for idx, name in enumerate(targets):
            frac = max(0.02, idx / max(1, len(targets)) * 0.35)
            self.lifecycle.update(name, "load", state="unloading", progress=frac, message="Unloading model from RAM/VRAM", job_id=job_id, extra={"loaded": False})
            if progress:
                progress(frac, f"Unloading {name} from RAM/VRAM")
        result = self.registry.unload(model_name)
        unloaded = result.get("unloaded", [])
        for name in unloaded:
            self._release_model_placement(name)
            self._release_loading_reservation(name)
        if model_name:
            self._release_loading_reservation(model_name)
        else:
            self._release_model_placement(None)
            with self._resource_lock:
                self._loading_reservations.clear()
        for idx, name in enumerate(unloaded, start=1):
            frac = 0.35 + (0.55 * idx / max(1, len(unloaded)))
            self.lifecycle.update(name, "load", state="unloading", progress=frac, message="Releasing model memory and cache", job_id=job_id, extra={"loaded": False})
            if progress:
                progress(frac, f"Releasing {name}")
            self.lifecycle.reset(name, "load", message="Model unloaded from RAM/VRAM")
            self.lifecycle.update(name, "load", state="idle", progress=0.0, message="Model unloaded from RAM/VRAM", job_id=job_id, extra={"loaded": False})
            self.lifecycle.reset(name, "inference", message="Inference idle after unload")
            if progress:
                progress(1.0, f"Unloaded {name}")
        for name in set(targets) - set(unloaded):
            self.lifecycle.update(name, "load", state="idle", progress=0.0, message="Model was not loaded", job_id=job_id)
            self.lifecycle.reset(name, "inference", message="Inference idle")
        try:
            result["resource_after"] = self.model_resource_status()
        except Exception:
            pass
        return result


    def media_ids_for_request(self, request: ModelRunRequest) -> list[int]:
        if request.media_ids:
            return request.media_ids
        if request.dataset_id:
            rows = self.db.query(
                "SELECT id FROM media WHERE dataset_id=? AND active=1 AND media_type IN ('image','animation') ORDER BY id ASC",
                (request.dataset_id,),
            )
            return [row["id"] for row in rows]
        return []

    def run(self, request: ModelRunRequest, run_id: int | None, progress) -> dict[str, Any]:
        model_name = request.model_name
        if self.lifecycle.is_active(model_name, "download"):
            raise RuntimeError(f"{model_name} is still downloading. Wait for the download status circle to finish before running inference.")
        if self.lifecycle.is_active(model_name, "load") and not self.registry.is_loaded(model_name):
            raise RuntimeError(f"{model_name} is still loading into memory. Wait for the load status circle to finish before running inference.")
        media_ids = self.media_ids_for_request(request)
        if not media_ids:
            self.lifecycle.complete(model_name, "inference", message="No media selected", job_id=run_id, result={"processed": 0})
            return {"processed": 0, "message": "No media selected"}
        workers = max(1, min(int(request.parallel_workers or 1), 16))
        applied_tags = 0
        applied_captions = 0
        predictions = 0
        prediction_preview: dict[int, list[str]] = {}
        candidate_tags_by_media: dict[int, list[str]] = {}
        candidate_scores_by_media: dict[int, list[dict[str, Any]]] = {}
        applied_tags_by_media: dict[int, list[str]] = {}
        effective_task = "tag" if request.model_name in {"redrocket-jtp-3", "redrocket-hydra-3-5"} else request.task
        try:
            effective_threshold = float(request.threshold)
        except Exception:
            effective_threshold = 0.70
        if not (0.0 < effective_threshold <= 1.0):
            # Quick Tag UI surfaces must never turn a blank input into threshold 0.0,
            # because that commits every emitted model label.  Non-quick advanced
            # API callers may still intentionally pass a tiny positive threshold.
            effective_threshold = 0.70 if (request.options or {}).get("quick_tag_surface") else max(0.0, min(1.0, effective_threshold if effective_threshold == effective_threshold else 0.70))

        def job_progress(value: float, message: str) -> None:
            if progress:
                progress(value, message)

        try:
            # Loading is tracked separately from inference so compatibility/load
            # failures are visible before item processing starts.  Job progress is
            # scaled so the regular Jobs table remains monotonic.
            if not self.registry.is_loaded(model_name):
                def load_progress(value: float, message: str = "") -> None:
                    job_progress(min(0.15, max(0.0, float(value or 0.0)) * 0.15), message)
                self._load_model_from_request(request, progress=load_progress, job_id=run_id)
            else:
                self._assert_loaded_placement_compatible(request)
                self.lifecycle.update(model_name, "load", state="completed", progress=1.0, message="Model already loaded in memory")
                job_progress(0.05, f"{model_name}: already loaded")

            self.lifecycle.update(model_name, "inference", state="running", progress=0.0, message="Inference started", job_id=run_id)

            def process_one(media_id: int) -> dict[str, Any]:
                media = self.media.get(media_id)
                if not media:
                    return {"media_id": media_id, "skipped": True}
                kwargs = self._runtime_options(request)
                kwargs.update({"threshold": effective_threshold, "prompt": request.prompt})
                if effective_task == "caption_split":
                    kwargs["caption"] = media.caption
                runtime_device = self._runtime_device_for_request(request.model_name, request)
                pred = self._registry_predict_with_vram_guard(request.model_name, Path(media.path), device=runtime_device, options=request.options, **kwargs)
                profile_key = str((request.options or {}).get("tag_profile") or (request.options or {}).get("profile_key") or "e621")
                apply_aliases = bool((request.options or {}).get("apply_model_tag_aliases", True))
                apply_implications = bool((request.options or {}).get("apply_model_tag_implications", True))
                payload = {
                    "kind": pred.kind,
                    "tags": pred.tags,
                    "caption": pred.caption,
                    "classes": pred.classes,
                    "embedding": pred.embedding,
                    "masks": pred.masks,
                    "raw": pred.raw,
                }
                desired_tag_text_mode = str((request.options or {}).get("tag_text_mode") or getattr(self.settings, "tag_text_mode_active", "underscores") or "underscores")
                payload = self.tags.normalize_model_prediction_payload(
                    payload,
                    profile_key=profile_key,
                    apply_aliases=apply_aliases,
                    apply_implications=apply_implications,
                    text_mode=desired_tag_text_mode,
                )
                payload["tag_text_mode"] = desired_tag_text_mode
                self.media.add_prediction(media_id, run_id, request.model_name, effective_task, payload)
                scored_candidates = payload.get("tags") or payload.get("classes") or []

                def _score_key(value: Any) -> str:
                    return str(value or "").strip().lower().replace(" ", "_")

                score_lookup: dict[str, float] = {}

                def _remember_score(label: Any, value: Any) -> None:
                    key = _score_key(label)
                    if not key:
                        return
                    try:
                        score = max(0.0, min(1.0, float(value)))
                    except Exception:
                        return
                    # Keep the strongest score when aliases/duplicates collapse.
                    score_lookup[key] = max(score_lookup.get(key, 0.0), score)

                def _collect_scores(obj: Any) -> None:
                    if isinstance(obj, dict):
                        label = obj.get("tag") or obj.get("label") or obj.get("class") or obj.get("name")
                        score = obj.get("score") or obj.get("confidence") or obj.get("probability") or obj.get("prob")
                        if label is not None and score is not None:
                            _remember_score(label, score)
                        for value in obj.values():
                            if isinstance(value, (list, tuple, dict)):
                                _collect_scores(value)
                    elif isinstance(obj, (list, tuple)):
                        if len(obj) >= 2 and not isinstance(obj[0], (list, tuple, dict)):
                            _remember_score(obj[0], obj[1])
                        else:
                            for value in obj:
                                _collect_scores(value)

                _collect_scores(pred.tags)
                _collect_scores(pred.classes)
                _collect_scores(pred.raw)
                _collect_scores(payload.get("classes"))

                candidate_tags = []
                candidate_score_rows: list[dict[str, Any]] = []
                for item in scored_candidates:
                    tag = None
                    score = 1.0
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        tag = item[0]
                        try:
                            score = float(item[1])
                        except Exception:
                            score = 1.0
                    elif isinstance(item, dict):
                        tag = item.get("tag") or item.get("label") or item.get("class")
                        try:
                            score = float(item.get("score") or item.get("confidence") or item.get("probability") or 1.0)
                        except Exception:
                            score = 1.0
                    elif isinstance(item, str):
                        # Some normalization paths emit tags as bare strings even
                        # when the adapter/raw payload still contained per-label
                        # probabilities.  Reattach that original score before
                        # applying the threshold; only fully thresholded adapters
                        # with no recoverable score are treated as accepted labels.
                        tag = item
                        score = score_lookup.get(_score_key(item), 1.0)
                    if not tag:
                        continue
                    tag_text = str(tag)
                    score = max(0.0, min(1.0, float(score)))
                    candidate_score_rows.append({"tag": tag_text, "score": score})
                    if score >= effective_threshold:
                        candidate_tags.append(tag_text)
                candidate_tags_by_media[media_id] = candidate_tags
                candidate_scores_by_media[media_id] = candidate_score_rows
                prediction_preview[media_id] = candidate_tags[:25]
                result = {"media_id": media_id, "prediction": 1, "tags": 0, "captions": 0}
                if request.apply_tags and candidate_tags:
                    current = self.tags.get_tags(media_id)
                    merged = list(current)
                    newly_added = []
                    for tag in candidate_tags:
                        if tag not in merged:
                            merged.append(tag)
                            newly_added.append(tag)
                    applied = self.tags.set_tags(
                        media_id,
                        merged,
                        source=request.model_name,
                        save_sidecar=True,
                        profile_key=profile_key,
                        order_strategy=str((request.options or {}).get("order_strategy") or "retain"),
                    )
                    applied_tags_by_media[media_id] = candidate_tags
                    result["tags"] = len(newly_added)
                if request.apply_caption and pred.caption:
                    self.db.upsert_caption(media_id, pred.caption, source=request.model_name)
                    result["captions"] = 1
                return result

            def mark_inference(done: int) -> None:
                frac = done / max(1, len(media_ids))
                msg = f"{request.model_name}: inference {done}/{len(media_ids)}"
                self.lifecycle.update(model_name, "inference", state="running", progress=frac, message=msg, job_id=run_id)
                job_progress(0.15 + (0.85 * frac), msg)

            if workers > 1 and len(media_ids) > 1 and request.sharding_strategy == "none":
                # Safe parallelism for many independent media items.  Sharded single
                # model runs intentionally stay sequential so layers are not raced.
                done = 0
                with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dct-model-run") as ex:
                    futs = {ex.submit(process_one, media_id): media_id for media_id in media_ids}
                    for fut in as_completed(futs):
                        out = fut.result()
                        done += 1
                        predictions += int(out.get("prediction") or 0)
                        applied_tags += int(out.get("tags") or 0)
                        applied_captions += int(out.get("captions") or 0)
                        mark_inference(done)
            else:
                for idx, media_id in enumerate(media_ids, start=1):
                    out = process_one(media_id)
                    predictions += int(out.get("prediction") or 0)
                    applied_tags += int(out.get("tags") or 0)
                    applied_captions += int(out.get("captions") or 0)
                    mark_inference(idx)
            result = {
                "processed": len(media_ids),
                "predictions": predictions,
                "applied_tags": applied_tags,
                "applied_captions": applied_captions,
                "parallel_workers": workers,
                "sharding_strategy": request.sharding_strategy,
                "effective_task": effective_task,
                "threshold": effective_threshold,
                "preview_tags_by_media": prediction_preview,
                "candidate_tags_by_media": candidate_tags_by_media,
                "candidate_scores_by_media": candidate_scores_by_media,
                "applied_tags_by_media": applied_tags_by_media,
            }
            self.lifecycle.complete(model_name, "inference", message="Inference completed", job_id=run_id, result=result)
            return result
        except Exception as exc:
            self.lifecycle.fail(model_name, "inference", exc, job_id=run_id)
            raise


    def _provider_token_profile(self, request: Any, provider: str) -> str | None:
        opts = getattr(request, "options", {}) or {}
        if not isinstance(opts, dict):
            return None
        provider_key = str(provider or "").lower().replace("-", "_")
        return (
            opts.get("token_profile")
            or opts.get(f"{provider_key}_token_profile")
            or opts.get(f"{provider_key}_token_name")
            or opts.get("api_token_profile")
            or opts.get("api_token_name")
        )

    def _inject_provider_token(self, runtime: dict[str, Any], provider: str, request: Any | None = None) -> None:
        if not self.settings:
            return
        key = str(provider or "").lower().replace("-", "_")
        profile = self._provider_token_profile(request, key) if request is not None else None
        token = self.settings.resolve_api_token(key, profile) if hasattr(self.settings, "resolve_api_token") else None
        if key in {"openrouter"} and token:
            runtime.setdefault("openrouter_token", token)
        elif key in {"openai"} and token:
            runtime.setdefault("openai_api_key", token)
        elif key in {"anthropic"} and token:
            runtime.setdefault("anthropic_api_key", token)
        elif key in {"huggingface", "hf"} and token:
            runtime.setdefault("token", token)
        elif key in {"xai", "x_ai", "grok"} and token:
            runtime.setdefault("xai_api_key", token)
        elif key in {"runpod"} and token:
            runtime.setdefault("runpod_api_key", token)
        elif key in {"vastai", "vast_ai"} and token:
            runtime.setdefault("vastai_api_key", token)
        elif key in {"lambda_labs", "lambda"} and token:
            runtime.setdefault("lambda_labs_api_key", token)

    def _chat_reasoning_options(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        opts = dict(options or {})
        settings = self.settings
        mode = str(opts.get("thinking_mode") or opts.get("deliberation_mode") or (getattr(settings, "assistant_thinking_mode", "balanced") if settings else "balanced") or "balanced").strip().lower()
        if mode not in {"off", "fast", "balanced", "deep"}:
            mode = "balanced"
        effort = str(opts.get("reasoning_effort") or opts.get("effort") or (getattr(settings, "assistant_reasoning_effort", "medium") if settings else "medium") or "medium").strip().lower()
        if effort not in {"none", "low", "medium", "high", "max"}:
            effort = "medium"
        show_plan_default = bool(getattr(settings, "assistant_show_visible_plan", True)) if settings else True
        show_plan = bool(opts.get("show_visible_plan", opts.get("visible_plan", opts.get("plan_before_answer", show_plan_default))))
        show_trace_default = bool(getattr(settings, "assistant_show_live_chain_of_thought", True)) if settings else True
        show_trace = bool(opts.get("show_live_chain_of_thought", opts.get("show_live_reasoning_trace", show_trace_default)))
        try:
            planning_passes = int(opts.get("planning_passes", opts.get("planner_passes", getattr(settings, "assistant_planning_passes", 1) if settings else 1)) or 0)
        except Exception:
            planning_passes = 1
        if mode == "off" or effort == "none":
            planning_passes = 0
            show_plan = False
        elif mode == "fast":
            planning_passes = min(planning_passes, 1)
        elif mode == "deep":
            planning_passes = max(planning_passes, 1)
        planning_passes = max(0, min(3, planning_passes))
        try:
            plan_tokens = int(opts.get("plan_max_new_tokens", opts.get("planning_max_tokens", getattr(settings, "assistant_plan_max_tokens", 768) if settings else 768)) or 768)
        except Exception:
            plan_tokens = 768
        plan_tokens = max(128, min(4096, plan_tokens))
        try:
            min_chat_tokens = int(opts.get("min_chat_max_new_tokens", getattr(settings, "assistant_min_chat_tokens", 1024) if settings else 1024) or 1024)
        except Exception:
            min_chat_tokens = 1024
        try:
            deep_chat_tokens = int(opts.get("deep_chat_max_new_tokens", getattr(settings, "assistant_deep_chat_tokens", 4096) if settings else 4096) or 4096)
        except Exception:
            deep_chat_tokens = 4096
        try:
            reflection_rounds = int(opts.get("max_auto_reflection_rounds", getattr(settings, "assistant_max_auto_reflection_rounds", 1) if settings else 1) or 0)
        except Exception:
            reflection_rounds = 1
        return {
            "thinking_mode": mode,
            "reasoning_effort": effort,
            "show_visible_plan": bool(show_plan),
            "show_live_chain_of_thought": bool(show_trace),
            "show_live_reasoning_trace": bool(show_trace),
            "planning_passes": planning_passes,
            "plan_max_new_tokens": plan_tokens,
            "min_chat_max_new_tokens": max(256, min(8192, min_chat_tokens)),
            "deep_chat_max_new_tokens": max(1024, min(16384, deep_chat_tokens)),
            "max_auto_reflection_rounds": max(0, min(3, reflection_rounds)),
        }

    def _apply_chat_reasoning_runtime(self, runtime: dict[str, Any], reasoning: dict[str, Any]) -> None:
        mode = str(reasoning.get("thinking_mode") or "balanced")
        target = int(reasoning.get("min_chat_max_new_tokens") or 1024)
        if mode == "deep":
            target = int(reasoning.get("deep_chat_max_new_tokens") or 4096)
        elif mode == "fast":
            target = max(512, target // 2)
        try:
            runtime["max_new_tokens"] = max(int(runtime.get("max_new_tokens") or 0), target)
        except Exception:
            runtime["max_new_tokens"] = target
        effort = str(reasoning.get("reasoning_effort") or "medium")
        if effort != "none":
            # Some cloud adapters/providers understand these fields; local adapters
            # simply ignore them while still benefiting from plan-before-answer prompts.
            runtime.setdefault("reasoning_effort", effort)
            runtime.setdefault("reasoning", {"effort": effort})


    def _agent_tool_contract_for_chat(self) -> str:
        """Prompt contract that tells local models how this app executes tools.

        The model itself never receives a raw Python object.  It emits JSON/tool
        calls; the app shows them to the user and then executes approved actions
        through the local Agent Tools runtime.  This wording is intentionally
        direct because many small local models otherwise default to "I cannot run
        commands" even though the host application can.
        """
        return """
LOCAL ACTION / TOOL-CALL DECISION CONTRACT FOR THIS APPLICATION:
- You are inside Data Curation Tool. The application can execute approved local actions through Agent Tools, but tool availability does NOT mean every prompt needs a tool.
- Before answering, classify the user request into exactly one response mode internally and then respond accordingly:
  1. DIRECT_ANSWER: no tool is needed. Answer normally. Do not emit tool_calls.
  2. APP_GUI_ACTION: the task is best handled by this app/GUI/API rather than the OS terminal. Explain the in-app action, or emit an app_gui_action tool call if it should be routed through the app after approval.
  3. TOOL_COA: the task requires filesystem/terminal/browser/Python/model-subtask access. Emit one or more concrete tool_calls/COA options for approval.
  4. MIXED: give a concise answer and then propose only the tool calls still needed.
- Use DIRECT_ANSWER for ordinary conversation, explanations, reasoning over already visible context, tag discussion that does not require inspection, and user preference/help questions.
- Use APP_GUI_ACTION for tasks such as switching tabs, refreshing app state, using the Tag Editor/Compare/Jobs/Models UI, applying app-side tag/caption operations, or asking the user to review app controls.
- Use TOOL_COA only when you truly need information or side effects outside the already-provided app context, such as reading a file, listing a path, running Python/PowerShell, opening a website/browser, or asking another model to run a subtask.
- You must not claim that tools are unavailable merely because you are an AI model or sandboxed. If tools are needed, output a structured COA/tool-call plan; the app executes it only after approval.
- If no tool is needed, do NOT output empty JSON, fake COAs, or a tool-call preamble. Just answer the user.
- If the user explicitly approves or asks to run a prior COA, return the concrete JSON tool_calls for that COA; do not re-explain only.
- Use only these tools when needed: run_shell_command, run_python_script, list_path, read_file, write_file, fetch_url_text, open_browser, app_gui_action, inspect_model_resources, run_model_chat, queue_model_load, queue_model_inference, queue_model_unload, wait_for_jobs.
- Each executable tool call/step must include a clear note, risk level, and requires_approval=true.
- For Windows local work, prefer run_shell_command with arguments.shell="powershell" and write ONLY the PowerShell script/command itself. Do NOT wrap it inside another powershell.exe -Command when shell="powershell".
- For multi-line Python, use run_python_script with a complete script and include requirements=[...] if pip packages are needed.
- If you need a specialized chat model, first use inspect_model_resources, then propose run_model_chat with model_name, prompt, GPU IDs, dtype, quantization, and sharding hints. If you need a classifier/tagger/detector/captioner, propose queue_model_load and queue_model_inference, then wait_for_jobs before using the results. Use queue_model_unload when cleanup is part of the plan.
- Do not say a tool has already run until the app relays a real job result back to you.
- After a tool result is relayed, summarize stdout/stderr/results, decide if the task is complete, and propose the next approved action only if more work is actually needed.
Example TOOL_COA:
{
  "summary": "Inspect the project folder and report what files are relevant.",
  "tool_calls": [
    {"tool":"run_shell_command","arguments":{"shell":"powershell","command":"Get-ChildItem -Force | Select-Object Name,Length,LastWriteTime","cwd":"C:\\\\path\\\\to\\\\project"},"risk":"low","note":"List files in the selected project folder.","requires_approval":true}
  ]
}
Example APP_GUI_ACTION:
{
  "summary": "Open the Jobs tab so the user can inspect a failed download.",
  "tool_calls": [
    {"tool":"app_gui_action","arguments":{"action":"open_tab","target":"Jobs","note":"Show the job details/logs panel."},"risk":"low","note":"Route this to the app UI instead of using terminal commands.","requires_approval":true}
  ]
}
""".strip()

    def _prompt_with_agent_tool_contract(self, user_prompt: str, context: dict[str, Any]) -> str:
        return (
            self._agent_tool_contract_for_chat()
            + "\n\nCURRENT APP CONTEXT EXCERPT:\n"
            + self._safe_context_excerpt(context, 6000)
            + "\n\nUSER REQUEST:\n"
            + str(user_prompt or "")
        )


    def _agent_tool_decision_metadata(self, *, enabled: bool, response_text: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Summarize whether the assistant response actually chose to use tools.

        The model is instructed to decide DIRECT_ANSWER vs APP_GUI_ACTION vs
        TOOL_COA/MIXED.  This lightweight metadata lets the UI/debug logs make
        that distinction visible without forcing a tool run for normal chat.
        """
        opts = dict(options or {})
        text = str(response_text or "")
        low = text.lower()
        has_tool_json = bool(re.search(r'"(?:tool_calls|actions|steps)"\s*:', text, re.I))
        has_external_tool = any(token in low for token in ("run_shell_command", "run_python_script", "read_file", "write_file", "list_path", "fetch_url_text", "open_browser", "inspect_model_resources", "run_model_chat"))
        has_gui_tool = "app_gui_action" in low or "gui_action" in low or "app_action" in low
        if not enabled:
            mode = "disabled"
        elif has_external_tool:
            mode = "tool_coa"
        elif has_gui_tool:
            mode = "app_gui_action"
        elif has_tool_json:
            mode = "mixed_or_unknown_tool_plan"
        else:
            mode = "direct_answer"
        return {
            "enabled": bool(enabled),
            "mode": mode,
            "tool_calls_present": bool(has_tool_json or has_external_tool or has_gui_tool),
            "external_tools_present": bool(has_external_tool),
            "app_gui_action_present": bool(has_gui_tool),
            "model_decides_when_to_use_tools": bool(opts.get("agent_tools_model_decides_when_to_use_tools", True)),
            "plain_chat_allowed": bool(opts.get("agent_tools_allow_plain_chat_without_tools", True)),
            "note": "Tool visibility is available, but normal chat/direct answers remain valid when no tool is needed.",
        }


    def _estimate_text_tokens(self, value: Any) -> int:
        """Fast approximate token counter for UI/context pressure controls.

        We avoid importing tokenizers here because this path runs for every chat
        request and must work for many local/API model families.  A 4 chars/token
        approximation is intentionally conservative enough for progress warnings.
        """
        try:
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            text = str(value or "")
        # Count long whitespace separated IDs/tags as at least one token each.
        char_est = int(math.ceil(len(text) / 4.0))
        word_est = int(math.ceil(len(re.findall(r"\S+", text)) * 1.15))
        return max(char_est, word_est, 1 if text else 0)

    def _model_context_limit(self, model_name: str, options: dict[str, Any] | None = None) -> int:
        opts = dict(options or {})
        for key in ("context_length", "context_window", "max_context_tokens"):
            try:
                val = int(opts.get(key) or 0)
                if val > 0:
                    return max(1024, val)
            except Exception:
                pass
        try:
            record = self.registry.get_record(model_name)
            if getattr(record, "context_length", None):
                return max(1024, int(record.context_length))
        except Exception:
            pass
        # Reasonable fallback for unknown local models.  Users still see this as
        # estimated context pressure rather than a hard provider token count.
        return 8192

    def _context_budget_payload(self, *, model_name: str, prompt: str, context: dict[str, Any], response_text: str = "", options: dict[str, Any] | None = None, condensed: bool = False, condense_reason: str = "") -> dict[str, Any]:
        limit = self._model_context_limit(model_name, options)
        input_tokens = self._estimate_text_tokens({"prompt": prompt, "context": context})
        output_tokens = self._estimate_text_tokens(response_text)
        total = input_tokens + output_tokens
        pct = min(1.0, total / max(1, limit))
        threshold = float((options or {}).get("auto_condense_context_threshold") or 0.72)
        return {
            "estimated": True,
            "model_name": model_name,
            "context_limit_tokens": limit,
            "input_tokens_estimate": input_tokens,
            "output_tokens_estimate": output_tokens,
            "tokens_used_estimate": total,
            "percent_used": round(pct, 4),
            "warning": pct >= 0.82,
            "critical": pct >= 0.94,
            "auto_condensed": bool(condensed),
            "auto_condense_enabled": (options or {}).get("auto_condense_context", True) is not False,
            "auto_condense_threshold": threshold,
            "auto_condense_pending": pct >= threshold,
            "condense_reason": condense_reason,
            "note": "Token counts are fast estimates for live UI pressure and automatic condensation; provider tokenizers may differ.",
        }

    def _maybe_precondense_chat_context(self, conversation_id: int, context: dict[str, Any], history: list[dict[str, Any]], state: dict[str, Any], request: ModelChatRequest, options: dict[str, Any]) -> tuple[dict[str, Any], str, bool, str]:
        """Condense before a request when the live context is approaching limit.

        This avoids the failure mode where the chat becomes unusable after only a
        few large messages/images/files.  The condensed summary is hard capped so
        it cannot get into an infinite "summary too large to summarize" loop.
        """
        budget = self._context_budget_payload(model_name=request.model_name, prompt=request.prompt or "", context=context, options=options)
        if options.get("auto_condense_context") is False:
            return context, str(context.get("conversation_memory_summary") or state.get("memory_summary") or "").strip(), False, ""
        threshold = float(options.get("auto_condense_context_threshold") or 0.72)
        condensed = False
        reason = ""
        memory_summary = str(context.get("conversation_memory_summary") or state.get("memory_summary") or "").strip()
        if budget["percent_used"] >= threshold or bool(options.get("force_memory_condense")):
            condensed = True
            reason = f"estimated context pressure {budget['tokens_used_estimate']}/{budget['context_limit_tokens']} tokens ({budget['percent_used']:.0%})"
            memory_summary = self._conversation_memory_summary(conversation_id, history, state, force=True)
            # Hard cap the memory summary.  If a prior summary is too large, keep
            # the newest/task-relevant tail instead of feeding an oversized block.
            max_memory_chars = max(3000, min(12000, int((budget["context_limit_tokens"] * 4) * 0.22)))
            if len(memory_summary) > max_memory_chars:
                memory_summary = "Condensed conversation memory (trimmed to fit context):\n" + memory_summary[-max_memory_chars:]
            context["conversation_memory_summary"] = memory_summary
            # Keep only a compact recent window once memory is present.
            compact_recent = self._compact_history_for_context(history[-10:]) if history else []
            context["history"] = compact_recent
            self._merge_conversation_state(conversation_id, {"memory_summary": memory_summary, "memory_updated_at": self._now(), "memory_threshold_messages": max(12, int(state.get("memory_threshold_messages") or 24))})
        return context, memory_summary, condensed, reason

    def _visible_planning_prompt(self, user_prompt: str, context: dict[str, Any], reasoning: dict[str, Any], pass_index: int = 1) -> str:
        return (
            "Create a detailed user-visible reasoning trace and practical plan for the next answer. "
            "This is the explicit, user-visible trace the app is allowed to show; do not claim to expose provider/private hidden reasoning. "
            "Do not solve the full task yet. Return only the trace/plan that the UI can show separately from the final answer.\n"
            "Use this format exactly where possible:\n"
            "VISIBLE_CHAIN_OF_THOUGHT:\n"
            "- Goal interpretation: ...\n"
            "- Evidence/context checked: ...\n"
            "- Tool/model actions considered: ...\n"
            "- Risks/uncertainties: ...\n"
            "- Next action: ...\n"
            "VISIBLE_PLAN:\n"
            "- Goal: ...\n"
            "- Context to use: ...\n"
            "- Steps: ...\n"
            "- Risks/uncertainties: ...\n"
            "- Next action: ...\n"
            f"Thinking mode: {reasoning.get('thinking_mode')} / effort: {reasoning.get('reasoning_effort')} / pass: {pass_index}.\n\n"
            f"User request:\n{user_prompt}\n\n"
            f"Available context summary:\n{self._safe_context_excerpt(context, 5000)}"
        )

    def _final_prompt_with_visible_plan(self, user_prompt: str, visible_plan: str) -> str:
        if not visible_plan.strip():
            return user_prompt
        return (
            "Use the following visible reasoning trace and plan/action-notes to structure your answer. "
            "Do not output private hidden reasoning; give the final user-facing response.\n\n"
            f"Visible plan/action-notes already shown in the UI:\n{visible_plan.strip()}\n\n"
            f"User request:\n{user_prompt}"
        )

    def _safe_context_excerpt(self, context: dict[str, Any], limit: int = 6000) -> str:
        try:
            text = json.dumps(context or {}, ensure_ascii=False, default=str, indent=2)
        except Exception:
            text = str(context or {})
        return text[:max(500, int(limit or 6000))]

    @staticmethod
    def _clean_visible_plan(text: str) -> str:
        raw = str(text or "").strip()
        if not raw:
            return ""
        raw = re.sub(r"^```(?:json|text|markdown)?\s*", "", raw, flags=re.I).strip()
        raw = re.sub(r"```$", "", raw).strip()
        # Prefer a VISIBLE_PLAN section, but keep normal text when the model is
        # small and ignores the requested heading.
        m = re.search(r"VISIBLE_PLAN\s*:\s*(.*)", raw, flags=re.I | re.S)
        if m:
            raw = m.group(1).strip()
        # Remove common hidden-reasoning labels if a model emits them.
        raw = re.sub(r"(?im)^\s*(chain[- ]of[- ]thought|hidden reasoning|private reasoning)\s*:\s*", "", raw)
        return raw[:8000]

    @staticmethod
    def _clean_visible_reasoning_trace(text: str) -> str:
        raw = str(text or "").strip()
        if not raw:
            return ""
        raw = re.sub(r"^```(?:json|text|markdown)?\s*", "", raw, flags=re.I).strip()
        raw = re.sub(r"```$", "", raw).strip()
        m = re.search(r"VISIBLE_CHAIN_OF_THOUGHT\s*:\s*(.*?)(?:\n\s*VISIBLE_PLAN\s*:|\Z)", raw, flags=re.I | re.S)
        if m:
            raw = m.group(1).strip()
        else:
            m = re.search(r"VISIBLE_REASONING_TRACE\s*:\s*(.*?)(?:\n\s*VISIBLE_PLAN\s*:|\Z)", raw, flags=re.I | re.S)
            if m:
                raw = m.group(1).strip()
        raw = re.sub(r"(?im)^\s*(hidden reasoning|private reasoning)\s*:\s*", "", raw)
        return raw[:12000]

    @staticmethod
    def _action_notes_from_plan(plan: str) -> list[str]:
        notes: list[str] = []
        for line in str(plan or "").splitlines():
            clean = re.sub(r"^\s*[-*0-9.)]+\s*", "", line).strip()
            if clean and len(clean) > 3:
                notes.append(clean)
            if len(notes) >= 12:
                break
        return notes

    def _generate_visible_plan(self, request: ModelChatRequest, prompt: str, context: dict[str, Any], runtime: dict[str, Any], reasoning: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
        passes = int(reasoning.get("planning_passes") or 0)
        if not reasoning.get("show_visible_plan") or passes <= 0:
            return "", "", []
        plan_runtime = dict(runtime)
        plan_runtime["max_new_tokens"] = int(reasoning.get("plan_max_new_tokens") or 768)
        plan_runtime.setdefault("temperature", min(float(plan_runtime.get("temperature", 0.2) or 0.2), 0.4))
        visible_plan = ""
        visible_reasoning_trace = ""
        pass_rows: list[dict[str, Any]] = []
        for pass_idx in range(1, passes + 1):
            plan_context = dict(context)
            if visible_plan:
                plan_context["previous_visible_plan"] = visible_plan
            plan_prompt = self._visible_planning_prompt(prompt, plan_context, reasoning, pass_idx)
            plan_response = self._registry_chat_with_vram_guard(request.model_name, plan_prompt, context=plan_context, device=request.device, options=reasoning, **plan_runtime)
            raw_plan_text = plan_response.get("response") or ""
            cleaned = self._clean_visible_plan(raw_plan_text)
            cleaned_trace = self._clean_visible_reasoning_trace(raw_plan_text)
            if cleaned:
                visible_plan = cleaned
            if cleaned_trace:
                visible_reasoning_trace = cleaned_trace
            elif cleaned and not visible_reasoning_trace:
                visible_reasoning_trace = cleaned
            pass_rows.append({"pass": pass_idx, "chars": len(cleaned), "trace_chars": len(cleaned_trace), "used": bool(cleaned or cleaned_trace)})
        return visible_plan, visible_reasoning_trace, pass_rows

    def chat(self, request: ModelChatRequest) -> dict[str, Any]:
        resolved_model = self.resolve_assistant_model_name(request.model_name, purpose="assistant")
        if resolved_model != request.model_name:
            request = request.model_copy(update={"model_name": resolved_model})
        options = dict(request.options or {})
        options.setdefault("auto_condense_context", True)
        options.setdefault("auto_condense_context_threshold", 0.72)
        options.setdefault("show_live_action_notes", True)
        options.setdefault("show_live_chain_of_thought", True)
        options.setdefault("show_live_reasoning_trace", True)
        options.setdefault("show_visible_plan", True)
        context = self._build_chat_context(request)
        conversation_id = self._ensure_conversation(request, context)
        # Compact stale payloads before reloading history.  This protects
        # overnight VLM/LLM sessions from accumulating media/model context JSON
        # into system RAM while preserving the visible chat transcript.
        self._prune_conversation_payloads(conversation_id, keep_recent=int(options.get("recent_message_window") or 32) + 4)
        full_history = self._conversation_history(conversation_id)
        conversation_state = self._conversation_state(conversation_id)
        context_reset_message_id = int(conversation_state.get("context_reset_message_id") or 0)
        stored_history = [m for m in full_history if int(m.get("id") or 0) > context_reset_message_id]
        if context_reset_message_id:
            context["context_reset_message_id"] = context_reset_message_id
            context["context_reset_note"] = "Earlier visible transcript messages were intentionally excluded after the user cleared model memory/context."
        memory_summary = self._conversation_memory_summary(conversation_id, stored_history, conversation_state)
        if memory_summary:
            context["conversation_memory_summary"] = memory_summary
        context["conversation_state"] = self._compact_conversation_state_for_context(conversation_state)
        # Preserve caller-provided in-memory history, but prefer persisted history
        # when a conversation has already been resumed from disk.  Keep the live
        # window compact and rely on the cached memory summary for older turns.
        recent_window = int(options.get("recent_message_window") or 32)
        if stored_history:
            context["history"] = self._compact_history_for_context(stored_history[-max(8, recent_window):])
        elif request.history:
            context["history"] = self._compact_history_for_context(request.history[-max(8, recent_window):])

        context, memory_summary, precondensed_context, precondense_reason = self._maybe_precondense_chat_context(
            conversation_id, context, stored_history, conversation_state, request, options
        )

        visible_user_prompt = request.prompt or ""
        prompt_for_model = visible_user_prompt
        continue_last_output = bool(options.get("continue_last_output") or options.get("finish_previous_output") or options.get("finish_last_output"))
        if continue_last_output:
            last_assistant = self._last_assistant_message(stored_history)
            prompt_for_model = self._continuation_prompt(visible_user_prompt, last_assistant, stored_history, memory_summary)
            context["continue_last_output"] = True
            if last_assistant:
                context["last_assistant_response_tail"] = str(last_assistant.get("content") or "")[-2200:]

        agent_tool_chat = bool(options.get("agent_tools_chat") or options.get("agent_tools") or options.get("enable_agent_tools") or options.get("agent_tools_execute_coa_enabled"))
        if agent_tool_chat and not continue_last_output:
            context["agent_tools_available"] = True
            context["agent_tools_model_decides_when_to_use_tools"] = bool(getattr(self.settings, "agent_tools_model_decides_when_to_use_tools", True))
            context["agent_tools_allow_plain_chat_without_tools"] = bool(getattr(self.settings, "agent_tools_allow_plain_chat_without_tools", True))
            context["agent_tools_app_gui_action_routing"] = bool(getattr(self.settings, "agent_tools_app_gui_action_routing", True))
            context["agent_tools_execution_contract"] = "Model first decides direct answer vs app GUI action vs external tool-call COA; app executes approved tool-call actions as jobs."
            options.setdefault("agent_tools_model_decides_when_to_use_tools", bool(getattr(self.settings, "agent_tools_model_decides_when_to_use_tools", True)))
            options.setdefault("agent_tools_allow_plain_chat_without_tools", bool(getattr(self.settings, "agent_tools_allow_plain_chat_without_tools", True)))
            prompt_for_model = self._prompt_with_agent_tool_contract(prompt_for_model, context)

        if options.get("include_lora_rule_context", True) is not False:
            prompt_for_model = self._append_lora_rules_to_prompt(prompt_for_model, options)

        runtime = self._runtime_options(request)
        reasoning = self._chat_reasoning_options(options)
        reasoning_enabled = bool(options.get("chat_assistant") or options.get("code_assistant") or options.get("agent_assistant") or options.get("assistant_reasoning") or options.get("think_longer"))
        if reasoning_enabled:
            self._apply_chat_reasoning_runtime(runtime, reasoning)
        # Prefer higher chat token budgets for long-form conversation. This is a
        # floor only; explicit larger Settings/API values still win.
        if options.get("chat_assistant") or options.get("code_assistant") or options.get("continue_last_output") or options.get("finish_previous_output"):
            try:
                runtime["max_new_tokens"] = max(int(runtime.get("max_new_tokens") or 0), int(options.get("min_chat_max_new_tokens") or (2048 if options.get("code_assistant") else 1024)))
            except Exception:
                runtime["max_new_tokens"] = 2048 if options.get("code_assistant") else 1024
        record = self.registry.get_record(request.model_name)
        self._inject_provider_token(runtime, record.provider, request)
        if self.lifecycle.is_active(request.model_name, "download"):
            raise RuntimeError(f"{request.model_name} is still downloading. Wait for download to finish before chatting with it.")
        if self.lifecycle.is_active(request.model_name, "load") and not self.registry.is_loaded(request.model_name):
            raise RuntimeError(f"{request.model_name} is still loading into memory. Wait for loading to finish before chatting with it.")
        if not self.registry.is_loaded(request.model_name):
            self._load_model_from_request(request, progress=None, job_id=None)
        user_message_id = self._append_chat_message(conversation_id, "user", visible_user_prompt, request.model_name, context, {})
        visible_plan = ""
        visible_reasoning_trace = ""
        planning_passes: list[dict[str, Any]] = []
        if reasoning_enabled and reasoning.get("show_visible_plan"):
            try:
                visible_plan, visible_reasoning_trace, planning_passes = self._generate_visible_plan(request, prompt_for_model, context, runtime, reasoning)
                if visible_plan or visible_reasoning_trace:
                    context["visible_plan"] = visible_plan
                    context["visible_reasoning_trace"] = visible_reasoning_trace or visible_plan
                    context["visible_chain_of_thought"] = visible_reasoning_trace or visible_plan
                    context["visible_action_notes"] = self._action_notes_from_plan(visible_plan or visible_reasoning_trace)
                    prompt_for_model = self._final_prompt_with_visible_plan(prompt_for_model, visible_plan or visible_reasoning_trace)
            except Exception as exc:
                planning_passes.append({"error": str(exc)})
        response = self._registry_chat_with_vram_guard(
            request.model_name,
            prompt_for_model,
            context=context,
            device=request.device,
            options=options,
            **runtime,
        )

        response_text = str(response.get("response") or "")
        continuation_rounds: list[dict[str, Any]] = []
        auto_continue = options.get("auto_continue_incomplete")
        if auto_continue is None:
            auto_continue = bool(options.get("chat_assistant") or options.get("code_assistant") or continue_last_output)
        max_rounds = max(0, min(3, int(options.get("max_continuation_rounds") or (1 if auto_continue else 0))))
        for round_idx in range(max_rounds):
            if not self._response_looks_incomplete(response_text, runtime):
                break
            cont_context = dict(context)
            cont_context["incomplete_response_so_far"] = response_text[-5000:]
            cont_prompt = self._continue_incomplete_response_prompt(visible_user_prompt, response_text)
            try:
                cont = self._registry_chat_with_vram_guard(
                    request.model_name,
                    cont_prompt,
                    context=cont_context,
                    device=request.device,
                    options=options,
                    **runtime,
                )
            except Exception as exc:
                continuation_rounds.append({"round": round_idx + 1, "error": str(exc)})
                break
            cont_text = str(cont.get("response") or "")
            merged = self._merge_continuation_text(response_text, cont_text)
            continuation_rounds.append({"round": round_idx + 1, "added_chars": max(0, len(merged) - len(response_text)), "raw_chars": len(cont_text)})
            if merged == response_text:
                break
            response_text = merged
            for tag in cont.get("suggested_tags") or []:
                response.setdefault("suggested_tags", [])
                if tag not in response["suggested_tags"]:
                    response["suggested_tags"].append(tag)
            if not response.get("suggested_caption") and cont.get("suggested_caption"):
                response["suggested_caption"] = cont.get("suggested_caption")

        suggested_tags = response.get("suggested_tags") or _extract_tags(response_text)
        suggested_caption = response.get("suggested_caption") or _extract_caption(response_text)
        applied: dict[str, Any] = {"tags": 0, "captions": 0, "media_ids": [], "tag_edits": None}
        target_ids = request.media_ids if request.use_selected_media else []
        if target_ids and bool(options.get("assistant_apply_tag_edits")):
            edit_result = self._apply_assistant_tag_edit_directives(media_ids=target_ids, response_text=response_text, model_name=request.model_name, options=options)
            applied["tag_edits"] = edit_result
            if edit_result.get("changed"):
                applied["tags"] += int(edit_result.get("changed") or 0)
                applied["media_ids"].extend([mid for mid in edit_result.get("media_ids") or [] if mid not in applied["media_ids"]])
        elif request.apply_suggested_tags and suggested_tags and target_ids:
            for media_id in target_ids:
                current = self.tags.get_tags(media_id)
                merged = list(current)
                for tag in suggested_tags:
                    if tag not in merged:
                        merged.append(tag)
                self.tags.set_tags(media_id, merged, source=request.model_name, save_sidecar=True, profile_key=str(options.get("tag_profile") or "e621"), order_strategy="retain")
                applied["tags"] += len(suggested_tags)
                applied["media_ids"].append(media_id)
        if request.apply_suggested_caption and suggested_caption and target_ids:
            for media_id in target_ids:
                self.db.upsert_caption(media_id, suggested_caption, source=request.model_name)
                applied["captions"] += 1
                if media_id not in applied["media_ids"]:
                    applied["media_ids"].append(media_id)
        context_budget = self._context_budget_payload(
            model_name=request.model_name,
            prompt=prompt_for_model,
            context=context,
            response_text=response_text,
            options=options,
            condensed=bool(precondensed_context),
            condense_reason=precondense_reason,
        )
        response_payload = {
            "model_name": request.model_name,
            "response": response_text,
            "suggested_tags": suggested_tags,
            "suggested_caption": suggested_caption,
            "applied": applied,
            "visible_plan": visible_plan or None,
            "visible_reasoning_trace": (visible_reasoning_trace or visible_plan) or None,
            "visible_chain_of_thought": (visible_reasoning_trace or visible_plan) or None,
            "action_notes": self._action_notes_from_plan(visible_plan or visible_reasoning_trace),
            "reasoning": {
                **reasoning,
                "enabled": bool(reasoning_enabled),
                "planning_passes": planning_passes,
                "final_max_new_tokens": runtime.get("max_new_tokens"),
                "hidden_chain_of_thought_exposed": False,
                "live_action_notes_enabled": bool(options.get("show_live_action_notes", True)),
                "live_chain_of_thought_enabled": bool(options.get("show_live_chain_of_thought", True)),
                "live_reasoning_trace_enabled": bool(options.get("show_live_reasoning_trace", True)),
                "visible_reasoning_trace": (visible_reasoning_trace or visible_plan) or None,
                "auto_condense_context_enabled": options.get("auto_condense_context", True) is not False,
                "auto_condense_context_threshold": float(options.get("auto_condense_context_threshold") or 0.72),
                "precondensed_context": bool(precondensed_context),
                "precondense_reason": precondense_reason,
                "note": "Visible plan/action-notes and chain-of-thought-style reasoning trace are generated as user-facing artifacts; provider/private hidden reasoning is not extracted.",
            },
            "continuation_rounds": continuation_rounds,
            "finish_requested": continue_last_output,
            "agent_tools_chat": bool(agent_tool_chat),
            "agent_tool_decision": self._agent_tool_decision_metadata(enabled=bool(agent_tool_chat), response_text=response_text, options=options),
            "looks_incomplete": self._response_looks_incomplete(response_text, runtime),
            "context_budget": context_budget,
            "context_reset_message_id": context_reset_message_id,
            "vram_memory_policy": {
                "cleanup_after_inference": self._settings_bool("model_vram_cleanup_after_inference", True),
                "auto_cpu_offload_enabled": self._settings_bool("model_vram_auto_cpu_offload_enabled", False),
                "auto_cpu_offload_policy": self._settings_str("model_vram_auto_cpu_offload_policy", "on_pressure"),
                "disable_generation_cache_on_pressure": self._settings_bool("model_vram_disable_generation_cache_on_pressure", True),
                "cleanup_events": context.get("runtime_memory_cleanup") or [],
            },
        }
        assistant_message_id = self._append_chat_message(conversation_id, "assistant", response_payload["response"], request.model_name, context, response_payload)
        final_history = self._conversation_history(conversation_id)
        current_state_for_memory = self._conversation_state(conversation_id)
        final_reset_id = int(current_state_for_memory.get("context_reset_message_id") or context_reset_message_id or 0)
        final_context_history = [m for m in final_history if int(m.get("id") or 0) > final_reset_id]
        force_memory = (
            len(final_context_history) > int(conversation_state.get("memory_threshold_messages") or 36)
            or bool(options.get("force_memory_condense"))
            or float((context_budget or {}).get("percent_used") or 0.0) >= float(options.get("auto_condense_context_threshold") or 0.72)
        )
        final_memory = self._conversation_memory_summary(conversation_id, final_context_history, current_state_for_memory, force=force_memory)
        # Final hard cap keeps memory compact enough that condensation cannot
        # feed an oversized summary back into the next request.
        if final_memory and len(final_memory) > 9000:
            final_memory = "Condensed conversation memory (trimmed after response):\n" + final_memory[-9000:]
        self._merge_conversation_state(conversation_id, {
            "last_model_name": request.model_name,
            "last_media_ids": request.media_ids,
            "last_external_paths": request.external_paths,
            "last_metadata_field_paths": request.metadata_field_paths,
            "last_response_looks_incomplete": response_payload["looks_incomplete"],
            "last_response_char_count": len(response_text),
            "memory_summary": final_memory,
            "memory_updated_at": self._now() if final_memory else None,
            "last_context_budget": context_budget,
        })
        prune_result = self._prune_conversation_payloads(conversation_id, keep_recent=max(12, int(options.get("recent_message_window") or 32)))
        ram_guard = self._system_ram_guard(label="after_chat_response", model_name=request.model_name)
        self.db.execute("UPDATE chat_conversations SET model_name=?, dataset_id=?, updated_at=? WHERE id=?", (request.model_name, request.dataset_id, self._now(), conversation_id))
        # Return a compact recent history to the browser.  Full visible history is
        # still persisted and can be reloaded through the conversation endpoint;
        # not echoing every old context/response JSON prevents long browser/worker
        # sessions from accumulating RAM.
        returned_history = final_history[-max(16, int(options.get("recent_message_window") or 32)):]
        return {**response_payload, "conversation_id": conversation_id, "user_message_id": user_message_id, "assistant_message_id": assistant_message_id, "history": returned_history, "history_truncated": len(final_history) > len(returned_history), "memory_summary": final_memory, "conversation_payload_prune": prune_result, "system_ram_guard": ram_guard}

    def _ensure_conversation(self, request: ModelChatRequest, context: dict[str, Any]) -> int:
        now = self._now()
        if request.fork_from_message_id:
            return self.fork_conversation(int(request.fork_from_message_id), title=request.conversation_title or None).get("conversation", {}).get("id")
        if request.conversation_id:
            row = self.db.query_one("SELECT id FROM chat_conversations WHERE id=? AND archived=0", (int(request.conversation_id),))
            if row:
                return int(row["id"])
        title = (request.conversation_title or request.prompt[:70] or "Dataset conversation").strip()
        state = {"dataset_id": request.dataset_id, "media_ids": request.media_ids, "external_paths": request.external_paths, "metadata_field_paths": request.metadata_field_paths}
        new_id = self.db.execute(
            "INSERT INTO chat_conversations(title, model_name, dataset_id, state_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, request.model_name, request.dataset_id, json.dumps(state, ensure_ascii=False, default=str), now, now),
        )
        return int(new_id)

    def _json_storage_limit(self, name: str, default: int) -> int:
        try:
            return max(8000, int(getattr(self.settings, name, default) if self.settings is not None else default))
        except Exception:
            return default

    def _compact_json_for_storage(self, value: Any, *, limit: int, label: str = "payload") -> Any:
        """Bound chat context/response JSON stored in SQLite.

        Long local-model sessions can otherwise retain full context payloads for
        every message.  That is useful for debugging but it creates a real RAM/DB
        growth vector when a VLM chat keeps appending large media/prediction
        objects overnight.  The visible message text is preserved; only bulky
        structured payloads are summarized.
        """
        try:
            text = json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)
        except Exception:
            text = json.dumps({"value": str(value)[:limit]}, ensure_ascii=False)
        if len(text) <= max(1000, int(limit)):
            try:
                return json.loads(text)
            except Exception:
                return value
        head = max(2000, int(limit * 0.40))
        tail = max(2000, int(limit * 0.55))
        return {
            "_dct_compacted": True,
            "label": label,
            "original_chars_estimate": len(text),
            "head": text[:head],
            "tail": text[-tail:],
            "note": "Structured chat payload was compacted to prevent long-running assistant memory growth; visible chat content remains intact.",
        }

    def _compact_context_for_storage(self, context: dict[str, Any]) -> dict[str, Any]:
        return self._compact_json_for_storage(context or {}, limit=self._json_storage_limit("model_chat_storage_max_context_chars", 60000), label="chat_context")

    def _compact_response_for_storage(self, response: dict[str, Any]) -> dict[str, Any]:
        return self._compact_json_for_storage(response or {}, limit=self._json_storage_limit("model_chat_storage_max_response_chars", 90000), label="chat_response")

    def _append_chat_message(self, conversation_id: int, role: str, content: str, model_name: str, context: dict[str, Any], response: dict[str, Any]) -> int:
        now = self._now()
        safe_context = self._compact_context_for_storage(context or {})
        safe_response = self._compact_response_for_storage(response or {})
        new_msg_id = self.db.execute(
            "INSERT INTO chat_messages(conversation_id, role, content, model_name, context_json, response_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conversation_id, role, content or "", model_name or "", json.dumps(safe_context, ensure_ascii=False, default=str), json.dumps(safe_response, ensure_ascii=False, default=str), now),
        )
        self.db.execute("UPDATE chat_conversations SET updated_at=? WHERE id=?", (now, conversation_id))
        return int(new_msg_id)

    def _prune_conversation_payloads(self, conversation_id: int, keep_recent: int = 40) -> dict[str, Any]:
        """Compact old chat JSON payloads in-place while preserving visible text.

        This intentionally fetches rows one at a time.  Older releases could
        read every stored context/response JSON blob for a conversation into RAM
        at once, which is exactly the kind of overnight assistant-session growth
        that can exhaust system memory when large media/model contexts are
        attached to many turns.
        """
        try:
            id_rows = self.db.query("SELECT id FROM chat_messages WHERE conversation_id=? ORDER BY id DESC", (int(conversation_id),))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        ids = [int(r["id"]) for r in id_rows]
        old_ids = ids[max(4, int(keep_recent or 40)):]
        compacted = 0
        for row_id in old_ids:
            row = self.db.query_one("SELECT id, context_json, response_json FROM chat_messages WHERE id=?", (row_id,))
            if not row:
                continue
            changed = False
            ctx_raw = row.get("context_json") or "{}"
            rsp_raw = row.get("response_json") or "{}"
            try:
                ctx_obj = json.loads(ctx_raw)
            except Exception:
                ctx_obj = {"raw": str(ctx_raw)[:8000]}
            try:
                rsp_obj = json.loads(rsp_raw)
            except Exception:
                rsp_obj = {"raw": str(rsp_raw)[:8000]}
            if not (isinstance(ctx_obj, dict) and ctx_obj.get("_dct_compacted")):
                new_ctx = self._compact_json_for_storage(ctx_obj, limit=18000, label="old_chat_context")
                changed = changed or (new_ctx != ctx_obj)
                ctx_obj = new_ctx
            if not (isinstance(rsp_obj, dict) and rsp_obj.get("_dct_compacted")):
                new_rsp = self._compact_json_for_storage(rsp_obj, limit=22000, label="old_chat_response")
                changed = changed or (new_rsp != rsp_obj)
                rsp_obj = new_rsp
            if changed:
                self.db.execute("UPDATE chat_messages SET context_json=?, response_json=? WHERE id=?", (json.dumps(ctx_obj, ensure_ascii=False, default=str), json.dumps(rsp_obj, ensure_ascii=False, default=str), int(row["id"])))
                compacted += 1
        if compacted:
            try:
                gc.collect()
            except Exception:
                pass
        return {"ok": True, "conversation_id": int(conversation_id), "compacted_rows": compacted}

    def _conversation_history(self, conversation_id: int, *, max_payload_chars: int = 18000) -> list[dict[str, Any]]:
        # Bound JSON payload materialization at the SQL layer so a long-running
        # chat cannot reload hundreds of huge context/response blobs into RAM.
        limit = max(4000, int(max_payload_chars or 18000))
        rows = self.db.query(
            """
            SELECT id, role, content, model_name, created_at,
                   CASE WHEN context_json IS NOT NULL AND length(context_json) > ? THEN substr(context_json, 1, ?) ELSE context_json END AS context_json,
                   CASE WHEN response_json IS NOT NULL AND length(response_json) > ? THEN substr(response_json, 1, ?) ELSE response_json END AS response_json,
                   CASE WHEN context_json IS NOT NULL AND length(context_json) > ? THEN length(context_json) ELSE 0 END AS context_truncated_from,
                   CASE WHEN response_json IS NOT NULL AND length(response_json) > ? THEN length(response_json) ELSE 0 END AS response_truncated_from
            FROM chat_messages WHERE conversation_id=? ORDER BY id
            """,
            (limit, limit, limit, limit, limit, limit, int(conversation_id)),
        )
        history = []
        for row in rows:
            item = dict(row)
            ctx_trunc = int(item.pop("context_truncated_from") or 0)
            rsp_trunc = int(item.pop("response_truncated_from") or 0)
            ctx_raw = item.pop("context_json") or "{}"
            rsp_raw = item.pop("response_json") or "{}"
            try:
                item["context"] = json.loads(ctx_raw) if not ctx_trunc else {"_dct_truncated_for_ram_guard": True, "original_chars": ctx_trunc, "head": ctx_raw}
            except Exception:
                item["context"] = {"_dct_unparsed_for_ram_guard": True, "head": str(ctx_raw)[:limit]}
            try:
                item["response"] = json.loads(rsp_raw) if not rsp_trunc else {"_dct_truncated_for_ram_guard": True, "original_chars": rsp_trunc, "head": rsp_raw}
            except Exception:
                item["response"] = {"_dct_unparsed_for_ram_guard": True, "head": str(rsp_raw)[:limit]}
            history.append(item)
        return history

    def _conversation_state(self, conversation_id: int) -> dict[str, Any]:
        row = self.db.query_one("SELECT state_json FROM chat_conversations WHERE id=?", (int(conversation_id),))
        if not row:
            return {}
        try:
            data = json.loads(row.get("state_json") or "{}")
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _merge_conversation_state(self, conversation_id: int, patch: dict[str, Any]) -> dict[str, Any]:
        state = self._conversation_state(conversation_id)
        for key, value in (patch or {}).items():
            if value is not None:
                state[key] = value
        state["saved_at"] = self._now()
        self.db.execute("UPDATE chat_conversations SET state_json=?, updated_at=? WHERE id=?", (json.dumps(state, ensure_ascii=False, default=str), state["saved_at"], int(conversation_id)))
        return state

    def save_conversation_state(self, conversation_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.db.query_one("SELECT id FROM chat_conversations WHERE id=? AND archived=0", (int(conversation_id),))
        if not row:
            raise ValueError(f"Conversation not found: {conversation_id}")
        patch = dict(payload or {})
        title = str(patch.pop("title", "") or "").strip()
        if title:
            self.db.execute("UPDATE chat_conversations SET title=?, updated_at=? WHERE id=?", (title[:220], self._now(), int(conversation_id)))
        state = self._merge_conversation_state(int(conversation_id), patch)
        result = self.get_conversation(int(conversation_id))
        result["state"] = state
        return result

    def _compact_history_for_context(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        compact: list[dict[str, Any]] = []
        for msg in history or []:
            compact.append({
                "id": msg.get("id"),
                "role": msg.get("role"),
                "content": str(msg.get("content") or "")[:8000],
                "model_name": msg.get("model_name") or "",
                "created_at": msg.get("created_at") or "",
            })
        return compact

    def _compact_conversation_state_for_context(self, state: dict[str, Any] | None) -> dict[str, Any]:
        state = dict(state or {})
        keep_keys = {
            "scope", "tag_profile", "media_ids", "active_media_id", "active_media_path",
            "active_tags", "active_caption", "project_root", "selected_files", "file_filter",
            "scan_summary", "selected_model", "last_model_name", "last_response_looks_incomplete",
        }
        compact: dict[str, Any] = {}
        for key in keep_keys:
            if key not in state:
                continue
            value = state.get(key)
            if isinstance(value, str):
                compact[key] = value[:5000]
            elif isinstance(value, list):
                compact[key] = value[:300]
            elif isinstance(value, dict):
                try:
                    text = json.dumps(value, ensure_ascii=False, default=str)
                    compact[key] = json.loads(text[:12000]) if len(text) < 12000 else {"summary": text[:12000] + " ..."}
                except Exception:
                    compact[key] = str(value)[:12000]
            else:
                compact[key] = value
        return compact

    def _last_assistant_message(self, history: list[dict[str, Any]]) -> dict[str, Any] | None:
        for msg in reversed(history or []):
            if str(msg.get("role") or "").lower() == "assistant" and str(msg.get("content") or "").strip():
                return msg
        return None

    def _continuation_prompt(self, user_prompt: str, last_assistant: dict[str, Any] | None, history: list[dict[str, Any]], memory_summary: str = "") -> str:
        previous = str((last_assistant or {}).get("content") or "").strip()
        prior_user = ""
        for msg in reversed(history or []):
            if str(msg.get("role") or "").lower() == "user" and str(msg.get("content") or "").strip():
                prior_user = str(msg.get("content") or "").strip()
                break
        tail = previous[-3200:]
        parts = [
            "Continue the previous assistant answer exactly from where it stopped.",
            "Do not repeat or summarize any text that was already shown to the user.",
            "Start with the next missing word, phrase, bullet, code line, or sentence only.",
            "Preserve the same format and level of detail.",
        ]
        if memory_summary:
            parts.append("Cached conversation memory is available in context; use it silently to stay consistent.")
        if prior_user:
            parts.append("Original user request before the interrupted answer:\n" + prior_user[-1800:])
        if user_prompt and user_prompt.strip() and user_prompt.strip().lower() not in {"finish", "continue", "finish previous output"}:
            parts.append("Additional user instruction for this continuation:\n" + user_prompt.strip())
        if tail:
            parts.append("The already-visible answer ended with this tail. Continue after it without repeating it:\n" + tail)
        return "\n\n".join(parts)

    def _continue_incomplete_response_prompt(self, original_prompt: str, response_so_far: str) -> str:
        return (
            "Your previous response appears to have ended mid-output. Continue it exactly where it stopped. "
            "Do not repeat any text already produced. Start with the next missing token/word/sentence only. "
            "Keep the same formatting.\n\n"
            f"Original user request:\n{str(original_prompt or '')[-1800:]}\n\n"
            f"Already-visible assistant response tail:\n{str(response_so_far or '')[-3200:]}"
        )

    def _continue_incomplete_tag_task_prompt(self, original_prompt: str, response_so_far: str, *, operation: str = "preview", current_tags: list[str] | None = None) -> str:
        current = ", ".join(current_tags or [])
        return (
            "The previous response for this tag curation task may be incomplete or missing the completion marker. "
            "If the task was already fully completed, reply exactly [TASK_COMPLETE] and nothing else. "
            "Otherwise, continue the missing tag/task output exactly where it stopped. Do not repeat tags or text already produced. "
            "Keep using parseable tag lines/JSON only. End the final completed response with [TASK_COMPLETE].\n\n"
            f"Operation: {operation}\n"
            f"Current/existing tags, if any:\n{current[-3000:]}\n\n"
            f"Original task prompt:\n{str(original_prompt or '')[-2600:]}\n\n"
            f"Already-produced response tail:\n{str(response_so_far or '')[-3600:]}"
        )

    def _strip_completion_markers(self, text: str) -> str:
        return re.sub(r"\s*\[TASK_COMPLETE\]\s*$", "", str(text or ""), flags=re.I).strip()

    def _has_task_completion_marker(self, text: str) -> bool:
        return bool(re.search(r"\[TASK_COMPLETE\]", str(text or ""), flags=re.I))

    def _response_looks_incomplete(self, text: str, runtime: dict[str, Any] | None = None) -> bool:
        raw = str(text or "").strip()
        if len(raw) < 12:
            return False
        tail = raw[-240:].strip()
        lower_tail = tail.lower()
        if lower_tail.endswith(("[complete]", "<complete>", "done.", "finished.")):
            return False
        if re.search(r"(```|~~~)\s*$", raw):
            return False
        terminal_re = r"[.!?)}\]\"\']$"
        if tail.endswith((".", "!", "?", ")", "]", "}", '"', "'")) and not re.search(r"\b(and|or|but|because|with|for|to|the|a|an|in|on|of|that|which|where|when|while|including|such as|e\.g)\s*$", lower_tail):
            return False
        if re.search(r"[:,;\-–—]\s*$", tail):
            return True
        if re.search(r"\b(and|or|but|because|with|for|to|the|a|an|in|on|of|that|which|where|when|while|including|such as|e\.g)\s*$", lower_tail):
            return True
        # Local models frequently hit max_new_tokens and end without punctuation.
        # Be conservative: require a fairly long answer and no strong terminal mark.
        try:
            max_tokens = int((runtime or {}).get("max_new_tokens") or 0)
        except Exception:
            max_tokens = 0
        if max_tokens and len(raw.split()) >= max(160, int(max_tokens * 0.45)) and not re.search(terminal_re, tail):
            return True
        return len(raw) > 600 and not re.search(terminal_re, tail)

    def _merge_continuation_text(self, base: str, continuation: str) -> str:
        base = str(base or "").rstrip()
        cont = str(continuation or "").strip()
        if not cont:
            return base
        if cont.startswith(base):
            return cont
        # Remove common instruction/prefix echoes from continuation outputs.
        cont = re.sub(r"^(?:assistant:|continue(?:d)?:|continuation:)\s*", "", cont, flags=re.I).strip()
        max_overlap = min(len(base), len(cont), 1200)
        for size in range(max_overlap, 30, -1):
            if base[-size:].lower() == cont[:size].lower():
                return (base + cont[size:]).strip()
        # Word-level overlap catches cases where only the last word or phrase
        # is repeated, e.g. base="... beta gamma" continuation="gamma delta".
        base_words = re.findall(r"\S+", base)
        cont_words = re.findall(r"\S+", cont)
        max_word_overlap = min(len(base_words), len(cont_words), 80)
        for count in range(max_word_overlap, 0, -1):
            if [w.lower() for w in base_words[-count:]] == [w.lower() for w in cont_words[:count]]:
                remainder = " ".join(cont_words[count:])
                return (base + ((" " + remainder) if remainder else "")).strip()
        base_tail = re.sub(r"\s+", " ", base[-500:]).strip().lower()
        cont_head = re.sub(r"\s+", " ", cont[:500]).strip().lower()
        if base_tail and cont_head and cont_head.startswith(base_tail[:120]):
            return base
        sep = "" if base.endswith((" ", "\n", "-", "–", "—", "(")) else " "
        return (base + sep + cont).strip()

    def _conversation_memory_summary(self, conversation_id: int, history: list[dict[str, Any]], state: dict[str, Any] | None = None, *, force: bool = False) -> str:
        state = state or {}
        existing = str(state.get("memory_summary") or "").strip()
        threshold = int(state.get("memory_threshold_messages") or 36)
        if not force and len(history or []) <= threshold:
            return existing
        older = list(history or [])[:-16] if len(history or []) > 16 else list(history or [])
        if not older:
            return existing
        lines: list[str] = []
        if existing:
            lines.append("Prior condensed memory:")
            lines.append(existing[:2500])
        lines.append("Condensed conversation memory:")
        for msg in older[-64:]:
            role = str(msg.get("role") or "message").upper()
            content = re.sub(r"\s+", " ", str(msg.get("content") or "")).strip()
            if not content:
                continue
            lines.append(f"- {role}: {content[:360]}")
        summary = "\n".join(lines).strip()
        if len(summary) > 7000:
            summary = summary[-7000:]
        return summary

    def list_conversations(self, limit: int = 100) -> dict[str, Any]:
        rows = self.db.query("SELECT * FROM chat_conversations WHERE archived=0 ORDER BY updated_at DESC, id DESC LIMIT ?", (max(1, int(limit or 100)),))
        return {"count": len(rows), "conversations": [dict(r) for r in rows]}

    def get_conversation(self, conversation_id: int) -> dict[str, Any]:
        row = self.db.query_one("SELECT * FROM chat_conversations WHERE id=?", (int(conversation_id),))
        if not row:
            raise ValueError(f"Conversation not found: {conversation_id}")
        conv = dict(row)
        try:
            conv["state"] = json.loads(conv.get("state_json") or "{}")
        except Exception:
            conv["state"] = {}
        return {"conversation": conv, "state": conv.get("state") or {}, "messages": self._conversation_history(int(conversation_id))}

    def edit_conversation_message(self, conversation_id: int, message_id: int, content: str, truncate_after: bool = True) -> dict[str, Any]:
        conv_id = int(conversation_id)
        msg_id = int(message_id)
        row = self.db.query_one("SELECT * FROM chat_messages WHERE id=? AND conversation_id=?", (msg_id, conv_id))
        if not row:
            raise ValueError(f"Message not found in conversation: {msg_id}")
        now = self._now()
        self.db.execute("UPDATE chat_messages SET content=?, created_at=? WHERE id=? AND conversation_id=?", (content or "", now, msg_id, conv_id))
        deleted = 0
        if truncate_after:
            count = self.db.query_one("SELECT COUNT(*) AS n FROM chat_messages WHERE conversation_id=? AND id>?", (conv_id, msg_id)) or {"n": 0}
            deleted = int(count.get("n") or 0)
            self.db.execute("DELETE FROM chat_messages WHERE conversation_id=? AND id>?", (conv_id, msg_id))
        self.db.execute("UPDATE chat_conversations SET updated_at=? WHERE id=?", (now, conv_id))
        result = self.get_conversation(conv_id)
        result["edited_message_id"] = msg_id
        result["deleted_after_count"] = deleted
        return result


    def delete_conversation_message(self, conversation_id: int, message_id: int, delete_following: bool = False) -> dict[str, Any]:
        conv_id = int(conversation_id)
        msg_id = int(message_id)
        row = self.db.query_one("SELECT id FROM chat_messages WHERE id=? AND conversation_id=?", (msg_id, conv_id))
        if not row:
            raise ValueError(f"Message not found in conversation: {msg_id}")
        if delete_following:
            self.db.execute("DELETE FROM chat_messages WHERE conversation_id=? AND id>=?", (conv_id, msg_id))
        else:
            self.db.execute("DELETE FROM chat_messages WHERE conversation_id=? AND id=?", (conv_id, msg_id))
        state = self._conversation_state(conv_id)
        # Removing turns can invalidate a condensed memory summary. Keep saved
        # image/project state but clear auto-generated memory so the next request
        # rebuilds context from the remaining message history.
        for key in ("memory_summary", "memory_updated_at", "last_response_looks_incomplete", "last_response_char_count"):
            state.pop(key, None)
        now = self._now()
        self.db.execute("UPDATE chat_conversations SET state_json=?, updated_at=? WHERE id=?", (json.dumps(state, ensure_ascii=False, default=str), now, conv_id))
        result = self.get_conversation(conv_id)
        result["deleted_message_id"] = msg_id
        result["deleted_following"] = bool(delete_following)
        return result

    def clear_conversation(self, conversation_id: int, clear_messages: bool = True, clear_memory: bool = True, keep_state: bool = True, reset_context: bool = True) -> dict[str, Any]:
        conv_id = int(conversation_id)
        row = self.db.query_one("SELECT id FROM chat_conversations WHERE id=? AND archived=0", (conv_id,))
        if not row:
            raise ValueError(f"Conversation not found: {conversation_id}")
        max_row = self.db.query_one("SELECT COALESCE(MAX(id), 0) AS max_id FROM chat_messages WHERE conversation_id=?", (conv_id,)) or {"max_id": 0}
        max_message_id = int(max_row.get("max_id") or 0)
        if clear_messages:
            self.db.execute("DELETE FROM chat_messages WHERE conversation_id=?", (conv_id,))
            max_message_id = 0
        state = self._conversation_state(conv_id) if keep_state else {}
        if clear_memory:
            prior_budget = dict(state.get("last_context_budget") or {}) if isinstance(state.get("last_context_budget"), dict) else {}
            prior_model_name = str(state.get("last_model_name") or prior_budget.get("model_name") or "")
            prior_context_limit = int(prior_budget.get("context_limit_tokens") or 0)
            for key in (
                "memory_summary", "memory_updated_at", "last_response_looks_incomplete",
                "last_response_char_count", "last_model_name", "last_media_ids",
                "last_external_paths", "last_metadata_field_paths", "conversation_memory_summary"
            ):
                state.pop(key, None)
            now_for_budget = self._now()
            if reset_context:
                state["context_reset_message_id"] = max_message_id
                state["context_cleared_at"] = now_for_budget
            else:
                state.pop("context_reset_message_id", None)
                state.pop("context_cleared_at", None)
            state["memory_summary"] = ""
            state["last_context_budget"] = {
                "estimated": True,
                "model_name": prior_model_name,
                "context_limit_tokens": prior_context_limit,
                "input_tokens_estimate": 0,
                "output_tokens_estimate": 0,
                "tokens_used_estimate": 0,
                "percent_used": 0,
                "warning": False,
                "critical": False,
                "context_cleared": True,
                "note": "Model-visible memory/context was cleared. Older visible transcript messages are not sent back to the model unless copied into a new message.",
            }
        now = self._now()
        self.db.execute("UPDATE chat_conversations SET state_json=?, updated_at=? WHERE id=?", (json.dumps(state, ensure_ascii=False, default=str), now, conv_id))
        result = self.get_conversation(conv_id)
        result["cleared"] = {"messages": bool(clear_messages), "memory": bool(clear_memory), "kept_state": bool(keep_state), "context_reset_message_id": int(state.get("context_reset_message_id") or 0)}
        return result

    def archive_conversation(self, conversation_id: int) -> dict[str, Any]:
        self.db.execute("UPDATE chat_conversations SET archived=1, updated_at=? WHERE id=?", (self._now(), int(conversation_id)))
        return {"archived": int(conversation_id)}

    def fork_conversation(self, message_id: int, title: str | None = None) -> dict[str, Any]:
        source = self.db.query_one("SELECT * FROM chat_messages WHERE id=?", (int(message_id),))
        if not source:
            raise ValueError(f"Message not found: {message_id}")
        conv = self.db.query_one("SELECT * FROM chat_conversations WHERE id=?", (int(source["conversation_id"]),))
        if not conv:
            raise ValueError("Source conversation not found")
        now = self._now()
        new_title = title or f"Fork of {conv['title']} @ msg {message_id}"
        new_id = self.db.execute(
            "INSERT INTO chat_conversations(title, model_name, dataset_id, state_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (new_title, conv["model_name"], conv["dataset_id"], conv["state_json"], now, now),
        )
        new_id = int(new_id)
        rows = self.db.query("SELECT * FROM chat_messages WHERE conversation_id=? AND id<=? ORDER BY id", (int(conv["id"]), int(message_id)))
        for row in rows:
            self.db.execute(
                "INSERT INTO chat_messages(conversation_id, role, content, model_name, context_json, response_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_id, row["role"], row["content"], row["model_name"], row["context_json"], row["response_json"], now),
            )
        return self.get_conversation(new_id)

    def metadata_context_for_media(self, media_ids: list[int], field_paths: list[str] | None = None, include_raw: bool = False) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        field_paths = [p for p in (field_paths or []) if str(p).strip()]
        metadata_service = getattr(self, "metadata_service", None)
        for media_id in media_ids[:24]:
            try:
                if metadata_service:
                    payload = metadata_service.extract_media(int(media_id), include_raw=include_raw, persist=True)
                    item = {
                        "media_id": int(media_id),
                        "source_app": payload.get("source_app"),
                        "positive_prompt": payload.get("positive_prompt"),
                        "negative_prompt": payload.get("negative_prompt"),
                        "caption": payload.get("caption"),
                        "tags": payload.get("tags") or [],
                        "lora_refs": payload.get("lora_refs") or [],
                    }
                    if field_paths:
                        item["selected_fields"] = metadata_service.compose_metadata_parts(payload, field_paths, input_delimiter="none", output_delimiter="\n", split_to_tags=False, keep_parentheses=True, keep_curly_braces=True, keep_square_brackets=True, keep_weight_syntax=True)
                    else:
                        schema = metadata_service.schema_for_payload(payload, max_items=250)
                        item["schema_paths"] = [e for e in schema.get("entries", []) if e.get("selectable")][:80]
                    items.append(item)
                else:
                    row = self.db.query_one("SELECT * FROM media_metadata WHERE media_id=? ORDER BY updated_at DESC LIMIT 1", (int(media_id),))
                    if row:
                        items.append({"media_id": int(media_id), "source_app": row["source_app"], "positive_prompt": row["positive_prompt"], "negative_prompt": row["negative_prompt"], "tag_string": row["tag_string"], "caption": row["caption"]})
            except Exception as exc:
                items.append({"media_id": int(media_id), "error": str(exc)})
        return items

    def metadata_context_for_paths(self, paths: list[str], field_paths: list[str] | None = None, include_raw: bool = False) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        field_paths = [p for p in (field_paths or []) if str(p).strip()]
        metadata_service = getattr(self, "metadata_service", None)
        if not metadata_service:
            return items
        for raw_path in (paths or [])[:12]:
            try:
                candidate = Path(str(raw_path).strip().strip('"'))
                if not candidate.exists():
                    items.append({"path": str(raw_path), "error": "Path does not exist"})
                    continue
                payload = metadata_service.extract_path(candidate, include_raw=include_raw)
                item = {
                    "path": str(candidate),
                    "source_app": payload.get("source_app"),
                    "positive_prompt": payload.get("positive_prompt"),
                    "negative_prompt": payload.get("negative_prompt"),
                    "caption": payload.get("caption"),
                    "tags": payload.get("tags") or [],
                    "lora_refs": payload.get("lora_refs") or [],
                }
                if field_paths:
                    item["selected_fields"] = metadata_service.compose_metadata_parts(payload, field_paths, input_delimiter="none", output_delimiter="\n", split_to_tags=False, keep_parentheses=True, keep_curly_braces=True, keep_square_brackets=True, keep_weight_syntax=True)
                else:
                    schema = metadata_service.schema_for_payload(payload, max_items=250)
                    item["schema_paths"] = [e for e in schema.get("entries", []) if e.get("selectable")][:80]
                items.append(item)
            except Exception as exc:
                items.append({"path": str(raw_path), "error": str(exc)})
        return items

    def _runtime_device_for_request(self, model_name: str, request: Any) -> str:
        requested = str(getattr(request, "device", "auto") or "auto")
        opts = getattr(request, "options", {}) or {}
        prefer_loaded = isinstance(opts, dict) and bool(opts.get("use_loaded_model_placement"))
        if prefer_loaded:
            try:
                info = self.registry.loaded_placement(model_name)
                if info and info.get("device"):
                    return str(info.get("device"))
            except Exception:
                pass
        if requested.lower() not in {"auto", "cuda"}:
            return requested
        ids = self._parse_device_ids_value(getattr(request, "device_ids", None))
        if ids and str(getattr(request, "sharding_strategy", "none") or "none").lower() == "none":
            return f"cuda:{ids[0]}"
        try:
            info = self.registry.loaded_placement(model_name)
            if info and info.get("device"):
                loaded_device = str(info.get("device"))
                # Do not let a previously CPU-offloaded or stale placement override
                # an explicit GPU selection for the current inference request.
                if loaded_device.lower() == "cpu" and requested.lower() in {"auto", "cuda"}:
                    return requested
                return loaded_device
        except Exception:
            pass
        return requested

    def _runtime_options(self, request: Any) -> dict[str, Any]:
        opts = dict(getattr(request, "options", {}) or {})
        for key in [
            "device_ids",
            "sharding_strategy",
            "device_map",
            "max_memory",
            "torch_dtype",
            "quantization",
            "runtime_engine",
            "tensor_parallel_size",
        ]:
            value = getattr(request, key, None)
            if value not in (None, "", [], {}):
                opts[key] = value
        if self.settings:
            opts.setdefault("temperature", self.settings.model_temperature)
            opts.setdefault("max_new_tokens", self.settings.model_max_new_tokens)
            opts.setdefault("huggingface_token", self.settings.huggingface_token)
            try:
                record = self.registry.get_record(getattr(request, "model_name", "") or "")
                provider_key = str(getattr(record, "provider", "") or "").lower().replace("-", "_")
                cloud_defaults = dict(getattr(self.settings, "cloud_model_runtime_defaults", {}) or {})
                provider_defaults = dict(cloud_defaults.get(provider_key) or {})
                if provider_defaults:
                    opts.setdefault("token_profile", provider_defaults.get("token_profile") or "")
                    if provider_defaults.get("model_id"):
                        opts.setdefault("api_model_id", provider_defaults.get("model_id"))
                    if provider_defaults.get("context_shrinker_model"):
                        opts.setdefault("context_shrinker_model", provider_defaults.get("context_shrinker_model"))
                    if provider_defaults.get("context_shrink_policy"):
                        opts.setdefault("context_shrink_policy", provider_defaults.get("context_shrink_policy"))
                    if provider_defaults.get("max_input_tokens"):
                        opts.setdefault("max_input_tokens", provider_defaults.get("max_input_tokens"))
                    if provider_defaults.get("max_output_tokens"):
                        opts.setdefault("max_new_tokens", int(provider_defaults.get("max_output_tokens") or opts.get("max_new_tokens") or 512))
                    if provider_key == "openrouter":
                        if provider_defaults.get("transforms"):
                            opts.setdefault("transforms", provider_defaults.get("transforms"))
                        route = provider_defaults.get("provider_route")
                        if isinstance(route, dict) and route:
                            opts.setdefault("provider", route)
            except Exception:
                pass
        return opts


    def select_tags(self, request: ModelTagSelectionRequest) -> dict[str, Any]:
        media_ids = list(request.media_ids)
        if request.dataset_id and not media_ids:
            rows = self.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1 ORDER BY id ASC", (request.dataset_id,))
            media_ids = [row["id"] for row in rows]
        criteria = (request.criteria or "").lower()
        options = dict(request.options or {})
        all_categories = bool(options.get("all_categories") or options.get("include_all_categories") or options.get("bypass_category_filter"))
        validate_existing_tags = bool(options.get("validate_existing_tags") or options.get("validate_existing") or options.get("select_existing_only"))
        requested_categories = set() if all_categories else {c.strip().lower() for c in request.categories if c.strip()}
        words = {w.strip().lower().replace(" ", "_") for w in re.split(r"[,;\s]+", criteria) if len(w.strip()) > 1}
        category_words = {"artist", "character", "copyright", "series", "general", "meta", "species", "rating", "style", "artstyle", "concept", "trigger", "quality", "negative", "unknown", "custom", "invalid", "lore"}
        for word in list(words):
            if not all_categories and word in category_words:
                requested_categories.add("copyright" if word == "series" else "style" if word == "artstyle" else word)
        if all_categories:
            requested_categories.clear()
        try:
            profile_categories = [str(c.get("key")) for c in self.tags.categories(request.profile_key) if c.get("key")]
        except Exception:
            profile_categories = []

        selected_by_media: dict[int, list[str]] = {}
        union: list[str] = []
        seen_union: set[str] = set()
        used_model_predictions = False
        used_chat_model = False
        used_manual_candidates = False
        selection_ready = False
        tag_task_completion: dict[int, dict[str, Any]] = {}
        visible_plans_by_media: dict[int, str] = {}

        def add_to_union(tags: list[str]) -> None:
            for tag in tags:
                if tag not in seen_union:
                    union.append(tag)
                    seen_union.add(tag)

        def normalize_candidates(values: Any) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()
            if isinstance(values, str):
                values = [values]
            for value in values or []:
                text = str(value or "").strip()
                if not text:
                    continue
                parts = re.split(r"[,;\n]+", text) if any(sep in text for sep in [",", ";", "\n"]) else [text]
                for part in parts:
                    clean = str(part or "").strip().lower().replace(" ", "_")
                    clean = re.sub(r"[^a-z0-9_:\-./]+", "", clean)
                    if clean and clean not in seen:
                        out.append(clean)
                        seen.add(clean)
            return out

        def restrict_to_existing_if_requested(current: list[str], proposed: list[str]) -> list[str]:
            if not validate_existing_tags or not current or request.operation != "preview":
                return proposed
            existing_by_norm: dict[str, str] = {}
            for tag in current:
                normalized = normalize_candidates([tag])
                if normalized:
                    existing_by_norm.setdefault(normalized[0], tag)
            selected: list[str] = []
            seen: set[str] = set()
            for tag in proposed:
                normalized = normalize_candidates([tag])
                key = normalized[0] if normalized else str(tag or "").strip().lower()
                chosen = existing_by_norm.get(key)
                if chosen and chosen not in seen:
                    selected.append(chosen)
                    seen.add(chosen)
            return selected

        def candidates_for_media(media_id: int) -> list[str]:
            by_media = getattr(request, "candidate_tags_by_media", {}) or {}
            raw = by_media.get(str(media_id))
            if raw is None:
                raw = by_media.get(media_id)  # defensive for direct/unit callers
            if raw is None:
                raw = request.candidate_tags
            return normalize_candidates(raw)

        def manual_selection_for(media_id: int, current: list[str], candidates: list[str]) -> list[str]:
            current_set = set(current)
            if request.operation in {"preview", "remove", "keep_only"}:
                return [tag for tag in current if tag in set(candidates)]
            if request.operation == "add":
                return [tag for tag in candidates if tag not in current_set]
            if request.operation == "set":
                return list(candidates)
            return list(candidates)

        def criteria_requests_select_all() -> bool:
            compact = re.sub(r"\s+", " ", criteria).strip().lower()
            return compact in {"select all", "select all tags", "all tags", "highlight all", "highlight all tags"} or "select all tags" in compact or "highlight all tags" in compact

        def match_existing_from_text(text: str, current: list[str]) -> list[str]:
            body = str(text or "").lower()
            if not body or not current:
                return []
            body_space = body.replace("_", " ").replace("-", " ")
            selected: list[str] = []
            seen: set[str] = set()
            for tag in current:
                key = str(tag or "").strip()
                if not key:
                    continue
                norm = key.lower()
                variants = {norm, norm.replace("_", " "), norm.replace("_", "-"), norm.replace(":", " ")}
                if any((variant and (variant in body or variant in body_space)) for variant in variants):
                    if key not in seen:
                        selected.append(key)
                        seen.add(key)
            return selected

        def response_implies_all_existing(text: str) -> bool:
            body = re.sub(r"\s+", " ", str(text or "").strip().lower())
            if not body:
                return False
            positive = any(phrase in body for phrase in [
                "all tags", "all existing tags", "all listed tags", "every tag", "all of the tags",
                "all are present", "all are visible", "all match", "all valid", "all selected",
            ])
            negative = any(phrase in body for phrase in ["not all", "none", "no tags", "cannot determine", "can't determine", "unclear"])
            return positive and not negative

        if criteria_requests_select_all():
            for media_id in media_ids:
                current = self.tags.get_tags(media_id)
                candidates = candidates_for_media(media_id)
                chosen = list(current) if current else list(candidates)
                selected_by_media[media_id] = chosen
                add_to_union(chosen)
            selection_ready = True
            used_manual_candidates = True

        manual_only = bool(options.get("manual_only"))
        if manual_only:
            any_manual = False
            for media_id in media_ids:
                current = self.tags.get_tags(media_id)
                candidates = candidates_for_media(media_id)
                chosen = manual_selection_for(media_id, current, candidates) if candidates else []
                selected_by_media[media_id] = chosen
                if candidates:
                    any_manual = True
                add_to_union(chosen)
            if any_manual:
                selection_ready = True
                used_manual_candidates = True

        try:
            record = self.registry.get_record(request.model_name or "dataset-assistant")
        except Exception:
            record = None
        caps = set(getattr(record, "capabilities", []) or []) if record else set()
        kind = getattr(record, "kind", "") if record else ""
        is_predictive_model = bool(record and (caps.intersection({"tag", "auto_tag", "classify", "rating", "image_classification"}) or kind in {"tagger", "classifier", "rating"}) and "chat" not in caps)
        is_chat_model = bool(record and request.model_name != "dataset-assistant" and ("chat" in caps or "vlm" in caps or "image_text_to_text" in caps or kind in {"vlm", "llm", "assistant"}))
        if not selection_ready and (is_predictive_model or is_chat_model):
            self.lifecycle.update(request.model_name, "inference", state="running", progress=0.01, message="Tag-selection request received")

        if not selection_ready and is_predictive_model:
            if self.lifecycle.is_active(request.model_name, "download"):
                raise RuntimeError(f"{request.model_name} is still downloading. Wait for download to finish before using it for tag selection.")
            if self.lifecycle.is_active(request.model_name, "load") and not self.registry.is_loaded(request.model_name):
                raise RuntimeError(f"{request.model_name} is still loading into memory. Wait for loading to finish before using it for tag selection.")
            threshold = float(options.get("threshold", self.settings.classifier_threshold if self.settings else 0.70) or 0.0)
            opts = self._runtime_options(request)
            opts.update(options)
            opts.setdefault("threshold", threshold)
            opts.setdefault("top_k", int(options.get("top_k", 250) or 250))
            try:
                if not self.registry.is_loaded(request.model_name):
                    self._load_model_from_request(request, progress=None, job_id=None)
                self.lifecycle.update(request.model_name, "inference", state="running", progress=0.0, message="Tag-selection inference started")
                for idx, media_id in enumerate(media_ids, start=1):
                    media = self.media.get(media_id)
                    if not media:
                        selected_by_media[media_id] = []
                        continue
                    runtime_device = self._runtime_device_for_request(request.model_name, request)
                    pred = self._registry_predict_with_vram_guard(request.model_name, Path(media.path), device=runtime_device, options=options, **opts)
                    payload = {
                        "kind": pred.kind,
                        "tags": pred.tags,
                        "caption": pred.caption,
                        "classes": pred.classes,
                        "embedding": pred.embedding,
                        "masks": pred.masks,
                        "raw": pred.raw,
                    }
                    payload = self.tags.normalize_model_prediction_payload(
                        payload,
                        profile_key=request.profile_key or str(options.get("tag_profile") or options.get("profile_key") or "e621"),
                        apply_aliases=bool(options.get("apply_model_tag_aliases", True)),
                        apply_implications=bool(options.get("apply_model_tag_implications", True)),
                    )
                    try:
                        self.media.add_prediction(media_id, None, request.model_name, pred.kind, payload)
                    except Exception:
                        pass
                    candidates: list[str] = []
                    for tag, score in list(payload.get("tags") or []):
                        if float(score) >= threshold and tag not in candidates:
                            candidates.append(str(tag))
                    if not candidates:
                        for tag, score in list(payload.get("classes") or []):
                            if float(score) >= threshold and tag not in candidates:
                                candidates.append(str(tag))
                    current_existing = self.tags.get_tags(media_id) if validate_existing_tags else []
                    candidates = restrict_to_existing_if_requested(current_existing, candidates)
                    selected_by_media[media_id] = candidates
                    add_to_union(candidates)
                    frac = idx / max(1, len(media_ids))
                    self.lifecycle.update(request.model_name, "inference", state="running", progress=frac, message=f"{request.model_name}: tag-selection inference {idx}/{len(media_ids)}")
                self.lifecycle.complete(request.model_name, "inference", message="Tag-selection inference completed", result={"processed": len(media_ids), "selected_tags": len(union)})
                used_model_predictions = True
                selection_ready = True
            except Exception as exc:
                self.lifecycle.fail(request.model_name, "inference", exc)
                raise

        if not selection_ready and is_chat_model:
            if self.lifecycle.is_active(request.model_name, "download"):
                raise RuntimeError(f"{request.model_name} is still downloading. Wait for download to finish before using it for tag selection.")
            if self.lifecycle.is_active(request.model_name, "load") and not self.registry.is_loaded(request.model_name):
                raise RuntimeError(f"{request.model_name} is still loading into memory. Wait for loading to finish before using it for tag selection.")
            opts = self._runtime_options(request)
            opts.update(options)
            if record:
                self._inject_provider_token(opts, record.provider, request)
            try:
                if not self.registry.is_loaded(request.model_name):
                    self._load_model_from_request(request, progress=None, job_id=None)
                self.lifecycle.update(request.model_name, "inference", state="running", progress=0.0, message="VLM/LLM tag-selection started")
                for idx, media_id in enumerate(media_ids, start=1):
                    media = self.media.get(media_id)
                    if not media:
                        selected_by_media[media_id] = []
                        continue
                    current = self.tags.get_tags(media_id)
                    manual_candidates = candidates_for_media(media_id)
                    if all_categories:
                        category_hint = "all tag categories" + (f" ({', '.join(profile_categories)})" if profile_categories else "")
                    else:
                        category_hint = ", ".join(sorted(requested_categories)) if requested_categories else "any relevant tag category"
                    operation_hint = {
                        "preview": "select or propose tags for review",
                        "remove": "select existing tags that should be removed",
                        "keep_only": "select existing tags that should be kept",
                        "set": "produce the final complete tag list for this image",
                        "add": "produce new tags that should be added to this image",
                    }.get(request.operation, "select tags")
                    prompt = (
                        "You are helping curate image-dataset tags.\n"
                        f"Task: {operation_hint}.\n"
                        f"Criteria from user: {request.criteria or 'use visual evidence and dataset tagging best practices'}.\n"
                        f"Target categories: {category_hint}.\n"
                        f"All-category bypass enabled: {'yes' if all_categories else 'no'}.\n"
                        f"Existing tags: {', '.join(current) if current else '(none)'}.\n"
                        f"Highlighted/manual candidate tags: {', '.join(manual_candidates) if manual_candidates else '(none)'}.\n\n"
                        "Return a short answer with one line exactly like:\n"
                        "tags: tag_one, tag_two, tag_three\n"
                        "If your model is better at structured extraction, you may instead return JSON like {\"selected_existing_tags\": [\"tag_one\", \"tag_two\"], \"add_tags\": [], \"remove_tags\": [], \"caption\": \"optional caption\"}.\n"
                        "For validate-existing-tags tasks, select only tags from the Existing tags list that are actually visible/present. "
                        "For add/set tasks, you may propose new normalized underscore tags. "
                        "Do not put prose inside the tags line; include only tags useful for this operation."
                    )
                    prompt = self._append_lora_rules_to_prompt(prompt, options)
                    if manual_candidates:
                        prompt += "\nThe highlighted/manual candidate tags are user-selected context. Honor them unless they clearly conflict with the requested operation or the image."
                    if request.operation in {"remove", "keep_only"} and current:
                        prompt += "\nFor remove/keep-only operations, prefer tags from the existing tag list unless a clear correction is needed."
                    context = {"media": [media.model_dump()], "dataset": {}, "history": []}
                    try:
                        context["generation_metadata"] = self.metadata_context_for_media([media_id], include_raw=False)
                    except Exception:
                        context["generation_metadata"] = []
                    runtime_device = self._runtime_device_for_request(request.model_name, request)
                    # Actionable tag operations need completion protection.
                    # Ask for a sentinel and automatically continue once or more if
                    # the local/API model stops mid-list or reaches its token budget.
                    tag_reasoning = self._chat_reasoning_options(options)
                    if options.get("think_longer") or options.get("assistant_reasoning") or options.get("show_visible_plan"):
                        self._apply_chat_reasoning_runtime(opts, tag_reasoning)
                    prompt_with_completion = prompt + "\n\nCritical completion rule: end the final answer with [TASK_COMPLETE]. If you run out of space, continue in the next response without repeating previous tags."
                    visible_plan_for_media = ""
                    if (options.get("think_longer") or options.get("assistant_reasoning") or options.get("show_visible_plan")) and tag_reasoning.get("show_visible_plan") and int(tag_reasoning.get("planning_passes") or 0) > 0:
                        try:
                            plan_runtime = dict(opts)
                            plan_runtime["max_new_tokens"] = int(tag_reasoning.get("plan_max_new_tokens") or 768)
                            plan_response = self._registry_chat_with_vram_guard(
                                request.model_name,
                                self._visible_planning_prompt(prompt, context, tag_reasoning, 1),
                                context=context,
                                device=runtime_device,
                                options=options,
                                **plan_runtime,
                            )
                            visible_plan_for_media = self._clean_visible_plan(plan_response.get("response") or "")
                            if visible_plan_for_media:
                                visible_plans_by_media[int(media_id)] = visible_plan_for_media
                                context["visible_plan"] = visible_plan_for_media
                                prompt_with_completion = self._final_prompt_with_visible_plan(prompt_with_completion, visible_plan_for_media)
                        except Exception as exc:
                            visible_plans_by_media[int(media_id)] = f"Planning pass failed: {exc}"
                    try:
                        opts["max_new_tokens"] = max(int(opts.get("max_new_tokens") or 0), int(options.get("min_tag_task_max_new_tokens") or 1024))
                    except Exception:
                        opts["max_new_tokens"] = 1024
                    response = self._registry_chat_with_vram_guard(request.model_name, prompt_with_completion, context=context, device=runtime_device, options=options, **opts)
                    response_text = str(response.get("response") or "")
                    continuation_rounds: list[dict[str, Any]] = []
                    max_tag_continuations = max(0, min(4, int(options.get("max_tag_continuation_rounds") or 2)))
                    for round_idx in range(max_tag_continuations):
                        has_marker = self._has_task_completion_marker(response_text)
                        looks_incomplete = self._response_looks_incomplete(response_text, opts)
                        # Always perform one verifier/continuation round when the
                        # model omitted the sentinel. The model can return only
                        # [TASK_COMPLETE] if there is nothing more to add.
                        if has_marker or (round_idx > 0 and not looks_incomplete):
                            break
                        cont_context = dict(context)
                        cont_context["tag_task_response_so_far"] = response_text[-6000:]
                        cont_prompt = self._continue_incomplete_tag_task_prompt(prompt_with_completion, response_text, operation=request.operation, current_tags=current)
                        try:
                            cont = self._registry_chat_with_vram_guard(request.model_name, cont_prompt, context=cont_context, device=runtime_device, options=options, **opts)
                        except Exception as exc:
                            continuation_rounds.append({"round": round_idx + 1, "error": str(exc)})
                            break
                        cont_text = str(cont.get("response") or "")
                        if re.fullmatch(r"\s*\[TASK_COMPLETE\]\s*", cont_text, flags=re.I):
                            response_text = response_text.rstrip() + "\n[TASK_COMPLETE]"
                            continuation_rounds.append({"round": round_idx + 1, "verified_complete": True})
                            break
                        merged = self._merge_continuation_text(response_text, cont_text)
                        continuation_rounds.append({"round": round_idx + 1, "added_chars": max(0, len(merged) - len(response_text)), "raw_chars": len(cont_text), "task_complete_marker": self._has_task_completion_marker(cont_text)})
                        if merged == response_text:
                            break
                        response_text = merged
                        for tag in cont.get("suggested_tags") or []:
                            response.setdefault("suggested_tags", [])
                            if tag not in response["suggested_tags"]:
                                response["suggested_tags"].append(tag)
                    response_text_for_parse = self._strip_completion_markers(response_text)
                    parsed = response.get("suggested_tags") or _extract_tags(response_text_for_parse)
                    normalized = normalize_candidates(parsed)
                    if validate_existing_tags and current and not normalized:
                        normalized = normalize_candidates(match_existing_from_text(response_text_for_parse, current))
                    if validate_existing_tags and current and not normalized and response_implies_all_existing(response_text_for_parse):
                        normalized = list(current)
                    if not normalized and criteria_requests_select_all():
                        normalized = list(current) if current else manual_candidates
                    if not normalized and manual_candidates:
                        normalized = manual_candidates
                    task_completion_verified = self._has_task_completion_marker(response_text) or any(r.get("verified_complete") for r in continuation_rounds)
                    task_looks_incomplete = self._response_looks_incomplete(response_text_for_parse, opts)
                    # For operations that would modify files, do not apply an
                    # ambiguous half-finished LLM/VLM response. Preview can still
                    # show its selection plus warnings for user review.
                    if request.operation != "preview" and task_looks_incomplete and not task_completion_verified:
                        raise RuntimeError(
                            "The assistant/model response still appears incomplete after automatic continuation attempts. "
                            "No tag changes were applied. Use a larger max token budget, fewer candidate tags, or run preview first. "
                            f"Continuation rounds: {continuation_rounds}"
                        )
                    tag_task_completion[int(media_id)] = {
                        "completion_verified": bool(task_completion_verified),
                        "looks_incomplete": bool(task_looks_incomplete),
                        "continuation_rounds": continuation_rounds,
                        "response_chars": len(response_text_for_parse),
                    }
                    if request.operation in {"remove", "keep_only"} and current:
                        current_set = set(current)
                        selected = [tag for tag in normalized if tag in current_set]
                    else:
                        selected = restrict_to_existing_if_requested(current, normalized)
                    selected_by_media[media_id] = selected
                    add_to_union(selected)
                    frac = idx / max(1, len(media_ids))
                    self.lifecycle.update(request.model_name, "inference", state="running", progress=frac, message=f"{request.model_name}: VLM/LLM tag selection {idx}/{len(media_ids)}")
                self.lifecycle.complete(request.model_name, "inference", message="VLM/LLM tag-selection completed", result={"processed": len(media_ids), "selected_tags": len(union), "chat_model_used": True})
                used_chat_model = True
                used_model_predictions = True
                selection_ready = True
            except Exception as exc:
                self.lifecycle.fail(request.model_name, "inference", exc)
                raise

        if not selection_ready:
            ignored = {"select", "remove", "keep", "tags", "tag", "with", "from", "all", "only", "and", "or", "the", "a"}
            for media_id in media_ids:
                tags = self.tags.get_tags(media_id)
                stored_categories = self.tags.get_categories(media_id)
                metadata = self.tags.metadata(tags, request.profile_key)
                media_explicit_candidates = set(candidates_for_media(media_id))
                chosen: list[str] = []
                for tag in tags:
                    meta = metadata.get(tag, {})
                    category = str(stored_categories.get(tag) or meta.get("category") or "unknown").lower()
                    known = bool(meta.get("known")) or category not in {"unknown", "custom"}
                    should_select = False
                    if media_explicit_candidates and tag in media_explicit_candidates:
                        should_select = True
                    if requested_categories and category in requested_categories:
                        should_select = True
                    if "unknown" in words and not known:
                        should_select = True
                    if "known" in words and known:
                        should_select = True
                    if "low_count" in words and int(meta.get("post_count") or 0) < int(options.get("low_count_threshold", 10)):
                        should_select = True
                    if any(word and word in tag.lower() for word in words - category_words - ignored):
                        should_select = True
                    if all_categories and not words and not media_explicit_candidates:
                        should_select = True
                    elif not words and not requested_categories and not media_explicit_candidates:
                        should_select = True
                    if should_select:
                        chosen.append(tag)
                selected_by_media[media_id] = chosen
                add_to_union(chosen)

        applied: dict[str, Any] = {
            "operation": request.operation,
            "media_ids": [],
            "changed": 0,
            "model_predictions_used": used_model_predictions,
            "chat_model_used": used_chat_model,
            "manual_selection_used": used_manual_candidates,
        }
        if request.operation != "preview":
            for media_id, chosen in selected_by_media.items():
                current = self.tags.get_tags(media_id)
                chosen_set = set(chosen)
                if request.operation == "remove":
                    updated = [tag for tag in current if tag not in chosen_set]
                elif request.operation == "keep_only":
                    updated = [tag for tag in current if tag in chosen_set]
                elif request.operation == "set":
                    updated = list(chosen)
                elif request.operation == "add":
                    updated = list(current)
                    add_tags = list(chosen) if (used_model_predictions or used_manual_candidates) else list(union)
                    for tag in add_tags:
                        if tag not in updated:
                            updated.append(tag)
                else:
                    updated = current
                if updated != current:
                    self.tags.set_tags(media_id, updated, source=request.model_name, save_sidecar=True, profile_key=request.profile_key, order_strategy="retain")
                    applied["changed"] += 1
                    applied["media_ids"].append(media_id)
        completion_summary = {
            "by_media": tag_task_completion,
            "any_incomplete": any(bool(v.get("looks_incomplete")) and not bool(v.get("completion_verified")) for v in tag_task_completion.values()),
            "continuation_rounds_total": sum(len(v.get("continuation_rounds") or []) for v in tag_task_completion.values()),
            "enforced_for_chat_models": bool(used_chat_model),
        }
        reasoning_summary = {
            "visible_plans_enabled": bool(visible_plans_by_media),
            "hidden_chain_of_thought_exposed": False,
            "live_action_notes_enabled": bool(options.get("show_live_action_notes", True)),
            "note": "Visible plans are concise user-facing task plans, not hidden/private chain-of-thought.",
        }
        return {"model_name": request.model_name, "criteria": request.criteria, "all_categories": all_categories, "validate_existing_tags": validate_existing_tags, "selected_tags_by_media": selected_by_media, "selected_tags": union, "applied": applied, "completion": completion_summary, "visible_plans_by_media": visible_plans_by_media, "reasoning": reasoning_summary}


    def tag_scores(self, media_id: int, tags: list[str] | None = None) -> dict[str, Any]:
        media = self.media.get(media_id)
        if not media:
            raise ValueError(f"Unknown media id: {media_id}")
        tag_list = tags or media.tags
        scores = self.media.prediction_scores_for_media(media_id, tag_list)
        return {"media_id": media_id, "tags": tag_list, "scores": scores}

    def tag_score_analytics(self, dataset_id: int | None = None, media_ids: list[int] | None = None, limit: int = 200, min_score: float = 0.0) -> dict[str, Any]:
        params: list[Any] = []
        where = ["s.score >= ?"]
        params.append(float(min_score or 0.0))
        if media_ids:
            ids = [int(x) for x in media_ids if int(x) > 0]
            if ids:
                where.append("s.media_id IN (" + ",".join("?" for _ in ids) + ")")
                params.extend(ids)
        elif dataset_id:
            where.append("m.dataset_id=?")
            params.append(int(dataset_id))
        where_sql = " AND ".join(where)
        rows = self.db.query(
            f"""
            SELECT s.tag, s.model_name, COUNT(*) AS count, AVG(s.score) AS avg_score, MAX(s.score) AS max_score, MIN(s.score) AS min_score
            FROM tag_prediction_scores s
            JOIN media m ON m.id=s.media_id
            WHERE {where_sql}
            GROUP BY s.tag, s.model_name
            ORDER BY s.tag ASC, avg_score DESC
            LIMIT ?
            """,
            (*params, max(1, int(limit or 200))),
        )
        tag_order: list[str] = []
        model_order: list[str] = []
        matrix: dict[str, dict[str, dict[str, Any]]] = {}
        for row in rows:
            tag = row["tag"]
            model = row["model_name"]
            if tag not in tag_order:
                tag_order.append(tag)
            if model not in model_order:
                model_order.append(model)
            matrix.setdefault(tag, {})[model] = {
                "count": int(row["count"] or 0),
                "avg_score": float(row["avg_score"] or 0),
                "max_score": float(row["max_score"] or 0),
                "min_score": float(row["min_score"] or 0),
            }
        return {"dataset_id": dataset_id, "media_ids": media_ids or [], "tags": tag_order, "models": model_order, "matrix": matrix, "rows": rows}

    def feature_matrix(self) -> dict[str, Any]:
        models = self.registry.list()
        groups = {
            "tagging": ["tag", "auto_tag", "multilabel"],
            "captioning": ["caption", "dense_caption"],
            "caption_to_tags": ["caption_split"],
            "upscaling": ["upscale", "super_resolution"],
            "segmentation": ["segment", "mask", "video_mask"],
            "cropping_detection": ["detect", "bbox", "crop"],
            "augmentation": ["augment", "image_edit"],
            "annotation_pose": ["annotation", "pose2d", "pose3d", "keypoints"],
            "quality_cleanup": ["quality", "safety", "watermark", "rating"],
        }
        result = {}
        for group, caps in groups.items():
            result[group] = [m for m in models if set(m.get("capabilities") or []).intersection(caps) or str(m.get("kind") or "") in {group, group.rstrip('s')}]
        return {"groups": {k: len(v) for k, v in result.items()}, "models": result}

    def _model_runtime_kwargs(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(options or {})
        if self.settings:
            payload.setdefault("temperature", self.settings.model_temperature)
            payload.setdefault("max_new_tokens", self.settings.model_max_new_tokens)
            if self.settings.huggingface_token and "token" not in payload:
                payload["token"] = self.settings.huggingface_token
            if self.settings and hasattr(self.settings, "resolve_api_token") and "openrouter_token" not in payload:
                token = self.settings.resolve_api_token("openrouter")
                if token:
                    payload["openrouter_token"] = token
            elif self.settings.openrouter_token and "openrouter_token" not in payload:
                payload["openrouter_token"] = self.settings.openrouter_token
            if self.settings.openai_api_key and "openai_api_key" not in payload:
                payload["openai_api_key"] = self.settings.openai_api_key
            payload.setdefault("torch_dtype", getattr(self.settings, "default_model_dtype", "auto"))
            payload.setdefault("quantization", getattr(self.settings, "default_model_quantization", "none"))
        return payload

    def _lora_rule_context_from_options(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        opts = dict(options or {})
        if opts.get("include_lora_rule_context", True) is False:
            return {}
        target = str(opts.get("lora_target_model") or opts.get("target_model") or "sdxl")
        adapter = str(opts.get("lora_adapter_family") or opts.get("adapter_family") or opts.get("adapter_type") or "lora")
        goal = str(opts.get("lora_dataset_goal") or opts.get("dataset_goal") or "character")
        trigger = str(opts.get("lora_trigger_token") or opts.get("trigger_token") or "").strip()
        style_trigger = str(opts.get("lora_style_trigger_token") or opts.get("style_trigger_token") or "").strip()
        notes = str(opts.get("lora_additional_notes") or opts.get("additional_notes") or "").strip()
        result = {
            "source": "pipeline_prep_rule_presets",
            "target_model": target,
            "adapter_family": adapter,
            "dataset_goal": goal,
            "trigger_token": trigger,
            "style_trigger_token": style_trigger,
            "additional_notes": notes,
        }
        svc = getattr(self, "pipeline_prep", None)
        if svc and hasattr(svc, "rule_presets"):
            try:
                rules = svc.rule_presets(target, adapter, goal)
                result["rule_preset"] = rules
                result["prompt_contract"] = rules.get("prompt_contract")
                return result
            except Exception as exc:
                result["rule_error"] = str(exc)
        # Fallback keeps the assistant useful even if the pipeline tab service is
        # not available in a minimal/unit-test context.
        result["fallback_rules"] = {
            "preserve_source_valid_tags": True,
            "never_invent_unseen_attributes": True,
            "remove_tags_not_visually_present": True,
            "use_selected_tag_profile_aliases_and_implications": True,
            "character_goal": goal == "character",
            "style_goal": goal == "style",
            "caption_rule": "Apply LoRA/dataset rules after visual-prune pass; output keep/remove/add/final_tags JSON when editing tags.",
        }
        return result

    def _append_lora_rules_to_prompt(self, prompt: str, options: dict[str, Any] | None = None) -> str:
        rules = self._lora_rule_context_from_options(options)
        if not rules:
            return prompt
        try:
            rule_text = json.dumps(rules, ensure_ascii=False, indent=2, default=str)
        except Exception:
            rule_text = str(rules)
        return (
            str(prompt or "")
            + "\n\nDATASET / LORA RULE CONTEXT FROM THIS TOOL:\n"
            + rule_text[:18000]
            + "\n\nWhen pruning tags, first remove tags that are not visually/media-evidenced. Then apply the dataset/LoRA rules above. "
              "Return JSON fields where possible: keep_tags, remove_tags, add_tags, final_tags, caption, confidence, reason. "
              "Only mutate tags if the user/app enabled tag edits. Do not invent unseen attributes."
        )

    def _parse_tag_edit_directives(self, text: str, current_tags: list[str]) -> dict[str, list[str]]:
        def norm_values(values: Any) -> list[str]:
            out: list[str] = []
            seen: set[str] = set()
            if isinstance(values, str):
                values = re.split(r"[,;\n]+", values)
            for value in values or []:
                if isinstance(value, dict):
                    value = value.get("tag") or value.get("name") or value.get("label") or value.get("value")
                clean = re.sub(r"[^a-z0-9_:\-./]+", "", str(value or "").strip().lower().replace(" ", "_"))
                if clean and clean not in seen:
                    out.append(clean); seen.add(clean)
            return out
        raw = str(text or "").strip()
        payloads: list[Any] = []
        candidates = [raw]
        candidates.extend(re.findall(r"```(?:json)?\s*(.*?)```", raw, flags=re.I | re.S))
        b0, b1 = raw.find("{"), raw.rfind("}")
        if 0 <= b0 < b1:
            candidates.append(raw[b0:b1 + 1])
        a0, a1 = raw.find("["), raw.rfind("]")
        if 0 <= a0 < a1:
            candidates.append(raw[a0:a1 + 1])
        for cand in candidates:
            try:
                obj = json.loads(cand)
                payloads.append(obj)
            except Exception:
                pass
        directives = {"keep_tags": [], "remove_tags": [], "add_tags": [], "final_tags": [], "selected_existing_tags": []}
        key_aliases = {
            "keep_tags": ["keep_tags", "keep", "visible_tags", "present_tags", "valid_tags", "selected_existing_tags"],
            "remove_tags": ["remove_tags", "remove", "delete_tags", "prune_tags", "invalid_tags", "absent_tags", "wrong_tags"],
            "add_tags": ["add_tags", "add", "missing_tags", "new_tags"],
            "final_tags": ["final_tags", "set_tags", "tags_final", "approved_tags"],
            "selected_existing_tags": ["selected_existing_tags", "selected_tags", "matching_tags", "chosen_tags"],
        }
        def visit(obj: Any) -> None:
            if isinstance(obj, dict):
                for out_key, aliases in key_aliases.items():
                    for alias in aliases:
                        if alias in obj:
                            directives[out_key].extend(norm_values(obj.get(alias)))
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        visit(value)
            elif isinstance(obj, list):
                for value in obj:
                    visit(value)
        for payload in payloads:
            visit(payload)
        # Conservative prose fallback for lines like "remove: a, b".
        for line in raw.splitlines():
            m = re.match(r"\s*(remove|delete|prune|keep|add|final|set)\s*(?:tags?)?\s*[:=]\s*(.+)$", line, flags=re.I)
            if not m:
                continue
            key, body = m.group(1).lower(), m.group(2)
            target = "remove_tags" if key in {"remove", "delete", "prune"} else "keep_tags" if key == "keep" else "add_tags" if key == "add" else "final_tags"
            directives[target].extend(norm_values(body))
        current_set = {str(t).lower().replace(" ", "_"): str(t) for t in current_tags or []}
        for key, vals in list(directives.items()):
            seen: set[str] = set()
            cleaned: list[str] = []
            for tag in vals:
                tag_key = str(tag).lower().replace(" ", "_")
                chosen = current_set.get(tag_key, tag) if key != "add_tags" else tag
                if chosen and chosen not in seen:
                    cleaned.append(chosen); seen.add(chosen)
            directives[key] = cleaned
        return directives

    def _apply_assistant_tag_edit_directives(self, *, media_ids: list[int], response_text: str, model_name: str, options: dict[str, Any]) -> dict[str, Any]:
        mode = str(options.get("assistant_tag_edit_mode") or options.get("tag_edit_mode") or "auto").lower()
        allow_add = bool(options.get("assistant_tag_edit_allow_add", True))
        profile_key = str(options.get("tag_profile") or options.get("profile_key") or "e621")
        result = {"enabled": True, "mode": mode, "changed": 0, "media_ids": [], "by_media": {}}
        for media_id in [int(x) for x in media_ids or [] if int(x) > 0]:
            current = self.tags.get_tags(media_id)
            directives = self._parse_tag_edit_directives(response_text, current)
            updated = list(current)
            if directives.get("final_tags"):
                updated = list(directives["final_tags"])
            elif directives.get("keep_tags") and mode in {"auto", "keep_only", "prune", "remove"}:
                keep_set = set(directives["keep_tags"])
                updated = [tag for tag in current if tag in keep_set]
            elif directives.get("remove_tags"):
                remove_set = set(directives["remove_tags"])
                updated = [tag for tag in current if tag not in remove_set]
            elif directives.get("selected_existing_tags") and mode in {"remove", "prune"}:
                remove_set = set(directives["selected_existing_tags"])
                updated = [tag for tag in current if tag not in remove_set]
            if allow_add and directives.get("add_tags"):
                for tag in directives["add_tags"]:
                    if tag not in updated:
                        updated.append(tag)
            changed = updated != current
            if changed:
                self.tags.set_tags(media_id, updated, source=model_name, save_sidecar=True, profile_key=profile_key, order_strategy="retain")
                result["changed"] += 1
                result["media_ids"].append(media_id)
            result["by_media"][str(media_id)] = {"changed": changed, "before_count": len(current), "after_count": len(updated), "directives": directives}
        return result

    def _build_chat_context(self, request: ModelChatRequest) -> dict[str, Any]:
        dataset = None
        if request.dataset_id:
            dataset = self.db.query_one("SELECT * FROM datasets WHERE id=?", (request.dataset_id,))
        media_items = []
        ids = list(request.media_ids)
        if request.dataset_id and not ids and not request.use_selected_media:
            ids = [row["id"] for row in self.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1 ORDER BY id ASC LIMIT 12", (request.dataset_id,))]
        for media_id in ids[:24]:
            item = self.media.get(media_id)
            if item:
                row = item.model_dump()
                try:
                    preds = self.db.query(
                        "SELECT model_name, kind, payload_json, created_at FROM predictions WHERE media_id=? ORDER BY id DESC LIMIT 12",
                        (media_id,),
                    )
                    row["model_predictions"] = [dict(p) for p in preds]
                except Exception:
                    row["model_predictions"] = []
                try:
                    anns = self.db.query(
                        "SELECT label, annotation_type, confidence, bbox_json, mask_path, source, model_key FROM annotations WHERE media_id=? ORDER BY id DESC LIMIT 12",
                        (media_id,),
                    )
                    row["annotations"] = [dict(a) for a in anns]
                except Exception:
                    row["annotations"] = []
                media_items.append(row)
        metadata_items = []
        if getattr(request, "include_metadata_context", True):
            field_paths = getattr(request, "metadata_field_paths", []) or []
            include_raw = bool(getattr(request, "metadata_include_raw", False))
            try:
                metadata_items.extend(self.metadata_context_for_media(ids[:24], field_paths, include_raw=include_raw))
            except Exception as exc:
                metadata_items.append({"media_error": str(exc)})
            try:
                metadata_items.extend(self.metadata_context_for_paths(request.external_paths or [], field_paths, include_raw=include_raw))
            except Exception as exc:
                metadata_items.append({"external_path_error": str(exc)})
        lora_rules = self._lora_rule_context_from_options(getattr(request, "options", {}) or {})
        return {
            "dataset": dataset or {},
            "media": media_items,
            "generation_metadata": metadata_items,
            "external_paths": request.external_paths,
            "history": request.history,
            "dataset_curation_rules": lora_rules,
        }


def _extract_tags(text: str) -> list[str]:
    def normalize(raw: Any) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        values = raw if isinstance(raw, list) else [raw]
        for value in values or []:
            if isinstance(value, dict):
                nested = value.get("tag") or value.get("name") or value.get("label") or value.get("value")
                values2 = normalize(nested)
            else:
                parts = re.split(r"[,;\n]+", str(value or ""))
                values2 = [part.strip().lower().replace(" ", "_") for part in parts if part.strip()]
            for tag in values2:
                clean = re.sub(r"[^a-z0-9_:\-./]+", "", str(tag or "").strip().lower().replace(" ", "_"))
                if clean and clean not in seen:
                    out.append(clean)
                    seen.add(clean)
        return out

    raw_text = str(text or "").strip()
    if not raw_text:
        return []
    fenced = raw_text
    if fenced.startswith("```"):
        fenced = re.sub(r"^```(?:json)?\s*", "", fenced, flags=re.I).strip()
        fenced = re.sub(r"\s*```$", "", fenced).strip()
    json_candidates = [fenced]
    brace_start = fenced.find("{")
    brace_end = fenced.rfind("}")
    if 0 <= brace_start < brace_end:
        json_candidates.append(fenced[brace_start:brace_end + 1])
    bracket_start = fenced.find("[")
    bracket_end = fenced.rfind("]")
    if 0 <= bracket_start < bracket_end:
        json_candidates.append(fenced[bracket_start:bracket_end + 1])
    for candidate in json_candidates:
        try:
            payload = json.loads(candidate)
        except Exception:
            continue
        if isinstance(payload, dict):
            for key in ("tags", "selected_tags", "selected_existing_tags", "valid_tags", "matching_tags", "present_tags", "visible_tags", "chosen_tags", "add_tags", "remove_tags", "keep_tags", "labels", "selected"):
                if key in payload:
                    values = normalize(payload.get(key))
                    if values:
                        return values
        elif isinstance(payload, list):
            values = normalize(payload)
            if values:
                return values
    for line in raw_text.splitlines():
        lower = line.strip().lower()
        if lower.startswith(("tags:", "selected_tags:", "selected existing tags:", "selected_existing_tags:", "matching_tags:", "present_tags:", "valid_tags:")):
            raw = line.split(":", 1)[1]
            return normalize(raw)
    return []


def _extract_caption(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip().lower().startswith("caption:"):
            return line.split(":", 1)[1].strip()
    return None

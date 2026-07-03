from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from .gpu_service import detect_devices


CUDA_RE = re.compile(r"(?:cuda:)?(\d+)", re.IGNORECASE)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_memory_gb(value: Any) -> float | None:
    """Parse memory strings such as 23GiB, 22000MiB, 24GB, or 12.5."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    text = str(value).strip().lower().replace(" ", "")
    if not text:
        return None
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)(gib|gb|mib|mb)?$", text)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2) or "gb"
    if unit in {"mib", "mb"}:
        return number / 1024.0
    return number


def parse_device_ids(device: str | None = None, values: Any = None) -> list[int]:
    raw = values
    if raw is None:
        raw = device
    if raw is None:
        return []
    if isinstance(raw, str):
        text = raw.strip().lower()
        if text in {"", "auto", "cpu", "cuda"}:
            return []
        parts = re.split(r"[,;\s]+", text)
    else:
        parts = list(raw)
    ids: list[int] = []
    for part in parts:
        if part is None:
            continue
        match = CUDA_RE.search(str(part).strip().lower())
        if not match:
            continue
        idx = int(match.group(1))
        if idx not in ids:
            ids.append(idx)
    return ids


def _request_value(request: Any, key: str, default: Any = None) -> Any:
    if isinstance(request, dict):
        return request.get(key, default)
    return getattr(request, key, default)


def _request_options(request: Any) -> dict[str, Any]:
    return dict(_request_value(request, "options", {}) or {})


def _record_value(record: Any, key: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


class ModelPlacementManager:
    """Track loaded model placement and enforce approximate VRAM budgets.

    This is intentionally conservative rather than magical: it uses registry
    metadata (vram_gb), user-selected device ids, current nvidia-smi readings when
    available, and DCT's own loaded-model reservations.  The real framework still
    performs the final allocation, but this catches common mistakes before the
    user waits through a large model load.
    """

    def __init__(self, safety_margin_gb: float = 0.0, default_max_fraction: float = 1.0):
        self.safety_margin_gb = max(0.0, float(safety_margin_gb))
        self.default_max_fraction = max(0.1, min(1.0, float(default_max_fraction)))
        self._lock = RLock()
        self._placements: dict[str, dict[str, Any]] = {}

    def placements(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {name: dict(plan) for name, plan in self._placements.items()}

    def get(self, model_name: str | None) -> dict[str, Any] | None:
        with self._lock:
            plan = self._placements.get(str(model_name or ""))
            return dict(plan) if plan else None

    def release(self, model_name: str | None = None) -> dict[str, Any]:
        with self._lock:
            if model_name:
                removed = self._placements.pop(str(model_name), None)
                return {"released": [str(model_name)] if removed else []}
            names = list(self._placements)
            self._placements.clear()
            return {"released": names}

    def reserve(self, model_name: str, record: Any, request: Any) -> dict[str, Any]:
        plan = self.plan(model_name, record, request)
        if not plan.get("ok", False):
            raise RuntimeError(plan.get("error") or "Model placement does not fit available VRAM.")
        with self._lock:
            plan = dict(plan)
            plan["reserved_at"] = now_iso()
            self._placements[model_name] = plan
        return plan

    def plan(self, model_name: str, record: Any, request: Any) -> dict[str, Any]:
        model_name = str(model_name or _record_value(record, "name", "unknown-model"))
        device = str(_request_value(request, "device", "auto") or "auto").strip() or "auto"
        strategy = str(_request_value(request, "sharding_strategy", "none") or "none").strip().lower()
        quantization = str(_request_value(request, "quantization", "none") or "none").strip().lower()
        torch_dtype = str(_request_value(request, "torch_dtype", "auto") or "auto").strip().lower()
        runtime_engine = str(_request_value(request, "runtime_engine", "transformers") or "transformers")
        tensor_parallel_size = int(_request_value(request, "tensor_parallel_size", 1) or 1)
        explicit_device_ids = parse_device_ids(device, _request_value(request, "device_ids", None))
        if not explicit_device_ids:
            explicit_device_ids = parse_device_ids(device, None)
        max_memory = self._normalize_max_memory(_request_value(request, "max_memory", {}) or {})
        options = _request_options(request)
        required_gb = self.estimate_vram_gb(record, request)
        provider = str(_record_value(record, "provider", "") or "").lower()
        cloud = bool(_record_value(record, "cloud", False)) or provider in {"cloud", "openai", "openrouter", "anthropic"}
        builtin = provider in {"builtin"} or required_gb <= 0.0
        if cloud or builtin or device.lower() == "cpu":
            return {
                "ok": True,
                "model_name": model_name,
                "mode": "cloud" if cloud else ("cpu" if device.lower() == "cpu" else "no_vram_reservation"),
                "device": "cpu" if device.lower() == "cpu" else device,
                "device_ids": [],
                "sharding_strategy": strategy,
                "required_vram_gb": required_gb,
                "allocations": {},
                "warnings": [] if not options.get("force_gpu") else ["This model/provider does not require a DCT VRAM reservation."],
                "runtime_engine": runtime_engine,
                "tensor_parallel_size": tensor_parallel_size,
                "max_memory": max_memory,
            }

        snapshot = self.gpu_status(exclude_model=model_name)
        gpus = [d for d in snapshot.get("devices", []) if str(d.get("id", "")).startswith("cuda:")]
        gpu_by_id = {int(d["index"]): d for d in gpus if isinstance(d.get("index"), int)}
        if not gpus:
            if device.lower() == "auto" and not explicit_device_ids:
                return {
                    "ok": True,
                    "model_name": model_name,
                    "mode": "cpu_fallback_no_cuda_detected",
                    "device": "auto",
                    "device_ids": [],
                    "sharding_strategy": strategy,
                    "required_vram_gb": required_gb,
                    "allocations": {},
                    "warnings": ["No CUDA GPUs were detected by this environment. The adapter may fall back to CPU or fail if CPU execution is unsupported."],
                    "runtime_engine": runtime_engine,
                    "tensor_parallel_size": tensor_parallel_size,
                    "max_memory": max_memory,
                }
            return self._error_plan(model_name, required_gb, device, explicit_device_ids, strategy, "No CUDA GPUs were detected, but GPU placement was requested.")

        if not explicit_device_ids:
            explicit_device_ids = self._auto_select_gpus(required_gb, strategy, gpu_by_id, record, max_memory)
        missing = [idx for idx in explicit_device_ids if idx not in gpu_by_id]
        if missing:
            return self._error_plan(model_name, required_gb, device, explicit_device_ids, strategy, f"Requested GPU id(s) are not available: {missing}.")
        if not explicit_device_ids:
            return self._error_plan(model_name, required_gb, device, explicit_device_ids, strategy, "No GPU ids were selected and no GPU had enough available VRAM.")

        supports_sharding = bool(_record_value(record, "supports_sharding", False))
        min_gpus = int(_record_value(record, "min_gpus", 1) or 1)
        max_gpus_raw = _record_value(record, "max_gpus", None)
        max_gpus = int(max_gpus_raw) if max_gpus_raw not in (None, "") else None
        multi_requested = len(explicit_device_ids) > 1 or strategy in {"auto", "balanced", "balanced_low_0", "sequential", "custom"} or tensor_parallel_size > 1
        warnings: list[str] = []

        effective_ids = list(explicit_device_ids)
        if strategy == "none" and len(effective_ids) > 1:
            first = effective_ids[0]
            warnings.append(
                "Multiple GPUs were selected but sharding_strategy is 'none'; only the first selected GPU will be used. "
                "Choose auto/balanced/sequential to shard the model."
            )
            effective_ids = [first]
            multi_requested = False
        if multi_requested and not supports_sharding and strategy != "custom":
            return self._error_plan(
                model_name,
                required_gb,
                device,
                explicit_device_ids,
                strategy,
                f"{_record_value(record, 'label', model_name)} is not marked as sharding-capable. Use one GPU, a custom device_map, or unload/reconfigure the adapter metadata.",
            )
        if multi_requested and len(effective_ids) < min_gpus:
            return self._error_plan(model_name, required_gb, device, effective_ids, strategy, f"This model requires at least {min_gpus} GPU(s); selected {len(effective_ids)}.")
        if multi_requested and max_gpus and len(effective_ids) > max_gpus:
            return self._error_plan(model_name, required_gb, device, effective_ids, strategy, f"This model supports at most {max_gpus} GPU(s); selected {len(effective_ids)}.")

        capacity = {idx: self._available_capacity_gb(gpu_by_id[idx], max_memory.get(idx)) for idx in effective_ids}
        selected_total = sum(capacity.values())
        if required_gb > selected_total + 1e-6:
            return self._error_plan(
                model_name,
                required_gb,
                device,
                effective_ids,
                strategy,
                (
                    f"Estimated VRAM requirement is {required_gb:.2f} GB, but selected GPU(s) have only "
                    f"{selected_total:.2f} GB available after current/reserved usage and safety margin. "
                    "Unload another model, select more GPUs, use 8-bit/4-bit quantization, or lower max_memory."
                ),
                snapshot=snapshot,
            )
        allocations = self._allocate(required_gb, effective_ids, capacity, strategy)
        selected_device = self._device_string(device, effective_ids, strategy)
        generated_max_memory = dict(max_memory)
        if multi_requested and not generated_max_memory:
            for idx in effective_ids:
                cap = max(1.0, math.floor(capacity[idx] * 10) / 10)
                generated_max_memory[idx] = f"{cap:.1f}GiB"
        return {
            "ok": True,
            "model_name": model_name,
            "mode": "multi_gpu" if multi_requested else "single_gpu",
            "device": selected_device,
            "device_ids": effective_ids,
            "requested_device_ids": explicit_device_ids,
            "sharding_strategy": strategy,
            "required_vram_gb": round(required_gb, 3),
            "allocations": {str(k): round(v, 3) for k, v in allocations.items()},
            "selected_available_vram_gb": round(selected_total, 3),
            "selected_total_vram_gb": round(sum(float(gpu_by_id[i].get("total_memory_gb") or 0) for i in effective_ids), 3),
            "max_memory": generated_max_memory,
            "quantization": quantization,
            "torch_dtype": torch_dtype,
            "runtime_engine": runtime_engine,
            "tensor_parallel_size": tensor_parallel_size,
            "warnings": warnings,
            "snapshot": snapshot,
        }

    def estimate_vram_gb(self, record: Any, request: Any) -> float:
        options = _request_options(request)
        override = options.get("estimated_vram_gb", options.get("vram_gb_override"))
        parsed_override = parse_memory_gb(override)
        if parsed_override is not None:
            return round(parsed_override, 3)
        base = _record_value(record, "vram_gb", None)
        try:
            required = float(base or 0.0)
        except Exception:
            required = 0.0
        if required <= 0:
            return 0.0
        quantization = str(_request_value(request, "quantization", "none") or "none").lower()
        dtype = str(_request_value(request, "torch_dtype", "auto") or "auto").lower().replace("torch.", "")
        factor = 1.0
        if quantization == "8bit":
            factor *= 0.62
        elif quantization == "4bit":
            factor *= 0.42
        if dtype in {"float32", "fp32"} and quantization == "none":
            factor *= 1.85
        elif dtype in {"float16", "fp16", "bfloat16", "bf16"}:
            factor *= 1.0
        # Add a small activation/runtime overhead so the planner is not exact-to-
        # the-byte optimistic.  Large model records already include broad VRAM
        # estimates, so keep the overhead capped.
        overhead = min(2.0, max(0.25, required * 0.04))
        return round(max(0.0, required * factor + overhead), 3)

    def gpu_status(self, exclude_model: str | None = None) -> dict[str, Any]:
        detected = detect_devices()
        with self._lock:
            placements = {name: dict(plan) for name, plan in self._placements.items() if name != exclude_model}
        allocations_by_gpu: dict[int, float] = {}
        models_by_gpu: dict[int, list[dict[str, Any]]] = {}
        for name, plan in placements.items():
            for raw_idx, amount in dict(plan.get("allocations") or {}).items():
                try:
                    idx = int(raw_idx)
                    gb = float(amount or 0.0)
                except Exception:
                    continue
                allocations_by_gpu[idx] = allocations_by_gpu.get(idx, 0.0) + gb
                models_by_gpu.setdefault(idx, []).append({"model_name": name, "reserved_vram_gb": round(gb, 3), "mode": plan.get("mode")})
        devices: list[dict[str, Any]] = []
        for d in detected.get("devices", []):
            item = dict(d)
            if not str(item.get("id", "")).startswith("cuda:"):
                devices.append(item)
                continue
            idx = item.get("index")
            if not isinstance(idx, int):
                parsed = parse_device_ids(item.get("id"))
                idx = parsed[0] if parsed else None
                item["index"] = idx
            if idx is None:
                devices.append(item)
                continue
            total = float(item.get("total_memory_gb") or 0.0)
            observed_used = item.get("used_memory_gb")
            if observed_used is None and item.get("free_memory_gb") is not None:
                observed_used = max(0.0, total - float(item.get("free_memory_gb") or 0.0))
            observed_used = float(observed_used or 0.0)
            reserved = float(allocations_by_gpu.get(idx, 0.0))
            accounted_used = max(observed_used, reserved)
            usable_total = max(0.0, total * self.default_max_fraction - self.safety_margin_gb)
            available = max(0.0, min(total - accounted_used - self.safety_margin_gb, usable_total - reserved))
            item.update(
                {
                    "index": idx,
                    "dct_reserved_vram_gb": round(reserved, 3),
                    "observed_used_memory_gb": round(observed_used, 3),
                    "accounted_used_memory_gb": round(accounted_used, 3),
                    "available_for_new_models_gb": round(available, 3),
                    "safety_margin_gb": self.safety_margin_gb,
                    "loaded_models": models_by_gpu.get(idx, []),
                }
            )
            devices.append(item)
        return {
            "detected": detected,
            "devices": devices,
            "placements": placements,
            "safety_margin_gb": self.safety_margin_gb,
            "default_max_fraction": self.default_max_fraction,
        }

    def _normalize_max_memory(self, value: dict[str, Any]) -> dict[int, str]:
        out: dict[int, str] = {}
        if not isinstance(value, dict):
            return out
        for raw_key, raw_value in value.items():
            ids = parse_device_ids(str(raw_key))
            if not ids:
                try:
                    ids = [int(raw_key)]
                except Exception:
                    continue
            parsed = parse_memory_gb(raw_value)
            if parsed is None:
                continue
            out[ids[0]] = f"{parsed:.2f}GiB"
        return out

    def _available_capacity_gb(self, gpu: dict[str, Any], max_memory: str | None = None) -> float:
        avail = float(gpu.get("available_for_new_models_gb") or 0.0)
        parsed = parse_memory_gb(max_memory)
        if parsed is not None:
            return max(0.0, min(avail, parsed))
        return max(0.0, avail)

    def _auto_select_gpus(self, required_gb: float, strategy: str, gpu_by_id: dict[int, dict[str, Any]], record: Any, max_memory: dict[int, str]) -> list[int]:
        candidates = sorted(
            ((idx, self._available_capacity_gb(gpu, max_memory.get(idx))) for idx, gpu in gpu_by_id.items()),
            key=lambda item: item[1],
            reverse=True,
        )
        if strategy == "none":
            for idx, avail in candidates:
                if avail >= required_gb:
                    return [idx]
            # Select the largest GPU anyway so the error message is specific.
            return [candidates[0][0]] if candidates else []
        max_gpus_raw = _record_value(record, "max_gpus", None)
        max_gpus = int(max_gpus_raw) if max_gpus_raw not in (None, "") else len(candidates)
        chosen: list[int] = []
        total = 0.0
        for idx, avail in candidates[:max_gpus]:
            chosen.append(idx)
            total += avail
            if total >= required_gb:
                break
        return sorted(chosen)

    def _allocate(self, required_gb: float, ids: list[int], capacity: dict[int, float], strategy: str) -> dict[int, float]:
        if required_gb <= 0:
            return {}
        if len(ids) == 1 or strategy == "none":
            return {ids[0]: required_gb}
        remaining = required_gb
        allocations = {idx: 0.0 for idx in ids}
        if strategy in {"balanced", "balanced_low_0", "auto", "custom"}:
            # Fill all GPUs toward a common target, respecting lower-capacity
            # cards first.  This keeps reservations close to balanced without a
            # complex bin-packing dependency.
            active = list(ids)
            while remaining > 1e-6 and active:
                share = remaining / len(active)
                next_active: list[int] = []
                for idx in active:
                    free = max(0.0, capacity[idx] - allocations[idx])
                    add = min(share, free, remaining)
                    allocations[idx] += add
                    remaining -= add
                    if capacity[idx] - allocations[idx] > 1e-6:
                        next_active.append(idx)
                if len(next_active) == len(active) and share <= 1e-6:
                    break
                active = next_active
        else:
            for idx in ids:
                add = min(remaining, capacity[idx])
                allocations[idx] += add
                remaining -= add
                if remaining <= 1e-6:
                    break
        return {idx: value for idx, value in allocations.items() if value > 1e-6}

    def _device_string(self, device: str, ids: list[int], strategy: str) -> str:
        if device.lower() not in {"", "auto"} and not device.lower().startswith("cuda"):
            return device
        if not ids:
            return device or "auto"
        if strategy == "none" or len(ids) == 1:
            return f"cuda:{ids[0]}"
        return ",".join(f"cuda:{idx}" for idx in ids)

    def _error_plan(
        self,
        model_name: str,
        required_gb: float,
        device: str,
        device_ids: list[int],
        strategy: str,
        message: str,
        *,
        snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "model_name": model_name,
            "mode": "invalid",
            "device": device,
            "device_ids": device_ids,
            "sharding_strategy": strategy,
            "required_vram_gb": round(required_gb, 3),
            "allocations": {},
            "error": message,
            "warnings": [],
            "snapshot": snapshot,
        }

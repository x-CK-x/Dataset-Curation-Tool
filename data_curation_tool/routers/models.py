from __future__ import annotations

import traceback
import json
import shlex
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx
from ..schemas import CustomModelRequest, ModelChatRequest, ModelDownloadRequest, ModelLoadRequest, ModelRunRequest, ModelTagSelectionRequest

router = APIRouter(prefix="/models", tags=["models"])


class AssistantConfigUpdate(BaseModel):
    assistant_model_name: str | None = None
    orchestrator_model_name: str | None = None
    assistant_model_auto_load: bool | None = None
    assistant_allow_orchestration: bool | None = None


class ExternalModelRootsUpdate(BaseModel):
    roots: list[str] = Field(default_factory=list)


class OpenRouterVideoGenerationRequest(BaseModel):
    model_name: str = "openrouter-xai-grok-imagine-video"
    prompt: str
    token_profile: str | None = None
    model_id: str | None = None
    duration: int | None = None
    resolution: str | None = None
    aspect_ratio: str | None = None
    size: str | None = None
    frame_images: list[dict] = Field(default_factory=list)
    input_references: list[dict] = Field(default_factory=list)
    provider_options: dict = Field(default_factory=dict)
    timeout: int = 120




class LingBotCommandRequest(BaseModel):
    model_name: str
    runtime_dir: str = ""
    mode: str = "t2v"
    prompt_json: str = "prompt.json"
    negative_prompt_json: str | None = "negative.json"
    output: str = "outputs/base.mp4"
    refiner_output: str | None = "outputs/refined.mp4"
    backend: str = "diffusers"
    height: int = 480
    width: int = 832
    fps: int = 24
    steps: int = 40
    run_refiner: bool | None = None
    extra: dict = Field(default_factory=dict)
    timeout_seconds: int = 0


def _command_line(cmd: list[str]) -> str:
    try:
        return shlex.join([str(x) for x in cmd])
    except Exception:
        return " ".join(str(x) for x in cmd)


def _lingbot_runtime_cwd(payload: LingBotCommandRequest, request_context) -> str:
    candidates: list[Path] = []
    if payload.runtime_dir:
        candidates.append(Path(payload.runtime_dir).expanduser())
    for root in getattr(request_context.registry, "external_model_roots", []) or []:
        candidates.extend([Path(root), Path(root) / "lingbot-video", Path(root) / "LingBot-Video"] )
    candidates.extend([
        request_context.paths.models / "lingbot-video-runtime-repo",
        request_context.paths.models / "lingbot-video",
        request_context.paths.root / "lingbot-video",
    ])
    for candidate in candidates:
        try:
            if (candidate / "scripts" / "inference.py").exists():
                return str(candidate.resolve(strict=False))
        except Exception:
            continue
    if payload.runtime_dir:
        raise ValueError(f"LingBot runtime_dir does not contain scripts/inference.py: {payload.runtime_dir}")
    raise ValueError("Set runtime_dir to a local LingBot-Video repository containing scripts/inference.py before launching inference.")


def _lingbot_command_payload(payload: LingBotCommandRequest, request_context) -> tuple[object, list[str]]:
    adapter = request_context.registry._loaded.get(payload.model_name) if hasattr(request_context.registry, "_loaded") else None
    if adapter is None:
        record = request_context.registry.get_record(payload.model_name)
        adapter = getattr(record, "adapter", None)
    if adapter is None or not hasattr(adapter, "build_command"):
        raise ValueError(f"{payload.model_name} is not a LingBot-Video runtime row.")
    cmd = adapter.build_command(
        mode=payload.mode,
        prompt_json=payload.prompt_json,
        negative_prompt_json=payload.negative_prompt_json,
        output=payload.output,
        refiner_output=payload.refiner_output,
        backend=payload.backend,
        height=payload.height,
        width=payload.width,
        fps=payload.fps,
        steps=payload.steps,
        run_refiner=payload.run_refiner,
        extra=payload.extra,
    )
    return adapter, cmd


class CustomModelCreate(BaseModel):
    name: str | None = None
    label: str
    category: str = ""
    provider: str | None = None
    repo_id: str | None = None
    direct_url: str | None = None
    local_path: str | None = None
    local_source_path: str | None = None
    source_local_path: str | None = None
    description: str | None = None
    capabilities: list[str] | None = None
    size_gb: float | None = None
    vram_gb: float | None = None
    parameter_count: str | None = None
    precision: str | None = None
    download_supported: bool | None = None
    recommended_backend: str | None = None
    modality: str | None = None
    supports_sharding: bool | None = None
    min_gpus: int | None = None
    max_gpus: int | None = None
    filename: str | None = None
    requirements: list[str] | None = None


class OrchestratorRunPlanRequest(BaseModel):
    orchestrator_model_name: str | None = None
    target_model_names: list[str] = Field(default_factory=list)
    model_names: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    context: str | None = None
    goal: str | None = None
    prompt: str | None = None
    require_user_approval: bool = True
    media_ids: list[int] = Field(default_factory=list)
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: str = "none"
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: str = "none"
    runtime_engine: str = "transformers"
    tensor_parallel_size: int = 1
    max_models: int = 12


class OrchestratorQueueRunsRequest(BaseModel):
    orchestrator_model_name: str | None = None
    user_approved: bool = False
    runs: list[ModelRunRequest] = Field(default_factory=list)


class ModelQueueRunsRequest(BaseModel):
    runs: list[ModelRunRequest] = Field(default_factory=list)
    queue_source: str = "user"
    user_approved: bool = True
    remove_completed_from_active_queue: bool = True


@router.get("")
def list_models(request: Request, force: bool = False):
    return ctx(request).models.list_models(force=force)


@router.post("/custom")
def add_custom_model(payload: CustomModelCreate, request: Request):
    c = ctx(request)
    try:
        row = c.models.add_custom_model(payload.model_dump(exclude_none=True))
        c.settings.save(c.paths.settings)
        try:
            catalog = c.paths.runtime / "custom_models.json"
            catalog.parent.mkdir(parents=True, exist_ok=True)
            catalog.write_text(json.dumps({"version": 1, "models": getattr(c.settings, "custom_models", []) or []}, indent=2), encoding="utf-8")
        except Exception:
            pass
        c.models.lifecycle.ensure_model(row.get("name"))
        return {"ok": True, "model": row, "models": c.models.list_models()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/custom/{model_name}")
def delete_custom_model(model_name: str, request: Request):
    c = ctx(request)
    try:
        result = c.models.delete_custom_model(model_name)
        c.settings.save(c.paths.settings)
        try:
            catalog = c.paths.runtime / "custom_models.json"
            catalog.parent.mkdir(parents=True, exist_ok=True)
            catalog.write_text(json.dumps({"version": 1, "models": getattr(c.settings, "custom_models", []) or []}, indent=2), encoding="utf-8")
        except Exception:
            pass
        return {"ok": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc



@router.get("/status")
def model_lifecycle_status(request: Request, model_name: str | None = None):
    return ctx(request).models.lifecycle_status(model_name)


@router.get("/status/{model_name}")
def model_lifecycle_status_for_model(model_name: str, request: Request):
    return ctx(request).models.lifecycle_status(model_name)


@router.get("/resource-status")
def model_resource_status(request: Request):
    return ctx(request).models.model_resource_status()


@router.get("/runtime-planning-context")
def model_runtime_planning_context(request: Request, limit: int = 250):
    return ctx(request).models.model_runtime_planning_context(limit=limit)


@router.post("/rescan")
def rescan_local_models(request: Request):
    c = ctx(request)
    c.models.invalidate_model_catalog_cache()
    return c.models.reconcile_local_assets()


@router.post("/reconcile/{model_name}")
def reconcile_single_model(model_name: str, request: Request, job_id: int | None = None):
    c = ctx(request)
    try:
        return c.models.reconcile_model_local_asset(model_name, job_id=job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/external-roots")
def get_external_model_roots(request: Request):
    c = ctx(request)
    roots = list(getattr(c.settings, "external_model_roots", []) or [])
    return {"roots": roots, "count": len(roots), "models_root": str(c.paths.models)}


@router.put("/external-roots")
def update_external_model_roots(payload: ExternalModelRootsUpdate, request: Request):
    c = ctx(request)
    roots = []
    seen = set()
    for raw in payload.roots or []:
        text = str(raw or "").strip().strip('"')
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key); roots.append(text)
    c.settings.external_model_roots = roots
    c.db.set_setting("external_model_roots", roots)
    c.settings.save(c.paths.settings)
    try:
        c.registry.set_external_model_roots(roots)
    except Exception:
        pass
    reconciliation = c.models.reconcile_local_assets()
    return {"ok": True, "roots": roots, "count": len(roots), "reconciliation": reconciliation}


@router.get("/gpu-status")
def model_gpu_status(request: Request):
    return ctx(request).models.placement_summary()


@router.get("/placement")
def model_placement_summary(request: Request):
    return ctx(request).models.placement_summary()


@router.post("/placement/plan")
def model_placement_plan(payload: ModelLoadRequest, request: Request):
    return ctx(request).models.placement_plan(payload, strict=False)


@router.post("/placement-plan")
def model_placement_plan_alias(payload: ModelLoadRequest, request: Request):
    return ctx(request).models.placement_plan(payload, strict=False)




@router.get("/assistant-config")
def get_assistant_config(request: Request):
    return ctx(request).models.assistant_config()


@router.put("/assistant-config")
def update_assistant_config(payload: AssistantConfigUpdate, request: Request):
    c = ctx(request)
    try:
        if payload.assistant_model_name is not None:
            c.settings.assistant_model_name = c.models.validate_assistant_model_name(payload.assistant_model_name)
            c.db.set_setting("assistant_model_name", c.settings.assistant_model_name)
        if payload.orchestrator_model_name is not None:
            c.settings.orchestrator_model_name = c.models.validate_assistant_model_name(payload.orchestrator_model_name)
            c.db.set_setting("orchestrator_model_name", c.settings.orchestrator_model_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload.assistant_model_auto_load is not None:
        c.settings.assistant_model_auto_load = bool(payload.assistant_model_auto_load)
        c.db.set_setting("assistant_model_auto_load", c.settings.assistant_model_auto_load)
    if payload.assistant_allow_orchestration is not None:
        c.settings.assistant_allow_orchestration = bool(payload.assistant_allow_orchestration)
        c.db.set_setting("assistant_allow_orchestration", c.settings.assistant_allow_orchestration)
    c.settings.save(c.paths.settings)
    return c.models.assistant_config()


def _orchestrator_model_candidates(c, payload: OrchestratorRunPlanRequest) -> list[dict]:
    requested = [str(x).strip() for x in ((payload.target_model_names or []) + (payload.model_names or [])) if str(x).strip()]
    rows = c.models.list_models()
    by_name = {row.get("name"): row for row in rows}
    if requested:
        return [by_name[name] for name in requested if name in by_name]
    task_words = {str(x).lower().strip() for x in (payload.tasks or []) if str(x).strip()}
    if not task_words:
        task_words = {"tag", "caption", "classify", "rating", "vlm"}
    selected = []
    for row in rows:
        caps = {str(x).lower() for x in (row.get("capabilities") or [])}
        kind = str(row.get("kind") or "").lower()
        if kind in {"assistant", "external_image_tool", "3d_tool"}:
            continue
        if task_words.intersection(caps) or kind in task_words or ("vlm" in task_words and ("vlm" in caps or kind == "vlm")):
            selected.append(row)
    return selected[: max(1, min(64, int(payload.max_models or 12)))]




@router.post("/lingbot/command")
def lingbot_command(payload: LingBotCommandRequest, request: Request):
    c = ctx(request)
    try:
        _adapter, cmd = _lingbot_command_payload(payload, c)
        cwd = None
        if payload.runtime_dir:
            cwd = _lingbot_runtime_cwd(payload, c)
        return {"ok": True, "model_name": payload.model_name, "runtime_dir": cwd, "command": cmd, "command_line": _command_line(cmd)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/lingbot/run")
def lingbot_run(payload: LingBotCommandRequest, request: Request):
    c = ctx(request)
    try:
        _adapter, cmd = _lingbot_command_payload(payload, c)
        cwd = _lingbot_runtime_cwd(payload, c)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    params = payload.model_dump()
    params["runtime_dir"] = cwd
    params["command"] = cmd

    def task(progress):
        progress(0.05, "Launching LingBot-Video inference command")
        timeout = int(payload.timeout_seconds or 0) or None
        proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        output = proc.stdout or ""
        progress(0.95, "LingBot-Video command finished")
        result = {"returncode": proc.returncode, "runtime_dir": cwd, "command": cmd, "command_line": _command_line(cmd), "output_tail": output[-12000:]}
        if proc.returncode != 0:
            raise RuntimeError(f"LingBot-Video command failed with exit code {proc.returncode}.\n{output[-12000:]}")
        return result

    job_id = c.jobs.submit("lingbot_video_inference", params, task)
    return {"ok": True, "job_id": job_id, "model_name": payload.model_name, "runtime_dir": cwd, "command": cmd, "command_line": _command_line(cmd)}


@router.post("/orchestrator/plan")
@router.post("/orchestrator/run-plan")
def orchestrator_run_plan(payload: OrchestratorRunPlanRequest, request: Request):
    c = ctx(request)
    try:
        orchestrator = c.models.resolve_assistant_model_name(payload.orchestrator_model_name, purpose="orchestrator")
        orchestrator = c.models.validate_assistant_model_name(orchestrator)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    allow = bool(getattr(c.settings, "assistant_allow_orchestration", True))
    targets = _orchestrator_model_candidates(c, payload)
    recommendations = []
    default_ids = payload.device_ids or list(getattr(c.settings, "default_model_device_ids", []) or [])
    for row in targets:
        name = str(row.get("name") or "")
        provider = str(row.get("provider") or "")
        is_cloud = bool(row.get("cloud")) or provider in {"openai", "openrouter", "anthropic", "cloud"}
        if is_cloud or provider == "builtin":
            recommendations.append({
                "model_name": name,
                "label": row.get("label") or name,
                "kind": row.get("kind"),
                "provider": provider,
                "can_load": True,
                "queue_supported": True,
                "recommendation": "API/built-in model: no local GPU reservation needed.",
                "placement": {"device_ids": [], "estimated_vram_gb": 0},
                "warnings": [],
                "errors": [],
            })
            continue
        if payload.device_ids or payload.max_memory or payload.sharding_strategy != "none" or payload.torch_dtype != "auto" or payload.quantization != "none":
            load_req = ModelLoadRequest(
                model_name=name,
                device="auto",
                device_ids=default_ids,
                sharding_strategy=payload.sharding_strategy if payload.sharding_strategy in {"none", "auto", "balanced", "balanced_low_0", "sequential", "custom"} else "none",
                max_memory=payload.max_memory or {},
                torch_dtype=payload.torch_dtype or "auto",
                quantization=payload.quantization if payload.quantization in {"none", "8bit", "4bit"} else "none",
                runtime_engine=payload.runtime_engine if payload.runtime_engine in {"transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"} else "transformers",
                tensor_parallel_size=max(1, int(payload.tensor_parallel_size or 1)),
                options={},
            )
        else:
            load_req = c.models._recommended_request_for_model(name)
        plan = c.models.placement_plan(load_req, strict=False)
        plan["placement_request"] = load_req.model_dump()
        ids = plan.get("selected_device_ids") or plan.get("device_ids") or default_ids or []
        if row.get("supports_sharding") and row.get("vram_gb") and len(ids) < int(row.get("min_gpus") or 1):
            rec = f"Select at least {int(row.get('min_gpus') or 1)} GPU(s) or use quantization/sharding for this model."
        elif plan.get("can_load") is False:
            rec = "Unload other models, choose more GPUs, enable sharding, or lower dtype/quantization before queueing."
        elif ids:
            rec = "Recommended local placement: " + ", ".join(f"cuda:{x}" for x in ids)
        else:
            rec = "CPU/local fallback or no CUDA device selected."
        recommendations.append({
            "model_name": name,
            "label": row.get("label") or name,
            "kind": row.get("kind"),
            "provider": provider,
            "can_load": bool(plan.get("can_load", True)),
            "queue_supported": True,
            "recommendation": rec,
            "placement": plan,
            "placement_request": load_req.model_dump(),
            "warnings": plan.get("warnings") or [],
            "errors": plan.get("errors") or [],
        })
    return {
        "orchestrator_model_name": orchestrator,
        "assistant_allow_orchestration": allow,
        "user_approval_required": bool(payload.require_user_approval),
        "context": payload.context or "assistant/orchestrator",
        "media_ids": payload.media_ids,
        "recommendations": recommendations,
        "runtime_planning_context": c.models.model_runtime_planning_context(limit=120),
        "resource_status": c.models.model_resource_status(),
        "message": "Review this plan before queueing. No model runs were started by this endpoint.",
    }


@router.post("/orchestrator/queue-runs")
def orchestrator_queue_runs(payload: OrchestratorQueueRunsRequest, request: Request):
    c = ctx(request)
    try:
        orchestrator = c.models.resolve_assistant_model_name(payload.orchestrator_model_name, purpose="orchestrator")
        orchestrator = c.models.validate_assistant_model_name(orchestrator)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not bool(getattr(c.settings, "assistant_allow_orchestration", True)):
        raise HTTPException(status_code=403, detail="Assistant/orchestrator model runs are disabled in settings.")
    if not payload.user_approved:
        raise HTTPException(status_code=400, detail="User approval is required before the orchestrator queues model runs.")
    if not payload.runs:
        raise HTTPException(status_code=400, detail="No model runs were requested.")
    queued = []
    for run in payload.runs:
        c.models.lifecycle.update(run.model_name, "inference", state="queued", progress=0.0, message=f"Inference queued by orchestrator {orchestrator}")

        def task(progress, job_id: int, _run=run):
            return c.models.run(_run, job_id, progress)

        job_id = c.jobs.submit_with_job_id("model_inference", {**run.model_dump(), "orchestrator_model_name": orchestrator}, task)
        c.models.lifecycle.update(run.model_name, "inference", job_id=job_id)
        queued.append({"job_id": job_id, "model_name": run.model_name, "task": run.task})
    return {"orchestrator_model_name": orchestrator, "queued": queued, "count": len(queued), "runtime_resources": c.models.model_resource_status()}


@router.post("/queue-runs")
def queue_model_runs(payload: ModelQueueRunsRequest, request: Request):
    c = ctx(request)
    if not payload.runs:
        raise HTTPException(status_code=400, detail="No model runs were requested.")
    queued = []
    for run in payload.runs:
        c.models.lifecycle.update(run.model_name, "inference", state="queued", progress=0.0, message=f"Inference queued from {payload.queue_source}")

        def task(progress, job_id: int, _run=run):
            return c.models.run(_run, job_id, progress)

        params = {**run.model_dump(), "queue_source": payload.queue_source, "user_approved": payload.user_approved}
        job_id = c.jobs.submit_with_job_id("model_inference", params, task)
        c.models.lifecycle.update(run.model_name, "inference", job_id=job_id)
        queued.append({"job_id": job_id, "model_name": run.model_name, "task": run.task, "queue_source": payload.queue_source})
    return {"queued": queued, "count": len(queued), "queue_source": payload.queue_source}


@router.post("/run")
def run_model(payload: ModelRunRequest, request: Request):
    c = ctx(request)
    c.models.lifecycle.update(payload.model_name, "inference", state="queued", progress=0.0, message="Inference queued")

    def task(progress, job_id: int):
        return c.models.run(payload, job_id, progress)

    job_id = c.jobs.submit_with_job_id("model_inference", payload.model_dump(), task)
    c.models.lifecycle.update(payload.model_name, "inference", job_id=job_id)
    return {"job_id": job_id, "status": "queued"}


@router.post("/load")
def load_model(payload: ModelLoadRequest, request: Request):
    c = ctx(request)
    if c.models.is_model_loaded(payload.model_name):
        result = c.models.load(payload)
        return {"job_id": None, "status": "completed", "already_loaded": True, "result": result}
    c.models.lifecycle.update(payload.model_name, "load", state="queued", progress=0.0, message="Model load queued")

    def task(progress, job_id: int):
        return c.models.load(payload, progress=progress, job_id=job_id)

    job_id = c.jobs.submit_with_job_id("model_load", payload.model_dump(), task)
    c.models.lifecycle.update(payload.model_name, "load", job_id=job_id)
    return {"job_id": job_id, "status": "queued"}


@router.post("/chat")
def chat_with_model(payload: ModelChatRequest, request: Request):
    return ctx(request).models.chat(payload)


@router.post("/openrouter/video")
def generate_openrouter_video(payload: OpenRouterVideoGenerationRequest, request: Request):
    c = ctx(request)
    try:
        record = c.registry.get_record(payload.model_name)
        adapter = record.adapter
        if not hasattr(adapter, "generate_video"):
            raise ValueError(f"Selected model does not expose video generation: {payload.model_name}")
        token = c.settings.resolve_api_token("openrouter", payload.token_profile) if hasattr(c.settings, "resolve_api_token") else c.settings.openrouter_token
        result = adapter.generate_video(
            payload.prompt,
            openrouter_token=token,
            model_id=payload.model_id or record.api_model_id or record.repo_id,
            duration=payload.duration,
            resolution=payload.resolution,
            aspect_ratio=payload.aspect_ratio,
            size=payload.size,
            frame_images=payload.frame_images,
            input_references=payload.input_references,
            provider_options=payload.provider_options,
            timeout=payload.timeout,
        )
        return {"model_name": payload.model_name, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OpenRouter video generation request failed: {exc}") from exc


@router.post("/select-tags")
def select_tags_with_model(payload: ModelTagSelectionRequest, request: Request):
    try:
        return ctx(request).models.select_tags(payload)
    except Exception as exc:
        detail = (
            f"Tag-selection inference failed for model={payload.model_name!r}, "
            f"media_ids={payload.media_ids!r}, operation={payload.operation!r}. "
            f"Error: {exc}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail=detail) from exc


@router.get("/chat/conversations")
def list_chat_conversations(request: Request, limit: int = 100):
    return ctx(request).models.list_conversations(limit)


@router.get("/chat/conversations/{conversation_id}")
def get_chat_conversation(conversation_id: int, request: Request):
    return ctx(request).models.get_conversation(conversation_id)


@router.delete("/chat/conversations/{conversation_id}")
def archive_chat_conversation(conversation_id: int, request: Request):
    return ctx(request).models.archive_conversation(conversation_id)


@router.put("/chat/conversations/{conversation_id}/state")
def save_chat_conversation_state(conversation_id: int, payload: dict, request: Request):
    try:
        return ctx(request).models.save_conversation_state(conversation_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/chat/conversations/{conversation_id}/messages/{message_id}")
def edit_chat_message(conversation_id: int, message_id: int, payload: dict, request: Request):
    try:
        return ctx(request).models.edit_conversation_message(
            conversation_id,
            message_id,
            str(payload.get("content") or ""),
            truncate_after=bool(payload.get("truncate_after", True)),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.delete("/chat/conversations/{conversation_id}/messages/{message_id}")
def delete_chat_message(conversation_id: int, message_id: int, request: Request, delete_following: bool = False):
    try:
        return ctx(request).models.delete_conversation_message(conversation_id, message_id, delete_following=delete_following)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat/conversations/{conversation_id}/clear")
def clear_chat_conversation(conversation_id: int, payload: dict, request: Request):
    try:
        return ctx(request).models.clear_conversation(
            conversation_id,
            clear_messages=bool(payload.get("clear_messages", True)),
            clear_memory=bool(payload.get("clear_memory", True)),
            keep_state=bool(payload.get("keep_state", True)),
            reset_context=bool(payload.get("reset_context", True)),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat/conversations/fork")
def fork_chat_conversation(payload: dict, request: Request):
    return ctx(request).models.fork_conversation(int(payload.get("message_id") or 0), title=payload.get("title"))


@router.get("/runtime-audit")
def runtime_audit(request: Request):
    return ctx(request).registry.runtime_audit()


@router.post("/download")
def download_model(payload: ModelDownloadRequest, request: Request):
    c = ctx(request)
    status_model_name = payload.model_name or payload.repo_id or payload.local_dir or "custom-model-download"
    c.models.lifecycle.update(status_model_name, "download", state="queued", progress=0.0, message="Download queued")

    size_estimate = c.models.model_download_size_estimate(payload.model_name) if payload.model_name else {}

    def task(progress, job_id: int):
        token = payload.token or c.settings.huggingface_token
        next_payload = payload.model_copy(update={"token": token})
        return c.models.download(next_payload, progress=progress, job_id=job_id)

    params = payload.model_dump(exclude={"token"})
    if size_estimate:
        params["size_estimate"] = size_estimate
        params["estimated_remaining_gb"] = size_estimate.get("estimated_remaining_gb")
        params["estimated_total_gb"] = size_estimate.get("estimated_total_gb")
    job_id = c.jobs.submit_with_job_id("model_download_dry_run" if payload.dry_run else "model_download", params, task)
    c.models.lifecycle.update(status_model_name, "download", job_id=job_id)
    return {"job_id": job_id, "status": "queued", "dry_run": payload.dry_run, "size_estimate": size_estimate}




@router.post("/memory/cleanup")
def cleanup_model_runtime_memory(payload: dict, request: Request):
    c = ctx(request)
    model_name = payload.get("model_name")
    offload = bool(payload.get("offload_to_cpu") or payload.get("cpu_offload"))
    return c.models.cleanup_runtime_memory(model_name, offload_to_cpu=offload)


@router.post("/offload-cpu")
def offload_model_to_cpu(payload: dict, request: Request):
    c = ctx(request)
    model_name = payload.get("model_name")
    return c.models.cleanup_runtime_memory(model_name, offload_to_cpu=True)


@router.post("/unload")
def unload_model(payload: dict, request: Request):
    c = ctx(request)
    model_name = payload.get("model_name")
    targets = [model_name] if model_name else c.registry.loaded_names()
    targets = [str(t) for t in targets if t]
    if not targets:
        return {"job_id": None, "status": "completed", "unloaded": [], "message": "No model adapters were loaded."}
    for name in targets:
        c.models.lifecycle.update(name, "load", state="unloading", progress=0.0, message="Model unload queued")

    def task(progress, job_id: int):
        return c.models.unload(model_name, progress=progress, job_id=job_id)

    job_id = c.jobs.submit_with_job_id("model_unload", {"model_name": model_name, "targets": targets}, task)
    for name in targets:
        c.models.lifecycle.update(name, "load", job_id=job_id)
    return {"job_id": job_id, "status": "queued", "targets": targets}


@router.post("/unload-many")
def unload_many_models(payload: dict, request: Request):
    c = ctx(request)
    raw_names = payload.get("model_names") or payload.get("models") or payload.get("names") or []
    if isinstance(raw_names, str):
        raw_names = [x.strip() for x in raw_names.split(",") if x.strip()]
    names: list[str] = []
    for value in raw_names or []:
        name = str(value or "").strip()
        if name and name not in names:
            names.append(name)
    if not names:
        raise HTTPException(status_code=400, detail="No model names were requested for unload.")
    queue_source = str(payload.get("queue_source") or "quick_tag").strip() or "quick_tag"
    queued = []
    for model_name in names:
        c.models.lifecycle.update(model_name, "load", state="unloading", progress=0.0, message="Model unload queued")

        def task(progress, job_id: int, _model_name=model_name):
            return c.models.unload(_model_name, progress=progress, job_id=job_id)

        job_id = c.jobs.submit_with_job_id("model_unload", {"model_name": model_name, "queue_source": queue_source, "batch_unload": True}, task)
        c.models.lifecycle.update(model_name, "load", job_id=job_id)
        queued.append({"job_id": job_id, "model_name": model_name, "status": "queued", "queue_source": queue_source})
    return {"queued": queued, "count": len(queued), "queue_source": queue_source}


@router.get("/tag-scores/{media_id}")
def tag_scores(media_id: int, request: Request, tags: str | None = None):
    parsed = [t.strip() for t in (tags or "").split(",") if t.strip()] or None
    return ctx(request).models.tag_scores(media_id, parsed)


@router.post("/tag-score-analytics")
def tag_score_analytics(payload: dict, request: Request):
    return ctx(request).models.tag_score_analytics(
        dataset_id=payload.get("dataset_id"),
        media_ids=payload.get("media_ids") or None,
        limit=int(payload.get("limit") or 200),
        min_score=float(payload.get("min_score") or 0.0),
    )


@router.get("/feature-matrix")
def feature_matrix(request: Request):
    return ctx(request).models.feature_matrix()

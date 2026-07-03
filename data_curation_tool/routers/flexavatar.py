from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/flexavatar", tags=["flexavatar"])


class FlexInstallRequest(BaseModel):
    mode: Literal["quick", "full", "update"] = "quick"


class FlexValidateRequest(BaseModel):
    load_checkpoint: bool = False
    device: str | None = None


class FlexCheckpointRequest(BaseModel):
    url: str | None = None
    local_path: str | None = None
    force: bool = False


class FlexStageRequest(BaseModel):
    avatar_name: str
    mode: Literal["single", "few_shot", "monocular"] = "single"
    media_ids: list[int] = Field(default_factory=list)
    paths: list[str] = Field(default_factory=list)
    role: Literal["source", "driver"] = "source"
    replace: bool = False


class FlexTrackRequest(BaseModel):
    manifest_path: str


class FlexRenderRequest(BaseModel):
    avatar_name: str
    source_manifest: str
    driver_manifest: str | None = None
    driver_mode: Literal["builtin", "custom", "neutral", "source"] = "builtin"
    driver_sequence: str = "EMO-1-shout+laugh"
    device: str = "cuda:0"
    run_fitting: bool = True
    fitting_steps: int = Field(200, ge=0, le=10000)
    fitting_lr: float = Field(1e-2, gt=0)
    lambda_sam: float = Field(1.0, ge=0)
    lambda_dino: float = Field(1.0, ge=0)
    lambda_latent: float = Field(0.0, ge=0)
    max_observations: int = Field(100, ge=1, le=2400)
    load_avatar_code: bool = False
    save_fitting_history: bool = True
    render_360: bool = False
    frame_limit: int = Field(240, ge=1, le=10000)
    fps: float = Field(24.0, ge=1, le=120)
    resolution: int = Field(512, ge=128, le=2048)


class FlexViewerRequest(BaseModel):
    avatar_name: str | None = None


class FlexInterpolateRequest(BaseModel):
    first: str
    second: str
    alpha: float = Field(0.5, ge=0, le=1)
    output_name: str


class FlexTrainingBundleRequest(BaseModel):
    name: str
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    subject_id: str | None = None
    source_type: Literal["monocular_2d", "multi_view_3d", "synthetic_multi_view"] = "monocular_2d"
    steps: int = Field(1_000_000, ge=1)
    batch_size: int = Field(20, ge=1)
    perceptual_start_step: int = Field(400_000, ge=0)
    mixed_precision: str = "bf16"
    nproc_per_node: int = Field(1, ge=1, le=16)
    device_ids: list[int] = Field(default_factory=lambda: [0])
    trainer_entrypoint: str | None = None


class FlexTrainingPlanRequest(BaseModel):
    config_path: str
    trainer_entrypoint: str | None = None
    nproc_per_node: int = Field(1, ge=1, le=16)
    extra_args: list[str] = Field(default_factory=list)


class FlexTrainingRunRequest(FlexTrainingPlanRequest):
    timeout_seconds: int = Field(2_592_000, ge=60)


@router.get("/status")
def flexavatar_status(request: Request, deep: bool = Query(False)):
    return ctx(request).flexavatar.status(deep=deep)


@router.get("/assets")
def flexavatar_assets(request: Request):
    return ctx(request).flexavatar.assets()


@router.get("/file")
def flexavatar_file(request: Request, path: str):
    try:
        target = ctx(request).flexavatar.resolve_workspace_file(path)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(target)


@router.post("/install")
def flexavatar_install(payload: FlexInstallRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.flexavatar.install(payload.mode, progress)

    job_id = c.jobs.submit("flexavatar_install", payload.model_dump(), task)
    return {"job_id": job_id, "mode": payload.mode}


@router.post("/validate")
def flexavatar_validate(payload: FlexValidateRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.flexavatar.validate_runtime(progress, load_checkpoint=payload.load_checkpoint, device=payload.device)

    job_id = c.jobs.submit("flexavatar_validate", payload.model_dump(), task)
    return {"job_id": job_id, "load_checkpoint": payload.load_checkpoint}


@router.post("/checkpoint")
def flexavatar_checkpoint(payload: FlexCheckpointRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.flexavatar.download_checkpoint(progress, url=payload.url, local_path=payload.local_path, force=payload.force)

    job_id = c.jobs.submit("flexavatar_checkpoint", payload.model_dump(), task)
    return {"job_id": job_id}


@router.post("/seed-examples")
def flexavatar_seed_examples(request: Request):
    c = ctx(request)
    job_id = c.jobs.submit("flexavatar_seed_examples", {}, c.flexavatar.seed_examples)
    return {"job_id": job_id}


@router.post("/stage")
def flexavatar_stage(payload: FlexStageRequest, request: Request):
    try:
        return ctx(request).flexavatar.stage_inputs(**payload.model_dump())
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/track")
def flexavatar_track(payload: FlexTrackRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.flexavatar.track(payload.manifest_path, progress)

    job_id = c.jobs.submit("flexavatar_track", payload.model_dump(), task)
    return {"job_id": job_id}


@router.post("/render")
def flexavatar_render(payload: FlexRenderRequest, request: Request):
    c = ctx(request)
    params = payload.model_dump()

    def task(progress):
        return c.flexavatar.render(params, progress)

    job_id = c.jobs.submit("flexavatar_render", params, task)
    return {"job_id": job_id}


@router.post("/viewer")
def flexavatar_viewer(payload: FlexViewerRequest, request: Request):
    try:
        return ctx(request).flexavatar.launch_viewer(payload.avatar_name)
    except (RuntimeError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/interpolate")
def flexavatar_interpolate(payload: FlexInterpolateRequest, request: Request):
    try:
        return ctx(request).flexavatar.interpolate_codes(payload.first, payload.second, payload.alpha, payload.output_name)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/training/bundle")
def flexavatar_training_bundle(payload: FlexTrainingBundleRequest, request: Request):
    try:
        return ctx(request).flexavatar.create_training_bundle(payload.model_dump())
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/training/plan")
def flexavatar_training_plan(payload: FlexTrainingPlanRequest, request: Request):
    try:
        return ctx(request).flexavatar.training_plan(payload.config_path, payload.trainer_entrypoint, payload.nproc_per_node, payload.extra_args)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:  # type: ignore[name-defined]
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/training/run")
def flexavatar_training_run(payload: FlexTrainingRunRequest, request: Request):
    c = ctx(request)
    params: dict[str, Any] = payload.model_dump()

    def task(progress):
        return c.flexavatar.run_external_training(params, progress)

    job_id = c.jobs.submit("flexavatar_training", params, task)
    return {"job_id": job_id}

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from .deps import ctx

router = APIRouter(prefix="/three-d", tags=["3d-studio"])


class ThreeDGeneratePayload(BaseModel):
    provider: str
    media_id: int | None = None
    input_path: str = ""
    multi_image_paths: list[str] | str = Field(default_factory=list)
    video_path: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    repo_path: str = ""
    python_executable: str = ""
    endpoint: str = ""
    api_key: str = ""
    token_profile: str = ""
    api_model_id: str = ""
    ai_model: str = ""
    model_context_shrinker: str = ""
    context_shrinker_model: str = ""
    provider_route: dict[str, Any] = Field(default_factory=dict)
    output_format: str = "glb"
    target_formats: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=1800, ge=30, le=86400)
    dry_run: bool = False
    texture: bool = True
    remove_background: bool = True
    seed: int = 1234
    texture_resolution: int | None = None
    texture_size: int | None = None
    remesh_option: str = ""
    bake_texture: bool = False
    options: dict[str, Any] = Field(default_factory=dict)


class ThreeDRigPayload(BaseModel):
    provider: str
    asset_path: str
    repo_path: str = ""
    blender_executable: str = ""
    shell_executable: str = ""
    output_format: str = "glb"
    target_formats: list[str] = Field(default_factory=list)
    media_id: int | None = None
    annotation_id: int | None = None
    pose: dict[str, Any] | None = None
    automatic_weights: bool = True
    skeleton_only: bool = False
    armature_name: str = "DCT_Armature"
    seed: int | None = None
    timeout_seconds: int = Field(default=3600, ge=30, le=86400)
    dry_run: bool = False
    options: dict[str, Any] = Field(default_factory=dict)


class ThreeDImportPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_path: str
    copy_asset: bool = Field(default=True, alias="copy")
    label: str = ""


class BlenderOpenPayload(BaseModel):
    asset_path: str
    blender_executable: str = ""


def _merged(model: BaseModel) -> dict[str, Any]:
    data = model.model_dump()
    options = data.pop("options", {}) or {}
    return data | dict(options)


@router.get("/providers")
def providers(request: Request):
    return ctx(request).three_d.provider_catalog()


@router.get("/assets")
def assets(request: Request, limit: int = 500):
    return ctx(request).three_d.list_assets(limit=limit)


@router.get("/assets/file")
def asset_file(request: Request, path: str):
    try:
        asset = ctx(request).three_d.asset_path_from_relative(path)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(str(asset), filename=asset.name)


@router.post("/assets/import")
def import_asset(payload: ThreeDImportPayload, request: Request):
    try:
        return ctx(request).three_d.import_asset(payload.source_path, copy=payload.copy_asset, label=payload.label)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate")
def generate(payload: ThreeDGeneratePayload, request: Request):
    c = ctx(request)
    params = _merged(payload)

    def task(progress):
        return c.three_d.generate(params, progress)

    job_id = c.jobs.submit("3d_generation", c.three_d._redact(params), task)
    return {"ok": True, "job_id": job_id, "provider": payload.provider}


@router.post("/rig")
def rig(payload: ThreeDRigPayload, request: Request):
    c = ctx(request)
    params = _merged(payload)

    def task(progress):
        return c.three_d.rig(params, progress)

    job_id = c.jobs.submit("3d_rigging", c.three_d._redact(params), task)
    return {"ok": True, "job_id": job_id, "provider": payload.provider}


@router.post("/open-in-blender")
def open_in_blender(payload: BlenderOpenPayload, request: Request):
    try:
        return ctx(request).three_d.open_in_blender(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

class ThreeDViewportPayload(BaseModel):
    asset_path: str = ""
    path: str = ""
    input_path: str = ""
    blender_executable: str = ""
    force_blender: bool = False
    include_payload: bool = True
    max_vertices: int = Field(default=200000, ge=100, le=1000000)
    max_faces: int = Field(default=200000, ge=100, le=1000000)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)


@router.get("/viewport/modes")
def viewport_modes(request: Request):
    return ctx(request).three_d.viewport_modes()


@router.post("/viewport/prepare")
def prepare_viewport(payload: ThreeDViewportPayload, request: Request):
    try:
        return ctx(request).three_d.prepare_viewer_payload(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/viewport/file")
def viewport_file(request: Request, path: str):
    try:
        payload = ctx(request).three_d.viewer_payload_from_path(path)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(str(payload), filename="viewer_payload.json")

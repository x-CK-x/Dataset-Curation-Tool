from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/comfy", tags=["comfy-bridge"])


class ComfyReceivePayload(BaseModel):
    filename: str = "comfy_output.png"
    data_base64: str = ""
    source_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    import_to_dataset: bool = False
    dataset_id: int | None = None


@router.get("/status")
def status(request: Request):
    return ctx(request).comfy.status()


@router.get("/nodes/package")
def node_package(request: Request):
    package = ctx(request).paths.root / "integrations" / "data_curation_tool_comfyui_nodes.zip"
    if not package.exists():
        raise HTTPException(status_code=404, detail="ComfyUI bridge node package was not found in integrations/.")
    return FileResponse(str(package), filename="data_curation_tool_comfyui_nodes.zip")


@router.get("/workflows")
def workflows(request: Request):
    return ctx(request).comfy.workflow_templates()


@router.post("/media/package/{media_id}")
def media_package(media_id: int, request: Request, include_metadata: bool = True):
    try:
        return ctx(request).comfy.media_package(media_id, include_metadata=include_metadata)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/receive")
def receive(payload: ComfyReceivePayload, request: Request):
    try:
        return ctx(request).comfy.receive_json_payload(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/receive-file")
async def receive_file(
    request: Request,
    file: UploadFile = File(...),
    metadata_json: str = Form(default="{}"),
    import_to_dataset: bool = Form(default=False),
    dataset_id: int | None = Form(default=None),
):
    try:
        import json
        data = await file.read()
        metadata = json.loads(metadata_json or "{}")
        return ctx(request).comfy.save_incoming_media(filename=file.filename or "comfy_output", data=data, metadata=metadata, import_to_dataset=import_to_dataset, dataset_id=dataset_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/metadata/extract")
def extract_metadata(payload: ComfyReceivePayload, request: Request):
    c = ctx(request)
    try:
        saved = c.comfy.receive_json_payload(payload.model_dump())
        extracted = c.metadata.extract_path(saved["path"], include_raw=True)
        return {"ok": True, "received": saved, "metadata": extracted}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

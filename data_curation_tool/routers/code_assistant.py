from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/code", tags=["code-assistant"])


class CodeProjectScanRequest(BaseModel):
    root_path: str
    max_files: int = 600
    max_depth: int = 12
    exclude_dirs: list[str] = Field(default_factory=list)


class CodeReadRequest(BaseModel):
    root_path: str
    paths: list[str] = Field(default_factory=list)
    max_bytes_per_file: int = 60_000
    max_total_bytes: int = 240_000


class CodeChatRequest(BaseModel):
    root_path: str
    prompt: str
    model_name: str = "dataset-assistant"
    files: list[str] = Field(default_factory=list)
    conversation_id: int | None = None
    token_profile: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: str = "none"
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: str = "none"
    runtime_engine: str = "transformers"
    tensor_parallel_size: int = 1
    options: dict = Field(default_factory=dict)


class CodePatchRequest(BaseModel):
    root_path: str
    patch_text: str
    create_backup: bool = True
    check_only: bool = False


class CodeWriteFileRequest(BaseModel):
    root_path: str
    rel_path: str
    content: str
    create_backup: bool = True


@router.post("/scan")
def scan_project(payload: CodeProjectScanRequest, request: Request):
    try:
        return ctx(request).code.scan(payload.root_path, max_files=payload.max_files, max_depth=payload.max_depth, exclude_dirs=payload.exclude_dirs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/read")
def read_project_files(payload: CodeReadRequest, request: Request):
    try:
        return ctx(request).code.read_files(payload.root_path, payload.paths, max_bytes_per_file=payload.max_bytes_per_file, max_total_bytes=payload.max_total_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat")
def chat_about_code(payload: CodeChatRequest, request: Request):
    try:
        runtime = {
            "device": payload.device,
            "device_ids": payload.device_ids,
            "sharding_strategy": payload.sharding_strategy,
            "max_memory": payload.max_memory,
            "torch_dtype": payload.torch_dtype,
            "quantization": payload.quantization,
            "runtime_engine": payload.runtime_engine,
            "tensor_parallel_size": payload.tensor_parallel_size,
        }
        options = dict(payload.options or {})
        if payload.token_profile:
            options["token_profile"] = payload.token_profile
        return ctx(request).code.chat(root_path=payload.root_path, prompt=payload.prompt, model_name=payload.model_name, files=payload.files, conversation_id=payload.conversation_id, options=options, runtime=runtime)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Code assistant request failed: {exc}") from exc


@router.post("/apply-patch")
def apply_code_patch(payload: CodePatchRequest, request: Request):
    try:
        return ctx(request).code.apply_patch(payload.root_path, payload.patch_text, create_backup=payload.create_backup, check_only=payload.check_only)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/write-file")
def write_project_file(payload: CodeWriteFileRequest, request: Request):
    try:
        return ctx(request).code.write_file(payload.root_path, payload.rel_path, payload.content, create_backup=payload.create_backup)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

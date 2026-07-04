from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from .deps import ctx
from ..schemas import DistributedNode

router = APIRouter(prefix="/distributed", tags=["distributed"])


class ShardRequest(BaseModel):
    item_ids: list[int]
    mode: str = "many-to-one"


class RemoteCommandRequest(BaseModel):
    name: str
    command: str
    timeout_seconds: int = 120
    user_approved: bool = False


class RemoteStartRequest(BaseModel):
    name: str
    host: str = "0.0.0.0"
    port: int | None = None
    worker_mode: str | None = None
    timeout_seconds: int = 30
    user_approved: bool = False


class ScpTransferRequest(BaseModel):
    name: str
    local_path: str = ""
    remote_path: str = ""
    recursive: bool = True
    timeout_seconds: int = 600
    user_approved: bool = False


class DownloadPlanRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    node_names: list[str] = Field(default_factory=list)
    include_local: bool = False


class DownloadDispatchRequest(DownloadPlanRequest):
    parallel: bool = True
    timeout_seconds: int = 30


class MergeBackRequest(BaseModel):
    node_names: list[str] = Field(default_factory=list)
    remote_path: str | None = None
    run_id: str | None = None
    timeout_seconds: int = 1800
    user_approved: bool = False


@router.get("/nodes")
def list_nodes(request: Request):
    return ctx(request).distributed.list_nodes()


@router.post("/nodes")
def upsert_node(payload: DistributedNode, request: Request):
    return ctx(request).distributed.upsert_node(payload)


@router.delete("/nodes/{name}")
def delete_node(name: str, request: Request):
    return {"deleted": ctx(request).distributed.remove_node(name)}


@router.post("/nodes/{name}/test")
def test_node(name: str, request: Request):
    return ctx(request).distributed.test_node(name)


@router.post("/ssh")
def run_ssh(payload: RemoteCommandRequest, request: Request):
    return ctx(request).distributed.run_ssh_command(payload.name, payload.command, user_approved=payload.user_approved, timeout_seconds=payload.timeout_seconds)


@router.post("/start-tool")
def start_tool(payload: RemoteStartRequest, request: Request):
    return ctx(request).distributed.start_tool(payload.name, user_approved=payload.user_approved, host=payload.host, port=payload.port, worker_mode=payload.worker_mode, timeout_seconds=payload.timeout_seconds)


@router.post("/scp-upload")
def scp_upload(payload: ScpTransferRequest, request: Request):
    return ctx(request).distributed.scp_upload(payload.name, payload.local_path, payload.remote_path, recursive=payload.recursive, user_approved=payload.user_approved, timeout_seconds=payload.timeout_seconds)


@router.post("/scp-download")
def scp_download(payload: ScpTransferRequest, request: Request):
    return ctx(request).distributed.scp_download(payload.name, payload.remote_path, payload.local_path, recursive=payload.recursive, user_approved=payload.user_approved, timeout_seconds=payload.timeout_seconds)


@router.post("/download-plan")
def download_plan(payload: DownloadPlanRequest, request: Request):
    return ctx(request).distributed.plan_download_shards(payload.payload, node_names=payload.node_names, include_local=payload.include_local)


@router.post("/download-dispatch")
def download_dispatch(payload: DownloadDispatchRequest, request: Request):
    return ctx(request).distributed.dispatch_download(payload.payload, node_names=payload.node_names, include_local=payload.include_local, parallel=payload.parallel, timeout_seconds=payload.timeout_seconds)


@router.post("/merge-back")
def merge_back(payload: MergeBackRequest, request: Request):
    return ctx(request).distributed.merge_back(node_names=payload.node_names, remote_path=payload.remote_path, run_id=payload.run_id, user_approved=payload.user_approved, timeout_seconds=payload.timeout_seconds)


@router.post("/shard")
def shard(payload: ShardRequest, request: Request):
    return ctx(request).distributed.shard(payload.item_ids, payload.mode)

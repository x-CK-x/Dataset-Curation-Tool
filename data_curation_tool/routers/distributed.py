from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .deps import ctx
from ..schemas import DistributedNode

router = APIRouter(prefix="/distributed", tags=["distributed"])


class ShardRequest(BaseModel):
    item_ids: list[int]
    mode: str = "many-to-one"


@router.get("/nodes")
def list_nodes(request: Request):
    return ctx(request).distributed.list_nodes()


@router.post("/nodes")
def upsert_node(payload: DistributedNode, request: Request):
    return ctx(request).distributed.upsert_node(payload)


@router.delete("/nodes/{name}")
def delete_node(name: str, request: Request):
    return {"deleted": ctx(request).distributed.remove_node(name)}


@router.post("/shard")
def shard(payload: ShardRequest, request: Request):
    return ctx(request).distributed.shard(payload.item_ids, payload.mode)

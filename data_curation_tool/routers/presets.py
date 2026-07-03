from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .deps import ctx
from ..schemas import DownloadPreset

router = APIRouter(prefix="/presets", tags=["presets"])


class NamesRequest(BaseModel):
    names: list[str]


class ImportTextRequest(BaseModel):
    content: str
    source: str = "booru"


@router.get("")
def list_presets(request: Request, include_archived: bool = False):
    return ctx(request).presets.list(include_archived)


@router.post("")
def upsert_preset(payload: DownloadPreset, request: Request):
    ctx(request).presets.upsert(payload)
    return {"saved": payload.name}


@router.post("/import-text")
def import_text(payload: ImportTextRequest, request: Request):
    names = ctx(request).presets.import_text(payload.content, payload.source)
    return {"created": names}


@router.post("/archive")
def archive(payload: NamesRequest, request: Request):
    return {"archived": ctx(request).presets.archive(payload.names)}


@router.post("/delete")
def delete(payload: NamesRequest, request: Request):
    return {"deleted": ctx(request).presets.delete(payload.names)}

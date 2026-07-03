from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from .deps import ctx
from ..schemas import CaptionUpdate, SidecarRefreshRequest, TagUpdate

router = APIRouter(prefix="/media", tags=["media"])


@router.get("")
def list_media(
    request: Request,
    dataset_id: int | None = None,
    q: str | None = None,
    tag: str | None = None,
    media_type: str | None = None,
    duplicate: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(80, ge=1, le=500),
):
    return ctx(request).media.page(dataset_id, q, tag, media_type, duplicate, page, page_size).model_dump()


@router.get("/{media_id}")
def get_media(media_id: int, request: Request):
    item = ctx(request).media.get(media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    return item.model_dump()


@router.get("/{media_id}/file")
def media_file(media_id: int, request: Request):
    item = ctx(request).media.get(media_id)
    if not item or not Path(item.path).exists():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(item.path)


@router.get("/{media_id}/thumbnail")
def media_thumbnail(media_id: int, request: Request):
    path = ctx(request).media.ensure_thumbnail(media_id)
    if not path or not path.exists():
        item = ctx(request).media.get(media_id)
        if not item or not Path(item.path).exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        return FileResponse(item.path)
    return FileResponse(path)


@router.put("/{media_id}/tags")
def update_tags(media_id: int, payload: TagUpdate, request: Request):
    item = ctx(request).media.get(media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    tags = ctx(request).tags.set_tag_string(media_id, payload.tag_string, payload.separator, payload.source, payload.save_sidecar, payload.tag_profile, payload.order_strategy)
    return {"media_id": media_id, "tags": tags}


@router.put("/{media_id}/caption")
def update_caption(media_id: int, payload: CaptionUpdate, request: Request):
    c = ctx(request)
    item = c.media.get(media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    c.db.upsert_caption(media_id, payload.caption, source=payload.source)
    if payload.save_sidecar:
        Path(item.path).with_suffix(".caption").write_text(payload.caption, encoding="utf-8")
    return {"media_id": media_id, "caption": payload.caption}


@router.post("/refresh-sidecars")
def refresh_sidecars(payload: SidecarRefreshRequest, request: Request):
    c = ctx(request)
    return c.datasets.refresh_sidecars(payload.media_ids or None, payload.dataset_id, profile_key=payload.tag_profile)

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json

import requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response

from .deps import ctx
from ..schemas import CaptionUpdate, SidecarRefreshRequest, TagUpdate
from ..services.downloader_service import BOORU_SOURCES, _extract_tags, _item_post_id

router = APIRouter(prefix="/media", tags=["media"])




def _thumbnail_placeholder_svg(media_id: int, label: str = "thumbnail pending") -> Response:
    safe_label = str(label or "thumbnail pending").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:80]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#101827"/><stop offset="1" stop-color="#243047"/></linearGradient></defs>
  <rect width="160" height="160" rx="14" fill="url(#g)"/>
  <rect x="19" y="28" width="122" height="82" rx="8" fill="none" stroke="#64748b" stroke-width="2"/>
  <path d="M31 96l31-30 23 21 15-13 30 22" fill="none" stroke="#38bdf8" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity="0.75"/>
  <circle cx="111" cy="51" r="9" fill="#38bdf8" opacity="0.8"/>
  <text x="80" y="136" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="11" fill="#cbd5e1">{safe_label}</text>
  <text x="80" y="151" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="#94a3b8">media #{int(media_id)}</text>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "no-store, max-age=0"})


def _booru_reset_source_options() -> list[str]:
    return [key for key in BOORU_SOURCES.keys() if key not in {"generic-json"}]


def _read_download_sidecar(media_path: str | Path) -> tuple[dict, Path]:
    path = Path(media_path)
    candidates = [path.with_suffix(".download.json"), path.with_suffix(path.suffix + ".download.json")]
    for candidate in candidates:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8")), candidate
            except Exception:
                return {}, candidate
    return {}, candidates[0]


def _fetch_booru_post_by_id(source: str, post_id: str, user_agent: str) -> dict:
    source = str(source or "").strip().lower()
    post_id = str(post_id or "").strip()
    if not source or not post_id:
        raise RuntimeError("Missing source/post id")
    headers = {"User-Agent": user_agent or "DataCurationTool/5.8"}
    timeout = 60
    if source in {"e621", "e926"}:
        url = f"https://{source}.net/posts/{post_id}.json"
        data = requests.get(url, headers=headers, timeout=timeout).json()
        return data.get("post") or data
    if source == "danbooru":
        url = f"https://danbooru.donmai.us/posts/{post_id}.json"
        return requests.get(url, headers=headers, timeout=timeout).json()
    cfg = BOORU_SOURCES.get(source) or {}
    api_url = cfg.get("api_url")
    if not api_url:
        raise RuntimeError(f"No post lookup endpoint is configured for {source}")
    if source in {"gelbooru", "safebooru", "rule34"}:
        sep = "&" if "?" in api_url else "?"
        url = f"{api_url}{sep}id={post_id}"
    elif source in {"konachan", "yandere"}:
        sep = "&" if "?" in api_url else "?"
        url = f"{api_url}{sep}tags=id:{post_id}&limit=1"
    else:
        sep = "&" if "?" in api_url else "?"
        url = f"{api_url}{sep}id={post_id}"
    data = requests.get(url, headers=headers, timeout=timeout).json()
    key = cfg.get("results_key")
    if isinstance(data, dict) and key and isinstance(data.get(key), list):
        rows = data.get(key) or []
        if not rows:
            raise RuntimeError(f"{source} returned no post for id {post_id}")
        return rows[0]
    if isinstance(data, list):
        if not data:
            raise RuntimeError(f"{source} returned no post for id {post_id}")
        return data[0]
    if isinstance(data, dict):
        return data
    raise RuntimeError(f"Unexpected {source} response for id {post_id}")


@router.get("/booru-reset/sources")
def booru_reset_sources(request: Request):
    return {"sources": _booru_reset_source_options()}


def _reset_tags_from_booru_with_context(c, payload: dict, progress=None) -> dict:
    media_ids = [int(x) for x in (payload.get("media_ids") or []) if str(x).strip().isdigit()]
    source = str(payload.get("source") or payload.get("profile_key") or "e621").strip().lower()
    profile_key = str(payload.get("profile_key") or source or "e621").strip().lower()
    order_strategy = str(payload.get("order_strategy") or "booru")
    if source not in BOORU_SOURCES or source == "generic-json":
        raise RuntimeError(f"Unsupported booru source: {source}")
    if not media_ids:
        raise RuntimeError("No media IDs were supplied")
    failures: list[dict] = []
    updated: list[dict] = []
    total = max(1, len(media_ids))
    for idx, media_id in enumerate(media_ids, start=1):
        if progress:
            progress((idx - 1) / total, f"Booru tag reset {idx}/{len(media_ids)}: media #{media_id}")
        item = c.media.get(media_id)
        if not item:
            failures.append({"media_id": media_id, "reason": "media not found"})
            continue
        meta, sidecar = _read_download_sidecar(item.path)
        item_meta = meta.get("item") if isinstance(meta, dict) else None
        if not isinstance(item_meta, dict):
            failures.append({"media_id": media_id, "path": item.path, "reason": "missing .download.json sidecar with original post metadata"})
            continue
        original_source = str(meta.get("source") or "").strip().lower()
        if original_source and original_source != source:
            failures.append({"media_id": media_id, "path": item.path, "reason": f"sidecar source is {original_source}, not selected {source}"})
            continue
        post_id = _item_post_id(item_meta)
        if not post_id:
            failures.append({"media_id": media_id, "path": item.path, "reason": "original sidecar has no post id"})
            continue
        try:
            fresh_item = _fetch_booru_post_by_id(source, post_id, c.settings.downloader_user_agent or "DataCurationTool/5.8")
            cfg = BOORU_SOURCES[source]
            tags = _extract_tags(fresh_item, cfg.get("tags_key"))
            if not tags:
                raise RuntimeError("fresh post returned no tags")
            applied = c.tags.set_tags(media_id, tags, source=f"booru_reset:{source}", save_sidecar=True, profile_key=profile_key, order_strategy=order_strategy)
            fresh_meta = dict(meta or {})
            fresh_meta.update({"source": source, "item": fresh_item, "booru_reset_at": datetime.now(timezone.utc).isoformat(), "booru_reset_post_id": str(post_id)})
            sidecar.write_text(json.dumps(fresh_meta, indent=2, ensure_ascii=False), encoding="utf-8")
            updated.append({"media_id": media_id, "path": item.path, "source": source, "post_id": str(post_id), "tag_count": len(applied)})
        except Exception as exc:
            failures.append({"media_id": media_id, "path": item.path, "source": source, "post_id": str(post_id), "reason": str(exc)})
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "source": source, "profile_key": profile_key, "requested": len(media_ids), "updated": updated, "failures": failures}
    out_dir = c.paths.runtime / "booru_tag_resets"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"booru_reset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(report_path)
    if progress:
        progress(1.0, f"Booru tag reset complete: {len(updated)} updated, {len(failures)} failed")
    return report


@router.post("/reset-tags-from-booru")
def reset_tags_from_booru(payload: dict, request: Request):
    try:
        return _reset_tags_from_booru_with_context(ctx(request), payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reset-tags-from-booru/job")
def reset_tags_from_booru_job(payload: dict, request: Request):
    c = ctx(request)
    params = dict(payload or {})
    def task(progress, job_id):
        return _reset_tags_from_booru_with_context(c, params, progress=progress)
    job_id = c.jobs.submit_with_job_id("booru_tag_reset", params, task)
    return {"job_id": job_id, "status": "queued", "media_ids": params.get("media_ids") or [], "source": params.get("source") or params.get("profile_key") or "e621"}


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


@router.post("/thumbnails/prewarm")
def prewarm_thumbnails(payload: dict, request: Request):
    ids = [int(x) for x in (payload.get("media_ids") or []) if str(x).strip().isdigit()]
    if not ids:
        return {"queued": 0}
    placeholders = ",".join("?" for _ in ids)
    rows = ctx(request).db.query(f"SELECT id, path, media_type FROM media WHERE id IN ({placeholders}) AND active=1", ids)
    queued = ctx(request).media.schedule_thumbnail_prewarm(rows)
    return {"queued": queued, "requested": len(ids)}


@router.post("/thumbnails/status")
def thumbnail_status(payload: dict, request: Request):
    ids = [int(x) for x in (payload.get("media_ids") or []) if str(x).strip().isdigit()]
    status = ctx(request).media.thumbnail_status(ids)
    if status.get("missing"):
        placeholders = ",".join("?" for _ in status["missing"])
        rows = ctx(request).db.query(f"SELECT id, path, media_type FROM media WHERE id IN ({placeholders}) AND active=1", status["missing"]) if placeholders else []
        queued = ctx(request).media.schedule_thumbnail_prewarm(rows)
    else:
        queued = 0
    return {**status, "queued": queued}


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
def media_thumbnail(media_id: int, request: Request, fast: bool = Query(False), v: str | None = None):
    media_service = ctx(request).media
    path = media_service.thumbnail_path(media_id)
    if path.exists():
        return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})
    media_service.queue_thumbnail(media_id)
    if fast:
        return _thumbnail_placeholder_svg(media_id, "thumbnail queued")
    path = media_service.ensure_thumbnail(media_id, wait_seconds=0.20, queue_if_missing=True)
    if path and path.exists():
        return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})
    return _thumbnail_placeholder_svg(media_id, "thumbnail queued")


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

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, File, Query, Request, UploadFile

from .deps import ctx
from ..schemas import (
    BulkTagRequest,
    CustomTagRequest,
    GroupRequest,
    TagCategoryRequest,
    TagCategoryReapplyRequest,
    TagDictionaryUrlImportRequest,
    TagDictionaryDefaultImportRequest,
    TagPrecedenceUpdateRequest,
    TagProfileUpdateRequest,
    TagMetadataRequest,
    TagPruneRequest,
    TagReorderRequest,
)

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/profiles")
def profiles(request: Request):
    return ctx(request).tags.list_profiles()

@router.post("/profiles")
def upsert_profile(payload: TagProfileUpdateRequest, request: Request):
    return ctx(request).tags.upsert_profile(payload.key, payload.label, payload.categories, payload.precedence, payload.db_export_url)


@router.put("/profiles/{profile_key}/precedence")
def update_profile_precedence(profile_key: str, payload: TagPrecedenceUpdateRequest, request: Request):
    return ctx(request).tags.update_precedence(profile_key, payload.precedence)


@router.get("/dictionary/status")
def dictionary_status(request: Request, profile_key: str | None = None):
    return ctx(request).tags.dictionary_status(profile_key)


@router.get("/dictionary/default-urls")
def dictionary_default_urls(request: Request, profile_key: str = "e621"):
    return {"profile_key": profile_key, "urls": ctx(request).tags.default_export_urls(profile_key)}


@router.get("/categories")
def categories(request: Request, profile_key: str = "e621"):
    return ctx(request).tags.categories(profile_key)

@router.post("/categories/custom")
def add_custom_category(payload: TagCategoryRequest, request: Request):
    result = ctx(request).tags.add_category(payload.profile_key, payload.key, payload.label, payload.css_class)
    if payload.color:
        settings = ctx(request).settings
        settings.category_colors[payload.key] = payload.color
        settings.save(ctx(request).paths.settings)
        result["color"] = payload.color
    return result

@router.get("/suggest")
def suggest_tags(request: Request, q: str = Query("", alias="q"), prefix: str = "", profile_key: str = "e621", limit: int = 50, include_custom: bool = True):
    return ctx(request).tags.suggest(q or prefix or "", limit=limit, profile_key=profile_key, include_custom=include_custom)

@router.post("/metadata")
def tag_metadata(payload: TagMetadataRequest, request: Request):
    return ctx(request).tags.metadata(payload.tags, payload.profile_key)

@router.post("/custom")
def add_custom_tag(payload: CustomTagRequest, request: Request):
    return ctx(request).tags.add_custom_tag(payload.profile_key, payload.tag, payload.category, payload.note, payload.color)

@router.get("/custom")
def list_custom_tags(request: Request, profile_key: str | None = None):
    return ctx(request).tags.custom_tags(profile_key)


@router.post("/categories/reapply")
def reapply_categories(payload: TagCategoryReapplyRequest, request: Request):
    return ctx(request).tags.reapply_categories(payload.media_ids, payload.dataset_id, payload.profile_key, payload.save_sidecars)

@router.post("/reorder")
def reorder_tags(payload: TagReorderRequest, request: Request):
    ordered = ctx(request).tags.order_tags(payload.tags, profile_key=payload.profile_key, strategy=payload.strategy)
    metadata = ctx(request).tags.metadata(ordered, payload.profile_key)
    return {"tags": ordered, "metadata": metadata}

@router.post("/bulk")
def bulk_tags(payload: BulkTagRequest, request: Request):
    return ctx(request).tags.bulk(payload)

@router.post("/prune")
def prune_tags(payload: TagPruneRequest, request: Request):
    return [item.model_dump() for item in ctx(request).tags.prune(payload)]

@router.post("/dictionary/import")
async def import_dictionary(request: Request, file: UploadFile = File(...), profile_key: str = "e621"):
    c = ctx(request)
    target = c.paths.runtime / "uploads" / file.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(await file.read())
    count = c.tags.import_dictionary_csv(target, profile_key=profile_key)
    return {"imported": count, "profile_key": profile_key, "path": str(target)}

@router.post("/dictionary/import-url")
def import_dictionary_url(payload: TagDictionaryUrlImportRequest, request: Request):
    c = ctx(request)
    parsed = urlparse(payload.url)
    filename = Path(parsed.path).name or f"tags_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    target = c.paths.runtime / "uploads" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": c.settings.downloader_user_agent or "DataCurationTool/5.36.0"}
    with requests.get(payload.url, headers=headers, timeout=120, stream=True) as response:
        response.raise_for_status()
        with target.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    count = c.tags.import_dictionary_csv(target, profile_key=payload.profile_key)
    return {"imported": count, "profile_key": payload.profile_key, "path": str(target), "url": payload.url}

@router.post("/dictionary/import-default")
def import_default_dictionary(payload: TagDictionaryDefaultImportRequest, request: Request):
    c = ctx(request)
    urls = [payload.url] if payload.url else c.tags.default_export_urls(payload.profile_key)
    urls = [url for url in urls if url]
    if not urls:
        raise ValueError("No default dictionary URL is configured for this profile. Paste a CSV/TSV/db-export URL instead.")

    def task(progress):
        return c.tags.import_default_exports(
            profile_key=payload.profile_key,
            url=payload.url,
            user_agent=c.settings.downloader_user_agent or "DataCurationTool/5.36.0",
            cache_hours=int(getattr(c.settings, "tag_db_export_cache_hours", 336) or 336),
            progress=progress,
            replace_existing=True,
        )

    job_id = c.jobs.submit("tag_dictionary_import", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued", "profile_key": payload.profile_key, "urls": urls}


@router.get("/groups")
def list_groups(request: Request, dataset_id: int | None = None):
    params = []
    where = ""
    if dataset_id:
        where = "WHERE g.dataset_id=?"
        params.append(dataset_id)
    rows = ctx(request).db.query(
        f"""
        SELECT g.*, COUNT(gi.media_id) AS media_count
        FROM groups g LEFT JOIN group_items gi ON gi.group_id=g.id
        {where}
        GROUP BY g.id ORDER BY g.name
        """,
        params,
    )
    return rows

@router.post("/groups")
def save_group(payload: GroupRequest, request: Request):
    c = ctx(request)
    c.db.execute("INSERT INTO groups(dataset_id, name, created_at) VALUES (?, ?, datetime('now')) ON CONFLICT(dataset_id, name) DO UPDATE SET name=excluded.name", (payload.dataset_id, payload.name))
    row = c.db.query_one("SELECT id FROM groups WHERE dataset_id=? AND name=?", (payload.dataset_id, payload.name))
    group_id = row["id"]
    c.db.execute("DELETE FROM group_items WHERE group_id=?", (group_id,))
    c.db.executemany("INSERT OR IGNORE INTO group_items(group_id, media_id, created_at) VALUES (?, ?, datetime('now'))", [(group_id, mid) for mid in payload.media_ids])
    return {"group_id": group_id, "saved": len(payload.media_ids)}

@router.get("/groups/{group_id}")
def load_group(group_id: int, request: Request):
    rows = ctx(request).db.query("SELECT media_id FROM group_items WHERE group_id=? ORDER BY media_id", (group_id,))
    return {"group_id": group_id, "media_ids": [row["media_id"] for row in rows]}

@router.delete("/groups/{group_id}")
def delete_group(group_id: int, request: Request):
    ctx(request).db.execute("DELETE FROM groups WHERE id=?", (group_id,))
    return {"deleted": group_id}

@router.post("/groups/{group_id}/subtract")
def subtract_group(group_id: int, payload: GroupRequest, request: Request):
    c = ctx(request)
    c.db.executemany("DELETE FROM group_items WHERE group_id=? AND media_id=?", [(group_id, mid) for mid in payload.media_ids])
    return {"group_id": group_id, "removed": len(payload.media_ids)}

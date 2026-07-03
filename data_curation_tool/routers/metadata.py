from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .deps import ctx
from ..schemas import MetadataApplyRequest, MetadataExtractRequest, MetadataFieldComposeRequest, MetadataFieldInspectRequest, MetadataPathRequest

router = APIRouter(prefix="/metadata", tags=["metadata"])


def _profile(payload: Any, default: str = "e621") -> str:
    return getattr(payload, "profile_key", None) or getattr(payload, "tag_profile", None) or default


def _tag_source(payload: Any) -> str:
    return getattr(payload, "derive_source", None) or getattr(payload, "tag_source", None) or "positive_prompt"


def _caption_source(payload: Any) -> str:
    return getattr(payload, "caption_source", None) or "positive_prompt"


@router.get("/sources")
def sources(request: Request):
    return ctx(request).metadata.supported_sources()


@router.get("/{media_id}")
def saved_metadata(media_id: int, request: Request):
    c = ctx(request)
    item = c.metadata.get_saved_metadata(media_id)
    if item is not None:
        return item
    try:
        return c.metadata.extract_media(media_id, persist=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/path")
def extract_path(payload: MetadataPathRequest, request: Request):
    c = ctx(request)
    try:
        return c.metadata.extract_path(Path(payload.path), include_raw=payload.include_raw, parse_stealth=payload.parse_stealth)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/fields")
def inspect_metadata_fields(payload: MetadataFieldInspectRequest, request: Request):
    c = ctx(request)
    try:
        return c.metadata.inspect_fields_for_media(media_id=payload.media_id, path=payload.path, include_raw=payload.include_raw, parse_stealth=payload.parse_stealth)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/compose")
def compose_metadata_fields(payload: MetadataFieldComposeRequest, request: Request):
    c = ctx(request)
    try:
        return c.metadata.compose_from_fields(
            media_id=payload.media_id,
            path=payload.path,
            include_raw=payload.include_raw,
            parse_stealth=payload.parse_stealth,
            fields=payload.fields,
            original_delimiter=payload.original_delimiter,
            output_delimiter=payload.output_delimiter,
            split_strings=payload.split_strings,
            keep_parentheses=payload.keep_parentheses,
            keep_braces=payload.keep_braces,
            strip_weight_syntax=payload.strip_weight_syntax,
            normalize_tags=payload.normalize_tags,
            apply_tags=payload.apply_tags,
            apply_caption=payload.apply_caption,
            replace_tags=payload.replace_tags,
            save_sidecars=payload.save_sidecars,
            tag_profile=payload.tag_profile or c.settings.default_tag_profile,
            order_strategy=payload.order_strategy,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _run_extract(c, payload: MetadataExtractRequest, progress=None):
    return c.metadata.extract_many(
        media_ids=payload.media_ids,
        media_id=payload.media_id,
        dataset_id=payload.dataset_id,
        path=payload.path,
        external_paths=payload.external_paths,
        profile_key=_profile(payload, c.settings.default_tag_profile),
        apply_tags=payload.apply_tags,
        apply_caption=payload.apply_caption,
        replace_tags=payload.replace_tags,
        tag_source=_tag_source(payload),
        caption_source=_caption_source(payload),
        save_sidecars=payload.save_sidecars,
        parse_stealth=payload.parse_stealth,
        include_raw=payload.include_raw,
        order_strategy=payload.order_strategy,
        progress=progress,
    )


@router.post("/extract-now")
def extract_now(payload: MetadataExtractRequest, request: Request):
    c = ctx(request)
    result = _run_extract(c, payload)
    if result.get("count", 0) == 0 and not result.get("errors"):
        raise HTTPException(status_code=400, detail="Provide selected media IDs, dataset ID, or external path(s).")
    return result


@router.post("/extract")
def extract_job(payload: MetadataExtractRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return _run_extract(c, payload, progress=progress)

    job_id = c.jobs.submit("metadata_extraction", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}


@router.post("/apply")
def apply_metadata(payload: MetadataApplyRequest, request: Request):
    c = ctx(request)
    ids: list[int] = []
    if payload.media_id is not None:
        ids.append(int(payload.media_id))
    ids.extend(int(x) for x in payload.media_ids or [])
    seen: set[int] = set()
    ids = [x for x in ids if not (x in seen or seen.add(x))]
    if not ids:
        raise HTTPException(status_code=400, detail="Select one or more media items.")
    results = []
    for media_id in ids:
        results.append(c.metadata.apply_metadata_to_media(
            media_id,
            include_raw=payload.include_raw,
            apply_tags=payload.apply_tags,
            apply_caption=payload.apply_caption,
            tag_source=_tag_source(payload),
            caption_source=_caption_source(payload),
            tag_profile=_profile(payload, c.settings.default_tag_profile),
            order_strategy=payload.order_strategy,
            save_sidecars=payload.save_sidecars,
            replace_tags=payload.replace_tags,
        ))
    return {"applied": len(results), "items": results}

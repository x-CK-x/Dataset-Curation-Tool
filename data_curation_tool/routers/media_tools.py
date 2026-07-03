from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from .deps import ctx
from ..database import now_iso
from ..schemas import (
    AudioExtractRequest,
    FrameExtractRequest,
    KritaExportRequest,
    KritaHandoffRequest,
    KritaImportRequest,
    MetadataApplyRequest,
    MetadataExtractRequest,
    MetadataSchemaRequest,
    MetadataComposeRequest,
)
from ..utils import average_hash, classify_media, image_size, sha256_file

router = APIRouter(prefix="/media-tools", tags=["media-tools"])


def _profile(payload: Any, default: str = "e621") -> str:
    return getattr(payload, "tag_profile", None) or getattr(payload, "profile_key", None) or default


def _tag_source(payload: Any) -> str:
    source = getattr(payload, "derive_source", None) or getattr(payload, "tag_source", None) or "positive_prompt"
    return {"all_text": "all", "all_prompts": "all", "lora_triggers": "lora_refs"}.get(source, source)


def _caption_source(payload: Any) -> str:
    source = getattr(payload, "caption_source", None) or "positive_prompt"
    return {"metadata_summary": "summary"}.get(source, source)


def _selected_ids(c, payload: MetadataExtractRequest | MetadataApplyRequest) -> list[int]:
    ids: list[int] = []
    if getattr(payload, "media_id", None) is not None:
        ids.append(int(payload.media_id))
    ids.extend(int(x) for x in (payload.media_ids or []))
    if getattr(payload, "dataset_id", None) is not None and hasattr(c.metadata, "media_targets"):
        ids.extend(c.metadata.media_targets(dataset_id=int(payload.dataset_id)))
    out: list[int] = []
    seen: set[int] = set()
    for mid in ids:
        if mid not in seen:
            out.append(mid); seen.add(mid)
    return out


def _normalize_metadata_result(result: dict[str, Any]) -> dict[str, Any]:
    tags = result.get("extracted_tags") or result.get("tags") or []
    if not tags and isinstance(result.get("payload"), dict):
        tags = result["payload"].get("tags") or []
    result["extracted_tags"] = tags
    result.setdefault("extracted_caption", result.get("caption") or (result.get("payload") or {}).get("caption") or "")
    return result


@router.get("/status")
def status(request: Request):
    c = ctx(request)
    return {"ffmpeg": c.video.ffmpeg_status(), "metadata_sources": c.metadata.supported_sources()}




@router.get("/ffmpeg/status")
def ffmpeg_status(request: Request):
    return ctx(request).video.ffmpeg_status()


@router.post("/metadata/extract")
def extract_metadata(payload: MetadataExtractRequest, request: Request):
    c = ctx(request)
    results: list[dict[str, Any]] = []
    for external in ([payload.path] if payload.path else []) + list(payload.external_paths or []):
        if external:
            results.append(_normalize_metadata_result(c.metadata.extract_path(Path(external), include_raw=payload.include_raw, parse_stealth=payload.parse_stealth)))
    for media_id in _selected_ids(c, payload):
        if payload.apply_tags or payload.apply_caption:
            results.append(_normalize_metadata_result(c.metadata.apply_metadata_to_media(
                int(media_id),
                include_raw=payload.include_raw,
                apply_tags=payload.apply_tags,
                apply_caption=payload.apply_caption,
                tag_source=_tag_source(payload),
                caption_source=_caption_source(payload),
                tag_profile=_profile(payload, c.settings.default_tag_profile),
                order_strategy=payload.order_strategy,
                save_sidecars=payload.save_sidecars,
                replace_tags=payload.replace_tags,
            )))
        else:
            results.append(_normalize_metadata_result(c.metadata.extract_media(int(media_id), include_raw=payload.include_raw, parse_stealth=payload.parse_stealth, persist=True)))
    if not results:
        raise HTTPException(status_code=400, detail="Provide selected media IDs or external paths.")
    return {"count": len(results), "results": results}


@router.post("/metadata/extract-now")
def extract_metadata_now(payload: MetadataExtractRequest, request: Request):
    return extract_metadata(payload, request)




@router.post("/metadata/schema")
def metadata_schema(payload: MetadataSchemaRequest, request: Request):
    c = ctx(request)
    results: list[dict[str, Any]] = []
    ids = []
    if payload.media_id is not None:
        ids.append(int(payload.media_id))
    ids.extend(int(x) for x in (payload.media_ids or []))
    for media_id in ids:
        results.append(c.metadata.schema_for_media_or_path(media_id=media_id, include_raw=payload.include_raw, parse_stealth=payload.parse_stealth, max_items=payload.max_items))
    for external in ([payload.path] if payload.path else []) + list(payload.external_paths or []):
        if external:
            results.append(c.metadata.schema_for_media_or_path(path=external, include_raw=payload.include_raw, parse_stealth=payload.parse_stealth, max_items=payload.max_items))
    if not results:
        raise HTTPException(status_code=400, detail="Provide selected media IDs or external paths.")
    return {"count": len(results), "results": results}


@router.post("/metadata/compose")
def metadata_compose(payload: MetadataComposeRequest, request: Request):
    c = ctx(request)
    if not payload.selected_paths:
        raise HTTPException(status_code=400, detail="Select one or more metadata paths to compose.")
    results: list[dict[str, Any]] = []
    ids = []
    if payload.media_id is not None:
        ids.append(int(payload.media_id))
    ids.extend(int(x) for x in (payload.media_ids or []))
    for media_id in ids:
        result = c.metadata.compose_for_media_or_path(
            media_id=media_id,
            selected_paths=payload.selected_paths,
            include_raw=payload.include_raw,
            parse_stealth=payload.parse_stealth,
            input_delimiter=payload.input_delimiter,
            output_delimiter=payload.output_delimiter,
            split_to_tags=payload.split_to_tags,
            keep_parentheses=payload.keep_parentheses,
            keep_curly_braces=payload.keep_curly_braces,
            keep_square_brackets=payload.keep_square_brackets,
            keep_weight_syntax=payload.keep_weight_syntax,
            dedupe=payload.dedupe,
        )
        if payload.apply_tags and result.get("tokens"):
            item = c.media.get(media_id)
            current = item.tags if item else []
            merged = result["tokens"] if payload.replace_tags else list(dict.fromkeys([*(current or []), *result["tokens"]]))
            c.tags.set_tags(media_id, merged, source="metadata_compose", save_sidecar=payload.save_sidecars, profile_key=payload.tag_profile, order_strategy=payload.order_strategy)
            result["applied_tags"] = True
        if payload.apply_caption and result.get("text"):
            c.db.upsert_caption(media_id, result["text"], source="metadata_compose")
            result["applied_caption"] = True
        results.append(result)
    for external in ([payload.path] if payload.path else []) + list(payload.external_paths or []):
        if external:
            results.append(c.metadata.compose_for_media_or_path(
                path=external,
                selected_paths=payload.selected_paths,
                include_raw=payload.include_raw,
                parse_stealth=payload.parse_stealth,
                input_delimiter=payload.input_delimiter,
                output_delimiter=payload.output_delimiter,
                split_to_tags=payload.split_to_tags,
                keep_parentheses=payload.keep_parentheses,
                keep_curly_braces=payload.keep_curly_braces,
                keep_square_brackets=payload.keep_square_brackets,
                keep_weight_syntax=payload.keep_weight_syntax,
                dedupe=payload.dedupe,
            ))
    if not results:
        raise HTTPException(status_code=400, detail="Provide selected media IDs or external paths.")
    return {"count": len(results), "results": results}


@router.post("/metadata/apply")
def apply_metadata(payload: MetadataApplyRequest, request: Request):
    c = ctx(request)
    ids = _selected_ids(c, payload)
    if not ids:
        raise HTTPException(status_code=400, detail="Select one or more media items.")
    applied = []
    for media_id in ids:
        applied.append(c.metadata.apply_metadata_to_media(
            int(media_id),
            apply_tags=payload.apply_tags,
            apply_caption=payload.apply_caption,
            tag_source=_tag_source(payload),
            caption_source=_caption_source(payload),
            tag_profile=_profile(payload, c.settings.default_tag_profile),
            order_strategy=payload.order_strategy,
            save_sidecars=payload.save_sidecars,
            replace_tags=payload.replace_tags,
        ))
    return {"applied": len(applied), "items": applied}


def _frame_task(c, payload: FrameExtractRequest):
    def task(progress):
        progress(0.05, "Extracting video frames as PNG")
        result = c.video.extract_frames(payload, progress=lambda frac, msg: progress(0.05 + frac * 0.90, msg))
        progress(1.0, "Frame extraction complete")
        return result
    return task


@router.post("/video/extract-frames")
def extract_frames(payload: FrameExtractRequest, request: Request):
    c = ctx(request)
    job_id = c.jobs.submit("video_frame_extraction", payload.model_dump(), _frame_task(c, payload))
    return {"job_id": job_id, "status": "queued"}


@router.post("/frames/extract")
def extract_frames_alias(payload: FrameExtractRequest, request: Request):
    return extract_frames(payload, request)


def _audio_task(c, payload: AudioExtractRequest):
    def task(progress):
        progress(0.05, "Extracting audio stream")
        result = c.video.extract_audio(payload, progress=lambda frac, msg: progress(0.05 + frac * 0.90, msg))
        progress(1.0, "Audio extraction complete")
        return result
    return task


@router.post("/video/extract-audio")
def extract_audio(payload: AudioExtractRequest, request: Request):
    c = ctx(request)
    job_id = c.jobs.submit("video_audio_extraction", payload.model_dump(), _audio_task(c, payload))
    return {"job_id": job_id, "status": "queued"}


@router.post("/audio/extract")
def extract_audio_alias(payload: AudioExtractRequest, request: Request):
    return extract_audio(payload, request)


@router.post("/audio/recording")
async def save_recording(request: Request, file: UploadFile = File(...), dataset_id: int | None = Form(default=None)):
    c = ctx(request)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded recording is empty.")
    return c.video.save_audio_recording(data, file.filename or "recording.webm", dataset_id=dataset_id)


@router.post("/audio/record")
async def save_recording_alias(request: Request, file: UploadFile = File(...), dataset_id: int | None = Form(default=None)):
    return await save_recording(request, file, dataset_id)


@router.post("/krita/export-package")
def krita_export_package(payload: KritaExportRequest, request: Request):
    c = ctx(request)
    item = c.media.get(payload.media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    source = Path(item.path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Source file does not exist")
    base_dir = Path(payload.output_dir).expanduser().resolve() if payload.output_dir else c.paths.outputs / "krita_packages"
    package_dir = base_dir / f"media_{item.id}_{source.stem}"
    package_dir.mkdir(parents=True, exist_ok=True)
    editable = package_dir / source.name
    shutil.copy2(source, editable)
    sidecars: list[str] = []
    if payload.include_sidecars:
        for suffix in (".txt", ".caption", ".json"):
            candidate = source.with_suffix(suffix)
            if candidate.exists():
                target = package_dir / candidate.name
                shutil.copy2(candidate, target)
                sidecars.append(str(target))
    manifest = {
        "source_media_id": item.id,
        "source_path": item.path,
        "editable_path": str(editable),
        "package_dir": str(package_dir),
        "width": item.width,
        "height": item.height,
        "tags": item.tags,
        "caption": item.caption,
        "sidecars": sidecars,
        "created_at": now_iso(),
        "note": "Open editable_path in Krita, save an edited copy, then import the edited file.",
    }
    manifest_path = package_dir / "edit_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {**manifest, "manifest_path": str(manifest_path)}


@router.post("/krita/handoff")
def krita_handoff(payload: KritaHandoffRequest, request: Request):
    c = ctx(request)
    if not payload.media_ids:
        raise HTTPException(status_code=400, detail="Select one or more images for Krita handoff.")
    base_dir = Path(payload.output_dir).expanduser().resolve() if payload.output_dir else c.paths.outputs / "krita_handoff"
    package_dir = base_dir / now_iso().replace(":", "-")
    package_dir.mkdir(parents=True, exist_ok=True)
    exported: list[dict[str, Any]] = []
    for media_id in payload.media_ids:
        item = c.media.get(int(media_id))
        if not item:
            continue
        source = Path(item.path)
        if not source.exists():
            continue
        target = package_dir / source.name
        shutil.copy2(source, target)
        sidecars: list[str] = []
        if payload.copy_sidecars:
            for suffix in (".txt", ".caption", ".json"):
                candidate = source.with_suffix(suffix)
                if candidate.exists():
                    sidecar_target = package_dir / candidate.name
                    shutil.copy2(candidate, sidecar_target)
                    sidecars.append(str(sidecar_target))
        exported.append({"media_id": item.id, "source_path": item.path, "editable_path": str(target), "sidecars": sidecars})
    manifest = {"created_at": now_iso(), "package_dir": str(package_dir), "items": exported}
    manifest_path = package_dir / "krita_handoff_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    launched = False
    if payload.launch_krita:
        exe = payload.krita_executable or getattr(c.settings, "krita_executable", None) or shutil.which("krita") or shutil.which("krita.exe")
        if exe:
            try:
                subprocess.Popen([exe, *[item["editable_path"] for item in exported]], shell=False)
                launched = True
            except Exception as exc:
                manifest["launch_error"] = str(exc)
    return {**manifest, "manifest_path": str(manifest_path), "launched": launched}


@router.post("/krita/import-edited")
def krita_import_edited(payload: KritaImportRequest, request: Request):
    c = ctx(request)
    source_item = c.media.get(payload.source_media_id)
    if not source_item:
        raise HTTPException(status_code=404, detail="Source media not found")
    edited = Path(payload.edited_path).expanduser().resolve()
    if not edited.exists():
        raise HTTPException(status_code=404, detail="Edited image does not exist")
    dataset_row = c.db.query_one("SELECT root_path FROM datasets WHERE id=?", (source_item.dataset_id,))
    if not dataset_row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    root = Path(dataset_row["root_path"])
    target = edited
    if payload.copy_to_dataset:
        edit_dir = root / "edited"
        edit_dir.mkdir(parents=True, exist_ok=True)
        target = edit_dir / f"{Path(source_item.path).stem}{payload.suffix or '_krita_edit'}{edited.suffix}"
        if target.resolve() != edited.resolve():
            shutil.copy2(edited, target)
    width, height = image_size(target)
    new_id = c.db.upsert_media({
        "dataset_id": source_item.dataset_id,
        "path": str(target),
        "relative_path": str(target.relative_to(root)) if str(target).startswith(str(root)) else target.name,
        "media_type": classify_media(target),
        "ext": target.suffix.lower().lstrip("."),
        "width": width,
        "height": height,
        "size_bytes": target.stat().st_size,
        "sha256": sha256_file(target),
        "phash": average_hash(target),
        "tag_path": str(target.with_suffix(".txt")),
        "caption_path": str(target.with_suffix(".caption")),
        "duplicate_of": None,
    })
    if payload.preserve_tags and source_item.tags:
        c.tags.set_tags_with_categories(new_id, source_item.tags, source_item.categories, source="krita_import", save_sidecar=True, profile_key=c.settings.default_tag_profile, order_strategy="retain")
    if payload.preserve_caption and source_item.caption:
        c.db.upsert_caption(new_id, source_item.caption, source="krita_import")
        target.with_suffix(".caption").write_text(source_item.caption, encoding="utf-8")
    return {"media_id": new_id, "path": str(target), "source_media_id": source_item.id}

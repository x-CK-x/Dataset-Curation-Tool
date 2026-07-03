from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse

from .deps import ctx
from ..utils import average_hash, classify_media, image_size, parse_tag_string, sha256_file

router = APIRouter(prefix="/krita", tags=["krita"])


class AnnotationPackagePayload(BaseModel):
    media_id: int
    annotation_ids: list[int] = Field(default_factory=list)
    output_dir: str | None = None
    include_masks: bool = True


class ImportAnnotationMaskPayload(BaseModel):
    media_id: int
    mask_path: str
    label: str = 'object'
    target_name: str = ''
    set_name: str = 'krita'
    source: str = 'krita'



@router.get("/status")
def status():
    return {"ok": True, "bridge": "krita_dataset_bridge", "protocol": 1}


@router.post("/import-image")
async def import_image_from_krita(
    request: Request,
    file: UploadFile = File(...),
    dataset_id: int | None = Form(None),
    tags: str = Form(""),
    caption: str = Form(""),
    profile_key: str = Form("e621"),
):
    c = ctx(request)
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in (file.filename or "krita_image.png"))[:180] or "krita_image.png"
    target = c.paths.outputs / "krita_bridge" / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(await file.read())
    result = {"saved": str(target), "dataset_id": dataset_id, "media_id": None}
    if dataset_id is not None:
        width, height = image_size(target)
        media_id = c.db.upsert_media({
            "dataset_id": dataset_id,
            "path": str(target),
            "relative_path": target.name,
            "media_type": classify_media(target),
            "ext": target.suffix.lower().lstrip('.'),
            "width": width,
            "height": height,
            "size_bytes": target.stat().st_size,
            "sha256": sha256_file(target),
            "phash": average_hash(target),
            "tag_path": str(target.with_suffix('.txt')),
            "caption_path": str(target.with_suffix('.caption')),
            "duplicate_of": None,
        })
        if tags.strip():
            c.tags.set_tags(media_id, parse_tag_string(tags), source="krita_bridge", save_sidecar=True, profile_key=profile_key, order_strategy="retain")
        if caption.strip():
            c.db.upsert_caption(media_id, caption.strip(), source="krita_bridge")
            target.with_suffix('.caption').write_text(caption.strip(), encoding='utf-8')
        result["media_id"] = media_id
    return result


@router.get("/plugin")
def plugin_zip(request: Request):
    path = ctx(request).paths.root / "integrations" / "krita_dataset_bridge.zip"
    if path.exists():
        return FileResponse(path, filename="krita_dataset_bridge.zip")
    return {"available": False, "path": str(path)}


@router.post("/annotation-package")
def annotation_package(payload: AnnotationPackagePayload, request: Request):
    return ctx(request).krita.export_annotation_package(payload.media_id, payload.annotation_ids or None, payload.output_dir, payload.include_masks)


@router.post("/import-annotation-mask")
def import_annotation_mask(payload: ImportAnnotationMaskPayload, request: Request):
    return ctx(request).reference.add_annotation(
        media_id=payload.media_id,
        label=payload.label,
        annotation_type='mask',
        mask_path=payload.mask_path,
        target_name=payload.target_name,
        set_name=payload.set_name,
        source=payload.source,
    )


@router.post("/import-mask")
async def import_mask_from_krita(
    request: Request,
    file: UploadFile = File(...),
    media_id: int = Form(...),
    label: str = Form('object'),
    target_name: str = Form(''),
    set_name: str = Form('krita'),
):
    c = ctx(request)
    safe_name = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in (file.filename or f'media_{media_id}_mask.png'))[:180] or f'media_{media_id}_mask.png'
    target = c.paths.outputs / 'krita_bridge' / 'masks' / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(await file.read())
    ann = c.reference.add_annotation(media_id=media_id, label=label, annotation_type='mask', mask_path=str(target), target_name=target_name, set_name=set_name, source='krita')
    return {'saved': str(target), **ann}

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/spatial", tags=["spatial-annotation"])


class SpatialProposalPayload(BaseModel):
    media_id: int
    label: str = "object"
    target_name: str = ""
    prompt: str = ""
    model_key: str
    threshold: float = 0.25
    save: bool = False
    device: str = "auto"
    options: dict[str, Any] = Field(default_factory=dict)


class ClearPreviewPayload(BaseModel):
    mask_paths: list[str] = Field(default_factory=list)


class SpatialLayerUpdatePayload(BaseModel):
    label: str | None = None
    target_name: str | None = None
    annotation_type: str | None = None
    bbox: dict[str, Any] | None = None
    polygon: list[list[float]] | None = None
    mask_path: str | None = None
    mask_data_url: str | None = None
    set_name: str | None = None
    source: str | None = None
    model_key: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] | None = None
    layer_name: str | None = None
    layer_order: int | None = None
    z_index: int | None = None
    visible: bool | None = None
    locked: bool | None = None
    opacity: float | None = None
    blend_mode: str | None = None
    color: str | None = None
    parent_ids: list[int] | None = None
    force: bool = False


class SpatialLayerDuplicatePayload(BaseModel):
    layer_name: str = ''


class SpatialLayerReorderPayload(BaseModel):
    media_id: int
    annotation_ids: list[int]
    task: str = ''


class SpatialLayerMergePayload(BaseModel):
    media_id: int
    annotation_ids: list[int]
    operation: str = 'union'
    label: str = ''
    layer_name: str = ''
    delete_sources: bool = False
    threshold: int = Field(default=1, ge=0, le=255)
    feather: int = Field(default=0, ge=0, le=128)
    grow: int = Field(default=0, ge=-128, le=128)
    base_annotation_id: int | None = None


class SpatialLayerDeletePayload(BaseModel):
    annotation_ids: list[int] = Field(default_factory=list)


class SpatialBlankMaskPayload(BaseModel):
    media_id: int
    label: str = 'blank_mask'
    layer_name: str = ''


class SpatialMaskCanvasPayload(BaseModel):
    media_id: int
    mask_data_url: str
    annotation_id: int | None = None
    label: str = 'object'
    target_name: str = ''
    source: str = 'user'
    model_key: str = ''
    metadata: dict[str, Any] = Field(default_factory=dict)
    layer_name: str = ''
    opacity: float = 0.55
    color: str = '#22c55e'


class SpatialMagicSelectPayload(BaseModel):
    media_id: int
    x: float
    y: float
    method: str = 'flood_fill'
    tolerance: int = 24
    connectivity: int = 8
    bbox: dict[str, Any] = Field(default_factory=dict)
    iterations: int = 5
    radius_ratio: float = 0.22
    feather: int = 0
    grow: int = Field(default=0, ge=-128, le=128)
    invert: bool = False


class SpatialPersistPreviewPayload(BaseModel):
    media_id: int
    proposals: list[dict[str, Any]] = Field(default_factory=list)
    label: str = ''


_DETECTION_TYPES = {"bbox", "obb", "rotated_bbox"}
_SEGMENTATION_TYPES = {"mask", "polygon", "bbox_mask", "segmentation"}


def _matches_task(row: dict[str, Any], task: Literal["detection", "segmentation"]) -> bool:
    caps = set(row.get("capabilities") or [])
    kind = str(row.get("kind") or "").lower()
    name = str(row.get("name") or "")
    if name == "custom-yolo-local":
        return True
    if task == "detection":
        # Segmentation and pose rows are intentionally excluded even if they also
        # emit boxes. This preserves a clear one-task/one-node contract.
        if kind in {"segmentation", "pose2d", "pose3d"} or caps & {"segment", "mask", "video_mask", "pose", "pose2d", "pose3d"}:
            return False
        return kind in {"detection", "detector"} or bool(caps & {"detect", "bbox", "open_vocabulary"})
    if name == "custom-sam-local":
        return True
    if kind in {"pose2d", "pose3d"} or caps & {"pose", "pose2d", "pose3d"}:
        return False
    return kind == "segmentation" or bool(caps & {"segment", "mask", "video_mask"})


def _runnable(row: dict[str, Any], task: Literal["detection", "segmentation"]) -> bool:
    provider = str(row.get("provider") or "").lower()
    name = str(row.get("name") or "")
    caps = set(row.get("capabilities") or [])
    if provider in {"ultralytics", "direct", "openai", "openrouter", "anthropic"}:
        return True
    if provider == "local":
        return name in {"custom-yolo-local", "custom-sam-local"}
    if task == "detection" and name in {"grounding-dino-tiny", "owlv2-reference-detector", "detr-resnet50-detector"}:
        return False
    return provider == "builtin" and "annotation" in caps


def _catalog(request: Request, task: Literal["detection", "segmentation"], include_staged: bool = False) -> list[dict[str, Any]]:
    rows = []
    for row in ctx(request).reference.annotation_model_catalog():
        if not _matches_task(row, task):
            continue
        runnable = _runnable(row, task)
        if not include_staged and not runnable:
            continue
        rows.append(row | {"spatial_task": task, "runnable_adapter": runnable})
    return rows


def _model_allowed(request: Request, task: Literal["detection", "segmentation"], model_key: str) -> bool:
    return any(row.get("name") == model_key for row in _catalog(request, task, include_staged=True))


def _save_proposals(request: Request, payload: SpatialProposalPayload, proposals: list[dict[str, Any]], task: Literal["detection", "segmentation"]) -> list[dict[str, Any]]:
    service = ctx(request).reference
    saved: list[dict[str, Any]] = []
    for proposal in proposals:
        if task == "detection":
            bbox = proposal.get("bbox") or {}
            if not bbox:
                continue
            saved.append(service.add_annotation(
                media_id=payload.media_id,
                label=proposal.get("label") or payload.label,
                target_name=proposal.get("target_name") or payload.target_name,
                annotation_type="bbox",
                bbox=bbox,
                polygon=[],
                mask_path="",
                source=proposal.get("source") or "model",
                model_key=proposal.get("model_key") or payload.model_key,
                confidence=proposal.get("confidence"),
                metadata=(proposal.get("metadata") or {}) | {"spatial_task": "detection"},
            ))
        else:
            mask_path = str(proposal.get("mask_path") or "")
            polygon = proposal.get("polygon") or []
            if not mask_path and len(polygon) < 3:
                continue
            saved.append(service.add_annotation(
                media_id=payload.media_id,
                label=proposal.get("label") or payload.label,
                target_name=proposal.get("target_name") or payload.target_name,
                annotation_type="mask" if mask_path else "polygon",
                bbox=proposal.get("bbox") or {},
                polygon=polygon,
                mask_path=mask_path,
                source=proposal.get("source") or "model",
                model_key=proposal.get("model_key") or payload.model_key,
                confidence=proposal.get("confidence"),
                metadata=(proposal.get("metadata") or {}) | {"spatial_task": "segmentation"},
            ))
    return saved


def _propose(request: Request, payload: SpatialProposalPayload, task: Literal["detection", "segmentation"]):
    if not _model_allowed(request, task, payload.model_key):
        return {
            "ok": False,
            "media_id": payload.media_id,
            "task": task,
            "proposals": [],
            "saved": [],
            "count": 0,
            "error": f"Model {payload.model_key!r} is not available in the {task} workflow. Choose a model from that tab's dedicated model list.",
        }
    options = dict(payload.options or {})
    options["spatial_task"] = task
    if payload.model_key == "custom-yolo-local":
        options.setdefault("custom_model_type", "yolo")
    result = ctx(request).reference.propose_annotation(
        media_id=payload.media_id,
        label=payload.label,
        target_name=payload.target_name,
        prompt=payload.prompt,
        model_key=payload.model_key,
        threshold=payload.threshold,
        annotation_type="bbox" if task == "detection" else "mask",
        save=False,
        create_mask=task == "segmentation",
        source="model",
        device=payload.device,
        options=options,
    )
    if not result.get("ok"):
        return result | {"task": task}

    proposals: list[dict[str, Any]] = []
    if task == "detection":
        for proposal in result.get("proposals") or []:
            if not proposal.get("bbox"):
                continue
            # Detection previews contain boxes only. A segmentation model cannot
            # leak a mask into this task even if invoked through a custom adapter.
            proposals.append(proposal | {"annotation_type": "bbox", "polygon": [], "mask_path": ""})
    else:
        for proposal in result.get("proposals") or []:
            if proposal.get("mask_path") or len(proposal.get("polygon") or []) >= 3:
                proposals.append(proposal | {"annotation_type": "mask" if proposal.get("mask_path") else "polygon"})
        if not proposals:
            return {
                "ok": False,
                "media_id": payload.media_id,
                "task": task,
                "proposals": [],
                "saved": [],
                "count": 0,
                "error": f"Model {payload.model_key} returned no actual mask or polygon. No bbox-only result was accepted as segmentation.",
                "model_status": result.get("model_status"),
            "conditioning": result.get("conditioning"),
            "warnings": result.get("warnings") or [],
            }
    saved = _save_proposals(request, payload, proposals, task) if payload.save else []
    return {
        "ok": True,
        "media_id": payload.media_id,
        "task": task,
        "proposals": proposals,
        "saved": saved,
        "count": len(proposals),
        "model_status": result.get("model_status"),
        "conditioning": result.get("conditioning"),
        "warnings": result.get("warnings") or [],
        "diagnostics": result.get("diagnostics") or {},
    }


@router.get("/detection/models")
def detection_models(request: Request, include_staged: bool = False):
    return _catalog(request, "detection", include_staged)


@router.get("/segmentation/models")
def segmentation_models(request: Request, include_staged: bool = False):
    return _catalog(request, "segmentation", include_staged)


@router.get("/detection/model-classes")
def detection_model_classes(
    request: Request,
    model_key: str,
    local_model_path: str | None = None,
    custom_model_type: str = "yolo",
    q: str = "",
    limit: int = 500,
):
    if not _model_allowed(request, "detection", model_key):
        raise HTTPException(status_code=400, detail=f"Model {model_key!r} is not available in the detection workflow.")
    options = {"custom_model_type": custom_model_type}
    if local_model_path:
        options["local_model_path"] = local_model_path
    return ctx(request).reference.annotation_model_classes(model_key, options, query=q, limit=limit)


@router.get("/segmentation/model-classes")
def segmentation_model_classes(
    request: Request,
    model_key: str,
    local_model_path: str | None = None,
    custom_model_type: str = "auto",
    q: str = "",
    limit: int = 500,
):
    if not _model_allowed(request, "segmentation", model_key):
        raise HTTPException(status_code=400, detail=f"Model {model_key!r} is not available in the segmentation workflow.")
    options = {"custom_model_type": custom_model_type}
    if local_model_path:
        options["local_model_path"] = local_model_path
    return ctx(request).reference.annotation_model_classes(model_key, options, query=q, limit=limit)


@router.post("/detection/propose")
def detection_propose(payload: SpatialProposalPayload, request: Request):
    try:
        return _propose(request, payload, "detection")
    except Exception as exc:
        return {"ok": False, "media_id": payload.media_id, "task": "detection", "proposals": [], "saved": [], "count": 0, "error": str(exc)}


@router.post("/segmentation/propose")
def segmentation_propose(payload: SpatialProposalPayload, request: Request):
    try:
        return _propose(request, payload, "segmentation")
    except Exception as exc:
        return {"ok": False, "media_id": payload.media_id, "task": "segmentation", "proposals": [], "saved": [], "count": 0, "error": str(exc)}


@router.post("/detection/clear-preview")
def clear_detection_preview(payload: ClearPreviewPayload, request: Request):
    return ctx(request).reference.clear_preview_masks(payload.mask_paths) | {"task": "detection"}


@router.post("/segmentation/clear-preview")
def clear_segmentation_preview(payload: ClearPreviewPayload, request: Request):
    return ctx(request).reference.clear_preview_masks(payload.mask_paths) | {"task": "segmentation"}


@router.delete("/detection/generated/{media_id}")
def clear_generated_detection_annotations(media_id: int, request: Request, model_key: str = ""):
    return ctx(request).reference.clear_generated_annotations(media_id, "detection", model_key)


@router.delete("/segmentation/generated/{media_id}")
def clear_generated_segmentation_annotations(media_id: int, request: Request, model_key: str = ""):
    return ctx(request).reference.clear_generated_annotations(media_id, "segmentation", model_key)


@router.get("/detection/state/{media_id}")
def detection_state(media_id: int, request: Request):
    c = ctx(request)
    media = c.media.get(media_id)
    rows = [row for row in c.reference.list_annotations(media_id=media_id, limit=5000) if str(row.get("annotation_type") or "").lower() in _DETECTION_TYPES]
    return {"media": media.model_dump() if media else None, "annotations": rows}


@router.get("/segmentation/state/{media_id}")
def segmentation_state(media_id: int, request: Request):
    c = ctx(request)
    media = c.media.get(media_id)
    rows = [row for row in c.reference.list_annotations(media_id=media_id, limit=5000) if str(row.get("annotation_type") or "").lower() in _SEGMENTATION_TYPES]
    return {"media": media.model_dump() if media else None, "annotations": rows}


@router.get("/layers/{annotation_id}")
def get_spatial_layer(annotation_id: int, request: Request):
    row = ctx(request).reference.get_annotation(annotation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Annotation layer was not found.")
    return row


@router.patch("/layers/{annotation_id}")
def update_spatial_layer(annotation_id: int, payload: SpatialLayerUpdatePayload, request: Request):
    changes = payload.model_dump(exclude_none=True)
    force = bool(changes.pop('force', False))
    if 'layer_order' in changes and 'z_index' not in changes:
        changes['z_index'] = changes.pop('layer_order')
    try:
        return ctx(request).reference.update_annotation(annotation_id, changes, force=force, reason='spatial_layer_editor')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/layers/{annotation_id}/duplicate")
def duplicate_spatial_layer(annotation_id: int, payload: SpatialLayerDuplicatePayload, request: Request):
    try:
        return ctx(request).reference.duplicate_annotation_layer(annotation_id, layer_name=payload.layer_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/layers/delete")
def delete_spatial_layers(payload: SpatialLayerDeletePayload, request: Request):
    results = [ctx(request).reference.delete_annotation(annotation_id) for annotation_id in payload.annotation_ids]
    return {
        'requested': len(payload.annotation_ids),
        'deleted': sum(int(row.get('deleted') or 0) for row in results),
        'results': results,
    }


@router.post("/layers/reorder")
def reorder_spatial_layers(payload: SpatialLayerReorderPayload, request: Request):
    try:
        return ctx(request).reference.reorder_annotation_layers(payload.media_id, payload.annotation_ids, payload.task)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/layers/{annotation_id}/revisions")
def spatial_layer_revisions(annotation_id: int, request: Request, limit: int = 50):
    return ctx(request).reference.list_annotation_revisions(annotation_id, limit)


@router.post("/layers/{annotation_id}/revisions/{revision_id}/restore")
def restore_spatial_layer_revision(annotation_id: int, revision_id: int, request: Request):
    try:
        return ctx(request).reference.restore_annotation_revision(annotation_id, revision_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/detection/layers/merge")
def merge_detection_layers(payload: SpatialLayerMergePayload, request: Request):
    try:
        return ctx(request).reference.merge_bbox_layers(
            payload.media_id, payload.annotation_ids, payload.operation,
            label=payload.label or 'combined_box', layer_name=payload.layer_name,
            delete_sources=payload.delete_sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/segmentation/layers/merge")
def merge_segmentation_layers(payload: SpatialLayerMergePayload, request: Request):
    try:
        annotation_ids = list(payload.annotation_ids)
        if payload.base_annotation_id is not None and payload.base_annotation_id in annotation_ids:
            annotation_ids = [payload.base_annotation_id, *[value for value in annotation_ids if value != payload.base_annotation_id]]
        return ctx(request).reference.merge_mask_layers(
            payload.media_id, annotation_ids, payload.operation,
            label=payload.label or 'combined_mask', layer_name=payload.layer_name,
            delete_sources=payload.delete_sources, threshold=payload.threshold,
            feather=payload.feather, grow=payload.grow,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/segmentation/save-mask-layer")
def save_segmentation_mask_layer(payload: SpatialMaskCanvasPayload, request: Request):
    try:
        values = payload.model_dump()
        values['mask_data'] = values.pop('mask_data_url')
        return ctx(request).reference.save_raster_mask_layer(**values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/segmentation/layers/blank")
def create_blank_segmentation_layer(payload: SpatialBlankMaskPayload, request: Request):
    try:
        return ctx(request).reference.create_blank_mask_layer(payload.media_id, payload.label, payload.layer_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/segmentation/magic-select")
def segmentation_magic_select(payload: SpatialMagicSelectPayload, request: Request):
    try:
        return ctx(request).reference.magic_select(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/detection/persist-preview")
def persist_detection_preview(payload: SpatialPersistPreviewPayload, request: Request):
    try:
        saved = ctx(request).reference.persist_spatial_proposals(payload.media_id, 'detection', payload.proposals, payload.label)
        return {'saved': saved, 'count': len(saved)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/segmentation/persist-preview")
def persist_segmentation_preview(payload: SpatialPersistPreviewPayload, request: Request):
    try:
        saved = ctx(request).reference.persist_spatial_proposals(payload.media_id, 'segmentation', payload.proposals, payload.label)
        return {'saved': saved, 'count': len(saved)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/mask-preview")
def mask_preview(path: str, request: Request):
    c = ctx(request)
    candidate = Path(path).expanduser()
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Mask file was not found.")
    try:
        resolved = candidate.resolve()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    annotation_root = c.reference.annotations_dir.resolve()
    allowed = False
    try:
        resolved.relative_to(annotation_root)
        allowed = True
    except ValueError:
        row = c.db.query_one("SELECT id FROM annotations WHERE mask_path=? LIMIT 1", (str(resolved),))
        allowed = bool(row)
    if not allowed:
        raise HTTPException(status_code=403, detail="Mask preview path is outside the annotation workspace.")
    return FileResponse(resolved)

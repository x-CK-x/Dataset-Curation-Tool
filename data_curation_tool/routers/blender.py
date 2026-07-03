from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix='/blender', tags=['blender-bridge'])


class BlenderPosePayload(BaseModel):
    media_id: int
    label: str = 'pose3d'
    target_name: str = ''
    set_name: str = 'default'
    keypoints_3d: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[list[Any]] = Field(default_factory=list)
    frames: list[dict[str, Any]] = Field(default_factory=list)
    rig_name: str = ''
    source: str = 'blender'


@router.get('/plugin')
def blender_plugin(request: Request):
    plugin = ctx(request).paths.root / 'integrations' / 'blender_dataset_bridge.zip'
    if not plugin.exists():
        raise HTTPException(status_code=404, detail='Blender bridge plugin ZIP not found')
    return FileResponse(str(plugin), filename='blender_dataset_bridge.zip')


@router.post('/import-pose')
def import_blender_pose(payload: BlenderPosePayload, request: Request):
    c = ctx(request)
    metadata = {
        'keypoints_3d': payload.keypoints_3d,
        'edges': payload.edges,
        'frames': payload.frames,
        'rig_name': payload.rig_name,
        'source_app': 'Blender',
    }
    return c.reference.add_annotation(
        media_id=payload.media_id,
        label=payload.label or payload.target_name or 'pose3d',
        annotation_type='animation_pose' if payload.frames else 'pose3d',
        bbox={},
        polygon=[],
        mask_path='',
        target_name=payload.target_name,
        set_name=payload.set_name,
        source=payload.source,
        model_key='blender-bridge',
        confidence=None,
        metadata=metadata,
    )


@router.get('/pose/{media_id}')
def export_pose(media_id: int, request: Request, annotation_id: int | None = None):
    c = ctx(request)
    row = c.reference.get_annotation(int(annotation_id)) if annotation_id else None
    if row is not None and int(row.get('media_id') or 0) != int(media_id):
        raise HTTPException(status_code=400, detail='annotation_id does not belong to media_id')
    if row is None:
        poses = [item for item in c.reference.list_annotations(media_id=int(media_id), limit=1000)
                 if str(item.get('annotation_type') or '').lower() in {'pose2d', 'pose3d', 'animation_pose'}]
        row = poses[-1] if poses else None
    if not row:
        raise HTTPException(status_code=404, detail='No saved pose annotation was found for this media item')
    metadata = row.get('metadata') or {}
    return {
        'annotation_id': row.get('id'),
        'media_id': int(media_id),
        'label': row.get('label'),
        'annotation_type': row.get('annotation_type'),
        'target_name': row.get('target_name'),
        'keypoints_2d': metadata.get('keypoints_2d') or [],
        'keypoints_3d': metadata.get('keypoints_3d') or [],
        'edges': metadata.get('edges') or [],
        'frames': metadata.get('frames') or [],
        'skeleton_template': metadata.get('skeleton_template') or metadata.get('template') or '',
        'metadata': metadata,
    }


@router.get('/assets')
def blender_assets(request: Request, limit: int = 200):
    return ctx(request).three_d.list_assets(limit=limit)


@router.get('/latest-asset')
def latest_blender_asset(request: Request):
    rows = ctx(request).three_d.list_assets(limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail='No generated/imported 3D asset is available')
    return rows[0]

from __future__ import annotations

from typing import Any
import json
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from .deps import ctx
from ..schemas import ModelDownloadRequest
from ..services.pose_models import list_skeleton_templates

router = APIRouter(prefix='/reference', tags=['reference-finder'])


class TargetPayload(BaseModel):
    name: str
    notes: str = ''


class ReferenceImagePayload(BaseModel):
    target_name: str
    path: str
    reference_set_name: str = 'default'


class ReferenceRunPayload(BaseModel):
    target_name: str
    reference_paths: list[str] = Field(default_factory=list)
    reference_set_name: str = 'default'
    dataset_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    folder: str = ''
    recursive: bool = True
    pipeline: str = 'demo_colorhash'
    threshold: float = 0.55
    duplicate_policy: str = 'reuse_verified_or_cached'
    save_all_annotations: bool = False
    run_name: str = ''
    notes: str = ''


class CharacterProfilePayload(BaseModel):
    target_name: str
    reference_paths: list[str] = Field(default_factory=list)
    reference_set_name: str = 'default'
    profile_name: str = 'default'
    pipeline: str = 'active_memory_colorhash'
    include_saved_references: bool = True
    include_verified_positive_memory: bool = True
    include_verified_negative_memory: bool = True
    negative_memory_penalty: float = 0.35
    notes: str = ''


class CharacterPrunePayload(ReferenceRunPayload):
    include_verified_positive_memory: bool = True
    include_verified_negative_memory: bool = True
    include_saved_references: bool = True
    negative_memory_penalty: float = 0.35


class VerifyPayload(BaseModel):
    detection_id: int
    label: str
    notes: str = ''


class QueryPayload(BaseModel):
    target_name: str
    query: str
    baseline_query: str = ''
    dataset_id: int | None = None
    scope: str = 'all_images'
    store: bool = True


class QueryManyPayload(BaseModel):
    target_name: str
    queries: list[str] = Field(default_factory=list)
    baseline_query: str = ''
    dataset_id: int | None = None
    scope: str = 'all_images'


class AnnotationPayload(BaseModel):
    media_id: int
    label: str = 'object'
    annotation_type: str = 'bbox'
    bbox: dict[str, Any] = Field(default_factory=dict)
    polygon: list[list[float]] = Field(default_factory=list)
    mask_path: str = ''
    target_name: str = ''
    set_name: str = 'default'
    source: str = 'user'
    model_key: str = ''
    confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    layer_name: str = ''
    layer_order: int | None = None
    z_index: int | None = None
    visible: bool = True
    locked: bool = False
    opacity: float = 0.55
    blend_mode: str = 'normal'
    color: str = '#22c55e'
    parent_ids: list[int] = Field(default_factory=list)


class AnnotationModelLoadPayload(BaseModel):
    model_key: str
    device: str = 'auto'
    options: dict[str, Any] = Field(default_factory=dict)


class AnnotationModelDownloadPayload(BaseModel):
    model_key: str
    dry_run: bool = False
    force_download: bool = False
    parallel_downloads: int = 8


class AnnotationDependencyInstallPayload(BaseModel):
    include_sam2: bool = False
    extra_args: list[str] = Field(default_factory=list)


class AnnotationModelSetupPayload(BaseModel):
    model_key: str
    device: str = 'auto'
    force_download: bool = False
    parallel_downloads: int = Field(default=8, ge=1, le=32)
    options: dict[str, Any] = Field(default_factory=dict)


class PoseDependencyInstallPayload(BaseModel):
    family: str = 'mediapipe'
    extra_args: list[str] = Field(default_factory=list)


class AnnotationProposalPayload(BaseModel):
    media_id: int
    label: str = 'object'
    target_name: str = ''
    prompt: str = ''
    model_key: str = 'demo_center_bbox'
    threshold: float = 0.25
    annotation_type: str = 'bbox'
    save: bool = False
    create_mask: bool = False
    source: str = 'model'
    device: str = 'auto'
    options: dict[str, Any] = Field(default_factory=dict)


class TrainingSetPayload(BaseModel):
    name: str
    query: str = ''
    dataset_id: int | None = None
    train_ratio: float = 0.9
    seed: int = 42
    description: str = ''


class YoloExportPayload(BaseModel):
    training_set_id: int
    output_dir: str | None = None
    task: str = 'detection'
    label_filter: str = ''


class TrainingJobPayload(BaseModel):
    name: str
    task: str
    model_key: str = ''
    training_set_id: int | None = None
    config: dict[str, Any] = Field(default_factory=dict)


@router.get('/status')
def status(request: Request):
    return ctx(request).reference.status()


@router.get('/character-methods')
def character_methods(request: Request):
    return ctx(request).reference.character_methods()


@router.get('/character-profiles')
def character_profiles(request: Request, target_name: str | None = None):
    return ctx(request).reference.list_character_profiles(target_name)


@router.post('/character-profiles/build')
def build_character_profile(payload: CharacterProfilePayload, request: Request):
    return ctx(request).reference.build_character_profile(payload.model_dump())


@router.post('/character-prune')
def character_prune(payload: CharacterPrunePayload, request: Request):
    c = ctx(request)

    def task(progress):
        return c.reference.run_character_prune(payload.model_dump(), progress)

    job_id = c.jobs.submit('character_reference_prune', payload.model_dump(), task)
    return {'job_id': job_id, 'status': 'queued'}


@router.post('/character-prune-now')
def character_prune_now(payload: CharacterPrunePayload, request: Request):
    return ctx(request).reference.run_character_prune(payload.model_dump())


@router.get('/targets')
def list_targets(request: Request):
    return ctx(request).reference.list_targets()


@router.post('/targets')
def upsert_target(payload: TargetPayload, request: Request):
    target_id = ctx(request).reference.upsert_target(payload.name, payload.notes)
    return {'target_id': target_id, 'name': payload.name}


@router.get('/references')
def list_references(request: Request, target_name: str | None = None):
    return ctx(request).reference.list_references(target_name)


@router.post('/references')
def add_reference(payload: ReferenceImagePayload, request: Request):
    return ctx(request).reference.add_reference(payload.target_name, payload.path, payload.reference_set_name)


@router.post('/run')
def run_reference_search(payload: ReferenceRunPayload, request: Request):
    c = ctx(request)

    def task(progress):
        return c.reference.run_search(payload.model_dump(), None, progress)

    job_id = c.jobs.submit('reference_search', payload.model_dump(), task)
    return {'job_id': job_id, 'status': 'queued'}


@router.get('/runs')
def list_runs(request: Request, target_name: str | None = None, limit: int = 100):
    return ctx(request).reference.list_runs(target_name, limit)


@router.get('/results')
def list_results(request: Request, run_id: int | None = None, target_name: str | None = None, decision: str | None = None, limit: int = 200):
    return ctx(request).reference.list_results(run_id, target_name, decision, limit)


@router.post('/verify')
def verify(payload: VerifyPayload, request: Request):
    return ctx(request).reference.verify(payload.detection_id, payload.label, payload.notes)


@router.post('/queries/evaluate')
def evaluate_query(payload: QueryPayload, request: Request):
    return ctx(request).reference.evaluate_query(payload.target_name, payload.query, payload.baseline_query, payload.dataset_id, payload.scope, payload.store)


@router.post('/queries/evaluate-many')
def evaluate_many(payload: QueryManyPayload, request: Request):
    return ctx(request).reference.evaluate_many_queries(payload.target_name, payload.queries, payload.baseline_query, payload.dataset_id, payload.scope)


@router.get('/queries/suggest')
def suggest_queries(request: Request, target_name: str, dataset_id: int | None = None, limit: int = 30):
    return ctx(request).reference.suggest_queries(target_name, dataset_id, limit)


@router.get('/annotations/model-catalog')
def annotation_model_catalog(request: Request):
    return ctx(request).reference.annotation_model_catalog()


@router.post('/annotations/load-model')
def load_annotation_model(payload: AnnotationModelLoadPayload, request: Request):
    c = ctx(request)
    c.models.lifecycle.update(payload.model_key, 'load', state='running', progress=0.05, message='Validating/loading annotation model')
    try:
        status = c.reference.load_annotation_model(payload.model_key, payload.device, payload.options)
        c.models.lifecycle.complete(payload.model_key, 'load', message='Annotation model validated/loaded', result=status)
        return status
    except Exception as exc:
        c.models.lifecycle.fail(payload.model_key, 'load', exc)
        raise


@router.post('/annotations/install-deps')
def install_annotation_dependencies(payload: AnnotationDependencyInstallPayload, request: Request):
    c = ctx(request)

    def task(progress):
        root = c.paths.root
        req = root / 'requirements-annotation-models.txt'
        if not req.exists():
            raise RuntimeError(f'Missing requirements file: {req}')
        cmd = [sys.executable, '-m', 'pip', 'install', '-r', str(req)]
        if payload.include_sam2:
            cmd += ['git+https://github.com/facebookresearch/sam2.git']
        cmd += list(payload.extra_args or [])
        if progress:
            progress(0.05, 'Installing annotation model dependencies')
        proc = subprocess.run(cmd, cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if progress:
            progress(1.0 if proc.returncode == 0 else 0.95, 'Dependency install finished')
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout[-6000:])
        return {'ok': True, 'command': cmd, 'output_tail': proc.stdout[-6000:]}

    job_id = c.jobs.submit('annotation_dependency_install', payload.model_dump(), task)
    return {'job_id': job_id, 'status': 'queued'}


@router.post('/annotations/setup-model')
def setup_annotation_model(payload: AnnotationModelSetupPayload, request: Request):
    """Install the selected SAM-family runtime, download weights, and validate it."""
    c = ctx(request)
    model_key = str(payload.model_key or '').strip()
    if model_key.startswith('sam-hq-'):
        family = 'sam_hq'
        install = [sys.executable, '-m', 'pip', 'install', '--upgrade', 'segment-anything-hq']
    elif model_key.startswith('sam2'):
        family = 'sam2'
        install = [sys.executable, '-m', 'pip', 'install', '--upgrade', 'git+https://github.com/facebookresearch/sam2.git']
    elif model_key.startswith('sam-'):
        family = 'sam'
        install = [sys.executable, '-m', 'pip', 'install', '--upgrade', 'git+https://github.com/facebookresearch/segment-anything.git']
    else:
        return {'ok': False, 'error': 'The setup assistant currently supports SAM, SAM-HQ, and SAM2.1 model rows.'}

    def task(progress):
        lifecycle_stage = 'load'
        try:
            if progress:
                progress(0.03, f'Installing {family} runtime')
            proc = subprocess.run(install, cwd=str(c.paths.root), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            install_result = {'command': install, 'returncode': proc.returncode, 'output_tail': proc.stdout[-10000:]}
            if proc.returncode != 0:
                raise RuntimeError(proc.stdout[-10000:])
            if progress:
                progress(0.28, f'Downloading {model_key} checkpoint')

            def download_progress(value, message):
                if progress:
                    progress(0.28 + max(0.0, min(1.0, float(value or 0.0))) * 0.57, message)

            lifecycle_stage = 'download'
            c.models.lifecycle.update(model_key, 'download', state='running', progress=0.0, message='Downloading annotation checkpoint')
            lifecycle_download_progress = c.models.lifecycle.progress_callback(model_key, 'download', download_progress)
            download_result = c.models.registry.download_model(
                name=model_key,
                token=c.settings.huggingface_token,
                dry_run=False,
                force_download=payload.force_download,
                progress=lifecycle_download_progress,
                parallel_downloads=max(1, int(payload.parallel_downloads or 8)),
            )
            c.models.lifecycle.complete(model_key, 'download', message='Annotation checkpoint downloaded', result=download_result)
            if progress:
                progress(0.90, 'Validating runtime and checkpoint pairing')
            lifecycle_stage = 'load'
            c.models.lifecycle.update(model_key, 'load', state='running', progress=0.15, message='Validating/loading annotation model')
            status = c.reference.load_annotation_model(model_key, payload.device, payload.options)
            c.models.lifecycle.complete(model_key, 'load', message='Annotation model validated/loaded', result=status)
            if progress:
                progress(1.0, f'{model_key} is ready')
            return {
                'ok': True,
                'family': family,
                'model_key': model_key,
                'install': install_result,
                'download': download_result,
                'model_status': status,
                'windows_note': 'SAM2 installation is generally more reliable in WSL/Linux.' if family == 'sam2' and sys.platform.startswith('win') else '',
            }
        except Exception as exc:
            c.models.lifecycle.fail(model_key, lifecycle_stage, exc)
            raise

    job_id = c.jobs.submit('annotation_model_setup', {'model_key': model_key, 'device': payload.device, 'family': family}, task)
    return {'ok': True, 'job_id': job_id, 'status': 'queued', 'family': family, 'model_key': model_key}




class CustomSkeletonPayload(BaseModel):
    key: str
    label: str = "Custom skeleton"
    dimension: str = "mixed"
    names: list[str] = Field(default_factory=list)
    edges: list[dict[str, Any] | list[Any]] = Field(default_factory=list)
    groups: list[dict[str, Any]] = Field(default_factory=list)
    notes: str = ""


def _custom_skeleton_path(request: Request) -> Path:
    c = ctx(request)
    path = c.paths.runtime / "custom_skeleton_templates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_custom_skeletons(request: Request) -> list[dict[str, Any]]:
    path = _custom_skeleton_path(request)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("templates") or [])
    except Exception:
        return []


def _normalize_custom_edges(edges: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, edge in enumerate(edges or []):
        if isinstance(edge, dict):
            a = edge.get("from", edge.get("a", edge.get("start")))
            b = edge.get("to", edge.get("b", edge.get("end")))
            label = str(edge.get("label") or f"edge_{index}")
            group = str(edge.get("group") or "default")
        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
            a, b = edge[0], edge[1]
            label = str(edge[2]) if len(edge) > 2 else f"edge_{index}"
            group = str(edge[3]) if len(edge) > 3 else "default"
        else:
            continue
        if a is None or b is None or str(a) == str(b):
            continue
        out.append({"from": a, "to": b, "label": label, "group": group})
    return out

@router.get('/annotations/pose-templates')
def pose_templates(request: Request):
    return list_skeleton_templates() + _load_custom_skeletons(request)


@router.get('/annotations/custom-skeletons')
def custom_skeletons(request: Request):
    return {'templates': _load_custom_skeletons(request)}


@router.post('/annotations/custom-skeletons')
def save_custom_skeleton(payload: CustomSkeletonPayload, request: Request):
    key = ''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in payload.key.strip().lower()) or 'custom_skeleton'
    item = {'key': key, 'label': payload.label or key, 'dimension': payload.dimension or 'mixed', 'names': list(payload.names or []), 'edges': _normalize_custom_edges(payload.edges), 'groups': list(payload.groups or []), 'notes': payload.notes or ''}
    path = _custom_skeleton_path(request)
    existing = [row for row in _load_custom_skeletons(request) if row.get('key') != key]
    existing.append(item)
    path.write_text(json.dumps({'templates': existing}, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'ok': True, 'template': item, 'path': str(path)}


@router.post('/annotations/install-pose-deps')
def install_pose_dependencies(payload: PoseDependencyInstallPayload, request: Request):
    c = ctx(request)
    requested_family = str(payload.family or 'basic').strip().lower()
    aliases = {'all': 'basic', 'default': 'basic', 'mmpose-full': 'mmpose', 'all-full': 'all-full'}
    family = aliases.get(requested_family, requested_family)
    if family not in {'ultralytics', 'mediapipe', 'mmpose', 'basic', 'all-full'}:
        return {'ok': False, 'error': f'Unknown pose runtime family: {requested_family}. Use basic, ultralytics, mediapipe, mmpose, or all-full.'}

    def task(progress):
        commands: list[list[str]] = []
        pip_common = ['--timeout', '120', '--retries', '3']
        if family in {'ultralytics', 'basic', 'all-full'}:
            commands.append([sys.executable, '-m', 'pip', 'install', '--upgrade', *pip_common, 'ultralytics', *list(payload.extra_args or [])])
        if family in {'mediapipe', 'basic', 'all-full'}:
            commands.append([sys.executable, '-m', 'pip', 'install', '--upgrade', *pip_common, 'mediapipe>=0.10.14', *list(payload.extra_args or [])])
        if family in {'mmpose', 'all-full'}:
            commands.append([sys.executable, '-m', 'pip', 'install', '--upgrade', *pip_common, 'openmim>=0.3.9'])
            commands.append([sys.executable, '-m', 'mim', 'install', 'mmengine>=0.10.0', 'mmcv>=2.0.1', 'mmdet>=3.0.0', 'mmpose>=1.3.0', *list(payload.extra_args or [])])
        outputs = []
        for index, command in enumerate(commands):
            if progress:
                progress(index / max(1, len(commands)), f'Installing {family} pose runtime ({index + 1}/{len(commands)})')
            proc = subprocess.run(command, cwd=str(c.paths.root), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=3600)
            outputs.append({'command': command, 'returncode': proc.returncode, 'output_tail': proc.stdout[-20000:]})
            if proc.returncode != 0:
                raise RuntimeError(proc.stdout[-20000:])
        if progress:
            progress(1.0, f'{family} pose runtime installation finished')
        return {'ok': True, 'family': family, 'requested_family': requested_family, 'steps': outputs, 'note': 'basic/all install Ultralytics + MediaPipe only. MMPose is intentionally separate because OpenMMLab CUDA wheels can be slow/version-sensitive.'}

    job_id = c.jobs.submit('pose_dependency_install', payload.model_dump() | {'resolved_family': family}, task)
    return {'job_id': job_id, 'status': 'queued', 'family': family, 'requested_family': requested_family}


@router.post('/annotations/download-model')
def download_annotation_model(payload: AnnotationModelDownloadPayload, request: Request):
    c = ctx(request)

    c.models.lifecycle.update(payload.model_key, 'download', state='queued', progress=0.0, message='Annotation model download queued')

    def task(progress, job_id: int):
        request_payload = ModelDownloadRequest(
            model_name=payload.model_key,
            dry_run=payload.dry_run,
            force_download=payload.force_download,
            parallel_downloads=max(1, int(payload.parallel_downloads or 8)),
        )
        return c.models.download(request_payload, progress=progress, job_id=job_id)

    job_id = c.jobs.submit_with_job_id('annotation_model_download_dry_run' if payload.dry_run else 'annotation_model_download', payload.model_dump(), task)
    c.models.lifecycle.update(payload.model_key, 'download', job_id=job_id)
    return {'job_id': job_id, 'status': 'queued', 'dry_run': payload.dry_run}


@router.get('/annotations/model-status')
def annotation_model_status(request: Request, model_key: str, local_model_path: str | None = None, custom_model_type: str | None = None):
    options = {}
    if local_model_path:
        options['local_model_path'] = local_model_path
    if custom_model_type:
        options['custom_model_type'] = custom_model_type
    return ctx(request).reference.annotation_model_status(model_key, options)


@router.get('/annotations')
def list_annotations(request: Request, media_id: int | None = None, label: str | None = None, limit: int = 500):
    return ctx(request).reference.list_annotations(media_id, label, limit)


@router.delete('/annotations/{annotation_id}')
def delete_annotation(annotation_id: int, request: Request):
    return ctx(request).reference.delete_annotation(annotation_id)


@router.post('/annotations')
def add_annotation(payload: AnnotationPayload, request: Request):
    values = payload.model_dump()
    if values.get('z_index') is None and values.get('layer_order') is not None:
        values['z_index'] = values.get('layer_order')
    return ctx(request).reference.add_annotation(**values)




@router.post('/annotations/propose')
def propose_annotation(payload: AnnotationProposalPayload, request: Request):
    try:
        return ctx(request).reference.propose_annotation(**payload.model_dump())
    except Exception as exc:
        # Annotation preview/generation should never hide model/dependency failures
        # behind a generic 500. Return a structured empty result so the HUD can
        # display the real problem without creating fake annotations.
        return {
            'ok': False,
            'media_id': payload.media_id,
            'proposals': [],
            'saved': [],
            'count': 0,
            'error': str(exc),
            'model_status': ctx(request).reference.annotation_model_status(payload.model_key, payload.options),
        }


@router.get('/annotations/editor-state/{media_id}')
def annotation_editor_state(media_id: int, request: Request):
    c = ctx(request)
    item = c.media.get(media_id)
    if not item:
        return {'media': None, 'annotations': []}
    return {'media': item.model_dump(), 'annotations': c.reference.list_annotations(media_id=media_id, limit=2000)}


@router.post('/training-sets')
def create_training_set(payload: TrainingSetPayload, request: Request):
    return ctx(request).reference.create_training_set(payload.name, payload.query, payload.dataset_id, payload.train_ratio, payload.seed, payload.description)


@router.post('/exports/yolo')
def export_yolo(payload: YoloExportPayload, request: Request):
    return ctx(request).reference.export_yolo(payload.training_set_id, payload.output_dir, payload.task, payload.label_filter)


@router.post('/exports/captions')
def export_captions(payload: YoloExportPayload, request: Request):
    return ctx(request).reference.export_caption_jsonl(payload.training_set_id, payload.output_dir)


@router.post('/training-jobs')
def create_training_job(payload: TrainingJobPayload, request: Request):
    c = ctx(request)
    model_name = payload.model_key or payload.name or 'training-job'
    c.models.lifecycle.update(model_name, 'training', state='running', progress=0.05, message='Creating training scaffold')
    try:
        result = c.reference.create_training_job(payload.name, payload.task, payload.model_key, payload.training_set_id, payload.config)
        c.models.lifecycle.complete(model_name, 'training', message='Training scaffold created', result=result)
        return result
    except Exception as exc:
        c.models.lifecycle.fail(model_name, 'training', exc)
        raise

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/multimodal", tags=["multimodal-dataset-builder"])


class ImportAssetPayload(BaseModel):
    source_path: str
    copy_asset: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)


class ProbePayload(BaseModel):
    source_path: str
    provenance: dict[str, Any] = Field(default_factory=dict)


class ClipSuggestPayload(BaseModel):
    asset_id: str
    method: str = "fixed_window"
    min_duration: float = 2.0
    max_duration: float = 8.0
    overlap_seconds: float = 0.0
    target_frames: int | None = None


class ClipCreatePayload(BaseModel):
    asset_id: str
    start_sec: float | None = None
    end_sec: float | None = None
    clip_path: str = ""
    audio_path: str = ""
    method: str = "manual"
    created_by: str = "user"
    qc: dict[str, Any] = Field(default_factory=dict)


class BatchClipCreatePayload(BaseModel):
    asset_id: str
    suggestions: list[dict[str, Any]] = Field(default_factory=list)
    method: str = "batch_suggested"


class CaptionRenderPayload(BaseModel):
    structured: dict[str, Any] = Field(default_factory=dict)
    style: str = "structured_blocks"
    trigger_strategy: str = "none"
    trigger_token: str = ""


class CaptionRevisionPayload(BaseModel):
    clip_id: str
    structured: dict[str, Any] = Field(default_factory=dict)
    caption_flat: str = ""
    trigger_token: str = ""
    model_outputs: dict[str, Any] = Field(default_factory=dict)
    reviewed: bool = False
    approved: bool = False
    edited_by_user: bool = True
    render_style: str = "structured_blocks"
    trigger_strategy: str = "none"


class AudioAnnotationPayload(BaseModel):
    clip_id: str
    annotation: dict[str, Any] = Field(default_factory=dict)


class VisualAnnotationPayload(BaseModel):
    clip_id: str
    annotation: dict[str, Any] = Field(default_factory=dict)


class VoiceProfilePayload(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)


class AVSyncAnnotationPayload(BaseModel):
    clip_id: str
    annotation: dict[str, Any] = Field(default_factory=dict)


class TrainingSamplePayload(BaseModel):
    clip_id: str
    task_profile: str
    caption_revision_id: str = ""
    split: str = "train"
    enabled: bool = True
    sample_weight: float = 1.0
    overrides: dict[str, Any] = Field(default_factory=dict)


class ValidatePayload(BaseModel):
    clip_id: str
    task_profile: str
    caption_revision_id: str = ""
    overrides: dict[str, Any] = Field(default_factory=dict)


class CompatibilityMatrixPayload(BaseModel):
    sample_ids: list[str] = Field(default_factory=list)
    clip_ids: list[str] = Field(default_factory=list)


class ExportPayload(BaseModel):
    export_profile: str = "generic_manifest"
    sample_ids: list[str] = Field(default_factory=list)
    output_dir: str = ""
    name: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class TrainingCommandPayload(BaseModel):
    export_profile: str
    output_dir: str = ""
    trainer: str = ""
    config: dict[str, Any] = Field(default_factory=dict)


class PipelineRunPayload(BaseModel):
    clip_ids: list[str] = Field(default_factory=list)
    passes: list[str] = Field(default_factory=list)


def _handle(fn):
    try:
        return fn()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/catalog")
def catalog(request: Request):
    return ctx(request).multimodal.catalog()


@router.get("/assets")
def assets(request: Request, limit: int = 250, media_type: str = "", q: str = ""):
    return {"items": ctx(request).multimodal.assets(limit=limit, media_type=media_type, q=q)}


@router.get("/assets/{asset_id}")
def asset(asset_id: str, request: Request):
    return _handle(lambda: ctx(request).multimodal.asset_detail(asset_id))


@router.post("/media/probe")
def probe(payload: ProbePayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.probe_path(payload.source_path, provenance=payload.provenance))


@router.post("/media/import")
def import_asset(payload: ImportAssetPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.import_asset(payload.source_path, copy_asset=payload.copy_asset, provenance=payload.provenance))


@router.get("/clips")
def clips(request: Request, asset_id: str = "", limit: int = 250):
    return {"items": ctx(request).multimodal.clips(asset_id=asset_id, limit=limit)}


@router.get("/clips/{clip_id}")
def clip(clip_id: str, request: Request):
    return _handle(lambda: ctx(request).multimodal.clip_detail(clip_id))


@router.post("/clips/suggest")
def suggest_clips(payload: ClipSuggestPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.suggest_clips(
        payload.asset_id,
        method=payload.method,
        min_duration=payload.min_duration,
        max_duration=payload.max_duration,
        overlap_seconds=payload.overlap_seconds,
        target_frames=payload.target_frames,
    ))


@router.post("/clips/create")
def create_clip(payload: ClipCreatePayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.create_clip(
        payload.asset_id,
        start_sec=payload.start_sec,
        end_sec=payload.end_sec,
        clip_path=payload.clip_path,
        audio_path=payload.audio_path,
        method=payload.method,
        created_by=payload.created_by,
        qc=payload.qc,
    ))


@router.post("/clips/batch-create")
def batch_create_clips(payload: BatchClipCreatePayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.batch_create_clips(payload.asset_id, payload.suggestions, method=payload.method))


@router.post("/captions/render")
def render_caption(payload: CaptionRenderPayload, request: Request):
    caption = ctx(request).multimodal.render_caption(payload.structured, style=payload.style, trigger_strategy=payload.trigger_strategy, trigger_token=payload.trigger_token)
    return {"caption": caption, "style": payload.style, "trigger_strategy": payload.trigger_strategy}


@router.post("/captions/revisions")
def caption_revision(payload: CaptionRevisionPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.save_caption_revision(
        payload.clip_id,
        payload.structured,
        caption_flat=payload.caption_flat,
        trigger_token=payload.trigger_token,
        model_outputs=payload.model_outputs,
        reviewed=payload.reviewed,
        approved=payload.approved,
        edited_by_user=payload.edited_by_user,
        render_style=payload.render_style,
        trigger_strategy=payload.trigger_strategy,
    ))


@router.post("/audio/annotations")
def audio_annotation(payload: AudioAnnotationPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.save_audio_annotation(payload.clip_id, payload.annotation))


@router.post("/visual/annotations")
def visual_annotation(payload: VisualAnnotationPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.save_visual_annotation(payload.clip_id, payload.annotation))


@router.get("/voice/profiles")
def voice_profiles(request: Request, limit: int = 250):
    return {"items": ctx(request).multimodal.voice_profiles(limit=limit)}


@router.get("/voice/profiles/{profile_id}")
def voice_profile(profile_id: str, request: Request):
    return _handle(lambda: ctx(request).multimodal.voice_profile(profile_id))


@router.post("/voice/profiles")
def save_voice_profile(payload: VoiceProfilePayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.save_voice_profile(payload.profile))


@router.post("/audio-video/sync")
def audio_video_sync_annotation(payload: AVSyncAnnotationPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.save_av_sync_annotation(payload.clip_id, payload.annotation))


@router.post("/training-samples/create")
def create_training_sample(payload: TrainingSamplePayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.create_training_sample(
        payload.clip_id,
        payload.task_profile,
        caption_revision_id=payload.caption_revision_id,
        split=payload.split,
        enabled=payload.enabled,
        sample_weight=payload.sample_weight,
        overrides=payload.overrides,
    ))


@router.get("/training-samples")
def training_samples(request: Request, limit: int = 250, task_profile: str = "", enabled_only: bool = False):
    return {"items": ctx(request).multimodal.samples(limit=limit, task_profile=task_profile, enabled_only=enabled_only)}


@router.post("/qc/run-sample")
def validate_sample(payload: ValidatePayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.validate_clip_for_profile(payload.clip_id, payload.task_profile, caption_revision_id=payload.caption_revision_id, overrides=payload.overrides))


@router.post("/datasets/validate-export")
def validate_export(payload: CompatibilityMatrixPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.compatibility_matrix(sample_ids=payload.sample_ids or None, clip_ids=payload.clip_ids or None))


@router.post("/datasets/export")
def export_dataset(payload: ExportPayload, request: Request):
    c = ctx(request)
    params = payload.model_dump()

    def task(progress):
        return c.multimodal.export_dataset(
            export_profile=payload.export_profile,
            sample_ids=payload.sample_ids,
            output_dir=payload.output_dir,
            name=payload.name,
            config=payload.config,
            progress=progress,
        )

    job_id = c.jobs.submit("multimodal_dataset_export", params, task)
    return {"ok": True, "job_id": job_id, "export_profile": payload.export_profile}


@router.post("/training/prepare-command")
def prepare_training_command(payload: TrainingCommandPayload, request: Request):
    return _handle(lambda: ctx(request).multimodal.prepare_training_command(payload.export_profile, payload.output_dir, trainer=payload.trainer, config=payload.config))


@router.post("/pipeline/plan")
def plan_pipeline(payload: PipelineRunPayload, request: Request):
    c = ctx(request)
    params = payload.model_dump()

    def task(progress):
        return c.multimodal.scaffold_pipeline_run(payload.clip_ids, passes=payload.passes or None, progress=progress)

    job_id = c.jobs.submit("multimodal_labeling_pipeline_plan", params, task)
    return {"ok": True, "job_id": job_id}


# Compatibility aliases matching the handoff report route vocabulary.
@router.post("/audio/extract")
def audio_extract(payload: PipelineRunPayload, request: Request):
    return plan_pipeline(PipelineRunPayload(clip_ids=payload.clip_ids, passes=["audio_extract"]), request)


@router.post("/audio/transcribe")
def audio_transcribe(payload: PipelineRunPayload, request: Request):
    return plan_pipeline(PipelineRunPayload(clip_ids=payload.clip_ids, passes=["asr_transcribe", "human_review"]), request)


@router.post("/video/caption")
def video_caption(payload: PipelineRunPayload, request: Request):
    return plan_pipeline(PipelineRunPayload(clip_ids=payload.clip_ids, passes=["video_understanding", "caption_synthesis", "verification", "human_review"]), request)


@router.post("/captions/verify")
def caption_verify(payload: PipelineRunPayload, request: Request):
    return plan_pipeline(PipelineRunPayload(clip_ids=payload.clip_ids, passes=["caption_verification", "human_review"]), request)

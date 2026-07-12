from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/pipeline-prep", tags=["pipeline-prep"])


class PipelineRulesRequest(BaseModel):
    target_model: str = "sdxl"
    adapter_family: str = "lora"
    dataset_goal: Literal["style", "character", "character_style", "concept"] = "character"


class PipelineBranchRequest(PipelineRulesRequest):
    branch_id: int | None = None
    branch_name: str | None = None
    max_items: int = 40
    output_dir: str | None = None
    include_manifest: bool = False


class PipelineApplyRequest(PipelineBranchRequest):
    dry_run: bool = True
    use_model: bool = False
    model_name: str = ""
    model_max_items: int = 40
    keep_low_signal_tags: bool = False
    generate_placeholder_captions: bool = True
    name: str = "Pipeline prep run"


class PipelinePlanRequest(PipelineRulesRequest):
    branch_name: str = "default"
    options: dict[str, Any] = Field(default_factory=dict)


class PipelineAugmentationRequest(PipelineBranchRequest):
    operations: list[str] = Field(default_factory=list)
    selected_augmentations: list[str] = Field(default_factory=list)
    dry_run: bool = True
    max_variants_per_item: int = Field(default=3, ge=1, le=12)
    name: str = "Pipeline augmentation variant run"


class PipelineRegularizationRequest(PipelineRulesRequest):
    branch_id: int | None = None
    branch_name: str | None = None
    max_items: int = 40
    trigger_token: str = ""
    class_label: str = ""
    class_name: str = ""
    regularization_class: str = ""


@router.get("/catalog")
def catalog(request: Request):
    return ctx(request).pipeline_prep.catalog()


@router.get("/rules")
def rules(request: Request, target_model: str = "sdxl", adapter_family: str = "lora", dataset_goal: str = "character"):
    return ctx(request).pipeline_prep.rule_presets(target_model, adapter_family, dataset_goal)


@router.post("/plan")
def plan(payload: PipelinePlanRequest, request: Request):
    return ctx(request).pipeline_prep.plan_pipeline(payload)


@router.post("/evaluate")
def evaluate(payload: PipelineBranchRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.evaluate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/build-prompt")
def build_prompt(payload: PipelineBranchRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.build_prompt(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/apply-rules")
def apply_rules(payload: PipelineApplyRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.pipeline_prep.apply_rules(payload, progress)

    job_id = c.jobs.submit("pipeline_prep_apply", payload.model_dump(), task)
    return {"ok": True, "job_id": job_id, "dry_run": payload.dry_run}


@router.post("/apply-rules-now")
def apply_rules_now(payload: PipelineApplyRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.apply_rules(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/export-manifest")
def export_manifest(payload: PipelineBranchRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.export_manifest(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def runs(request: Request, limit: int = 50):
    return ctx(request).pipeline_prep.runs(limit=limit)


@router.get("/augmentation-policies")
def augmentation_policies(request: Request):
    return ctx(request).pipeline_prep.augmentation_policy_catalog()


@router.post("/augmentation-plan")
def augmentation_plan(payload: PipelineAugmentationRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.augmentation_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/apply-augmentations")
def apply_augmentations(payload: PipelineAugmentationRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.pipeline_prep.apply_augmentations(payload, progress)

    job_id = c.jobs.submit("pipeline_prep_augmentations", payload.model_dump(), task)
    return {"ok": True, "job_id": job_id, "dry_run": payload.dry_run}


@router.post("/apply-augmentations-now")
def apply_augmentations_now(payload: PipelineAugmentationRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.apply_augmentations(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/generate-variants")
def generate_variants(payload: PipelineAugmentationRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.pipeline_prep.generate_augmented_variants(payload, progress)

    job_id = c.jobs.submit("pipeline_prep_generate_variants", payload.model_dump(), task)
    return {"ok": True, "job_id": job_id, "dry_run": payload.dry_run}


@router.post("/generate-variants-now")
def generate_variants_now(payload: PipelineAugmentationRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.generate_augmented_variants(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/regularization-plan")
def regularization_plan(payload: PipelineRegularizationRequest, request: Request):
    try:
        return ctx(request).pipeline_prep.regularization_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

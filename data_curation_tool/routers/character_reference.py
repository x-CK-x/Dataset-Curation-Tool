from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/character-reference", tags=["character-reference"])


class CharacterReferenceProfilePayload(BaseModel):
    target_name: str
    notes: str = ""
    pipeline: str = "dino_clip_fallback"
    threshold: float = 0.62
    crop_strategy: Literal["whole_plus_head", "whole_only", "headshot_only"] = "whole_plus_head"
    reference_paths: list[str] = Field(default_factory=list)
    positive_paths: list[str] = Field(default_factory=list)
    negative_paths: list[str] = Field(default_factory=list)
    positive_media_ids: list[int] = Field(default_factory=list)
    negative_media_ids: list[int] = Field(default_factory=list)


class CharacterReferenceRankPayload(BaseModel):
    target_name: str
    pipeline: str = "dino_clip_fallback"
    threshold: float | None = None
    uncertain_margin: float = 0.06
    crop_strategy: Literal["whole_plus_head", "whole_only", "headshot_only"] = "whole_plus_head"
    reference_paths: list[str] = Field(default_factory=list)
    positive_paths: list[str] = Field(default_factory=list)
    negative_paths: list[str] = Field(default_factory=list)
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    branch_id: int | None = None
    branch_name: str = ""
    folder: str = ""
    recursive: bool = True
    max_items: int = 5000
    return_limit: int = 500
    notes: str = ""


class CharacterReferenceRebuildPayload(BaseModel):
    target_name: str
    run_id: int | None = None
    accept_threshold: float = 0.72
    reject_threshold: float = 0.40


class CharacterReferencePrunePayload(CharacterReferenceRankPayload):
    run_id: int | None = None


class CharacterReferenceApplyBranchPayload(BaseModel):
    target_name: str = ""
    run_id: int
    branch_id: int
    mode: Literal["exclude_rejects", "include_matches_only", "mark_uncertain"] = "exclude_rejects"


@router.get("/status")
def status(request: Request):
    return ctx(request).character_reference.status()


@router.get("/pipelines")
def pipelines(request: Request):
    return ctx(request).character_reference.pipeline_catalog()


@router.get("/profiles")
def profiles(request: Request):
    return {"items": ctx(request).character_reference.list_profiles()}


@router.get("/profiles/{target_name}")
def profile(target_name: str, request: Request):
    item = ctx(request).character_reference.get_profile(target_name)
    if not item:
        raise HTTPException(status_code=404, detail=f"Unknown character reference profile: {target_name}")
    return item


@router.post("/profiles")
def upsert_profile(payload: CharacterReferenceProfilePayload, request: Request):
    try:
        return ctx(request).character_reference.upsert_profile(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/profiles/{target_name}")
def delete_profile(target_name: str, request: Request):
    return ctx(request).character_reference.delete_profile(target_name)


@router.post("/profiles/rebuild-from-run")
def rebuild_profile(payload: CharacterReferenceRebuildPayload, request: Request):
    try:
        return ctx(request).character_reference.rebuild_profile_from_run(payload.target_name, payload.run_id, payload.accept_threshold, payload.reject_threshold)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rank-now")
def rank_now(payload: CharacterReferenceRankPayload, request: Request):
    try:
        return ctx(request).character_reference.rank(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rank")
def rank_job(payload: CharacterReferenceRankPayload, request: Request):
    c = ctx(request)

    def task(progress):
        return c.character_reference.rank(payload, progress)

    job_id = c.jobs.submit("character_reference_rank", payload.model_dump(), task)
    return {"ok": True, "job_id": job_id, "status": "queued"}


@router.post("/prune-plan")
def prune_plan(payload: CharacterReferencePrunePayload, request: Request):
    try:
        return ctx(request).character_reference.prune_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/apply-prune-to-branch")
def apply_prune_to_branch(payload: CharacterReferenceApplyBranchPayload, request: Request):
    try:
        return ctx(request).character_reference.apply_prune_to_branch(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

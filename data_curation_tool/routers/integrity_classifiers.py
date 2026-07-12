from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException

from .deps import ctx

router = APIRouter(prefix="/integrity-classifiers", tags=["integrity-classifiers"])


@router.get("/profiles")
def list_profiles(request: Request):
    return ctx(request).integrity_classifiers.list_profiles()


@router.post("/profiles")
def save_profile(payload: dict, request: Request):
    try:
        return ctx(request).integrity_classifiers.save_profile(payload or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str, request: Request):
    return ctx(request).integrity_classifiers.delete_profile(profile_id)


@router.post("/inspect-folder")
def inspect_folder(payload: dict, request: Request):
    return ctx(request).integrity_classifiers.inspect_folder((payload or {}).get("folder") or "")


@router.post("/run")
def run_integrity_classifier(payload: dict, request: Request):
    c = ctx(request)
    params = dict(payload or {})
    def task(progress, job_id):
        return c.integrity_classifiers.run(params, progress=progress, job_id=job_id)
    job_id = c.jobs.submit_with_job_id("integrity_classifier", params, task)
    return {"job_id": job_id, "status": "queued", "media_ids": params.get("media_ids") or [], "profile_id": params.get("profile_id")}

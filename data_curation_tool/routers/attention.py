from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from .deps import ctx

router = APIRouter(prefix="/attention-visualization", tags=["attention-visualization"])


@router.get("/capabilities")
def capabilities(request: Request):
    return ctx(request).attention.capabilities()


@router.post("/plan")
def plan(payload: dict, request: Request):
    try:
        return ctx(request).attention.plan(payload or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/render")
def render_sync(payload: dict, request: Request):
    try:
        return ctx(request).attention.run(dict(payload or {}), progress=None)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/artifact/{name}")
def artifact(name: str, request: Request):
    try:
        return FileResponse(str(ctx(request).attention.artifact_path(name)))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Attention artifact not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run")
def run(payload: dict, request: Request):
    c = ctx(request)
    params = dict(payload or {})

    def task(progress):
        return c.attention.run(params, progress=progress)

    job_id = c.jobs.submit("attention_visualization", params, task)
    return {"job_id": job_id}

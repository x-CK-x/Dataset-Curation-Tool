from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import OrchestrationRequest

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


@router.get("/templates")
def templates(request: Request):
    return ctx(request).orchestration.templates()


@router.post("/run")
def run_orchestration(payload: OrchestrationRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.orchestration.run(payload, job_id, progress)

    job_id = c.jobs.submit("orchestration", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}

from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import ExportRequest

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/run")
def run_export(payload: ExportRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.exports.run(payload, progress)

    job_id = c.jobs.submit("export", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}

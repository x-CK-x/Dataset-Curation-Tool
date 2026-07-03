from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import DownloadRequest
from ..services.downloader_service import booru_logic_summary, source_definitions, validate_source_configs

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("/sources")
def sources():
    return source_definitions()


@router.get("/validate-sources")
def validate_sources(request: Request, live: bool = False):
    return ctx(request).downloads.validate_source_configurations(live=live)


@router.get("/source-validation")
def source_validation():
    return validate_source_configs()


@router.get("/logic/preview")
def logic_preview(query: str = "", max_clauses: int = 64):
    return booru_logic_summary(query, max_clauses=max(1, min(int(max_clauses or 64), 512)))


@router.post("/run")
def run_download(payload: DownloadRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.downloads.run(payload, progress)

    job_id = c.jobs.submit("download", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}


@router.get("/runs")
def runs(request: Request, limit: int = 100):
    return ctx(request).db.query("SELECT * FROM download_runs ORDER BY id DESC LIMIT ?", (limit,))

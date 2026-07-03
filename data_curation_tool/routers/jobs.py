from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request

from .deps import ctx
from ..schemas import DownloadRequest, ModelDownloadRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


class ClearJobsRequest(BaseModel):
    job_ids: list[int] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    clear_all: bool = False
    include_running: bool = False


class CancelJobsRequest(BaseModel):
    job_ids: list[int] = Field(default_factory=list)
    download_only: bool = False
    include_running: bool = True


class PauseJobsRequest(BaseModel):
    job_ids: list[int] = Field(default_factory=list)
    download_only: bool = False
    include_running: bool = True


class RetryJobsRequest(BaseModel):
    job_ids: list[int] = Field(default_factory=list)
    failed_only: bool = True
    force_download: bool = True


@router.get("")
def list_jobs(request: Request, limit: int = 100):
    return ctx(request).jobs.list_jobs(limit)


@router.get("/{job_id}")
def get_job(job_id: int, request: Request):
    job = ctx(request).jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/clear")
def clear_jobs(payload: ClearJobsRequest, request: Request):
    return ctx(request).jobs.clear_jobs(
        job_ids=payload.job_ids or None,
        statuses=payload.statuses or None,
        clear_all=payload.clear_all,
        include_running=payload.include_running,
    )


@router.post("/cancel")
def cancel_jobs(payload: CancelJobsRequest, request: Request):
    return ctx(request).jobs.cancel_jobs(
        job_ids=payload.job_ids or None,
        download_only=payload.download_only,
        include_running=payload.include_running,
    )


@router.post("/pause")
def pause_jobs(payload: PauseJobsRequest, request: Request):
    return ctx(request).jobs.pause_jobs(
        job_ids=payload.job_ids or None,
        download_only=payload.download_only,
        include_running=payload.include_running,
    )


@router.post("/resume")
def resume_jobs(payload: PauseJobsRequest, request: Request):
    return ctx(request).jobs.resume_jobs(
        job_ids=payload.job_ids or None,
        download_only=payload.download_only,
    )


@router.post("/retry")
def retry_jobs(payload: RetryJobsRequest, request: Request):
    """Requeue failed/cancelled jobs from their saved params.

    This is intentionally conservative: it only retries download-like jobs whose
    params map cleanly back to the original API payload.  Unsupported jobs are
    reported instead of guessed.
    """
    c = ctx(request)
    new_jobs: list[dict] = []
    skipped: list[dict] = []
    allowed_statuses = {"failed", "cancelled", "canceled"}

    for raw_id in payload.job_ids or []:
        try:
            original_id = int(raw_id)
        except Exception:
            skipped.append({"job_id": raw_id, "reason": "invalid job id"})
            continue
        job = c.jobs.get_job(original_id)
        if not job:
            skipped.append({"job_id": original_id, "reason": "job not found"})
            continue
        status = str(job.get("status") or "").lower()
        if payload.failed_only and status not in allowed_statuses:
            skipped.append({"job_id": original_id, "type": job.get("type"), "status": status, "reason": "not failed/cancelled"})
            continue
        job_type = str(job.get("type") or "")
        params = dict(job.get("params") or {})
        lower_type = job_type.lower()

        try:
            if lower_type == "download":
                request_payload = DownloadRequest(**{**params, "force_download": bool(payload.force_download)})

                def task(progress, _payload=request_payload):
                    return c.downloads.run(_payload, progress)

                new_id = c.jobs.submit("download", request_payload.model_dump(), task)
                new_jobs.append({"original_job_id": original_id, "job_id": new_id, "type": "download"})
                continue

            if lower_type.startswith("model_download"):
                if "model_key" in params and "model_name" not in params:
                    params["model_name"] = params.pop("model_key")
                request_payload = ModelDownloadRequest(**{**params, "force_download": bool(payload.force_download)})
                status_model_name = request_payload.model_name or request_payload.repo_id or request_payload.local_dir or "custom-model-download"
                c.models.lifecycle.update(status_model_name, "download", state="queued", progress=0.0, message="Retry download queued")

                def task(progress, job_id: int, _payload=request_payload):
                    token = _payload.token or c.settings.huggingface_token
                    next_payload = _payload.model_copy(update={"token": token})
                    return c.models.download(next_payload, progress=progress, job_id=job_id)

                new_id = c.jobs.submit_with_job_id("model_download", request_payload.model_dump(exclude={"token"}), task)
                c.models.lifecycle.update(status_model_name, "download", job_id=new_id)
                new_jobs.append({"original_job_id": original_id, "job_id": new_id, "type": "model_download", "model_name": status_model_name})
                continue

            if lower_type.startswith("annotation_model_download"):
                model_key = params.get("model_key") or params.get("model_name")
                if not model_key:
                    raise ValueError("annotation model retry requires model_key/model_name")
                request_payload = ModelDownloadRequest(model_name=str(model_key), dry_run=bool(params.get("dry_run", False)), force_download=bool(payload.force_download), parallel_downloads=max(1, int(params.get("parallel_downloads") or 8)))
                c.models.lifecycle.update(str(model_key), "download", state="queued", progress=0.0, message="Retry annotation model download queued")

                def task(progress, job_id: int, _payload=request_payload):
                    return c.models.download(_payload, progress=progress, job_id=job_id)

                new_id = c.jobs.submit_with_job_id("annotation_model_download", {"model_key": model_key, "force_download": bool(payload.force_download), "parallel_downloads": request_payload.parallel_downloads}, task)
                c.models.lifecycle.update(str(model_key), "download", job_id=new_id)
                new_jobs.append({"original_job_id": original_id, "job_id": new_id, "type": "annotation_model_download", "model_name": model_key})
                continue

            if lower_type.startswith("tag_dictionary") or lower_type.startswith("db_export"):
                profile_key = str(params.get("profile_key") or c.settings.default_tag_profile or "e621")
                source_url = params.get("url")
                cache_hours = int(params.get("cache_hours") or getattr(c.settings, "tag_db_export_cache_hours", 336) or 336)

                def task(progress, _profile_key=profile_key, _url=source_url, _cache_hours=cache_hours):
                    return c.tags.import_default_exports(
                        profile_key=_profile_key,
                        url=_url,
                        user_agent=c.settings.downloader_user_agent or "DataCurationTool/5.46.0",
                        cache_hours=_cache_hours,
                        progress=progress,
                        replace_existing=True,
                        force_download=bool(payload.force_download),
                    )

                new_type = "tag_dictionary_import" if lower_type != "tag_dictionary_startup_sync" else "tag_dictionary_startup_sync"
                new_id = c.jobs.submit(new_type, {"profile_key": profile_key, "url": source_url, "force_download": bool(payload.force_download)}, task)
                new_jobs.append({"original_job_id": original_id, "job_id": new_id, "type": new_type, "profile_key": profile_key})
                continue

            skipped.append({"job_id": original_id, "type": job_type, "reason": "retry is only implemented for download/model/tag-export jobs"})
        except Exception as exc:
            skipped.append({"job_id": original_id, "type": job_type, "reason": str(exc)})

    return {"retried": new_jobs, "skipped": skipped, "count": len(new_jobs)}

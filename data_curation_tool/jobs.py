from __future__ import annotations

import concurrent.futures
import os
import traceback
import threading
from collections.abc import Callable
from typing import Any

from .database import Database

ProgressCallback = Callable[[float, str], None]
JobCallable = Callable[[ProgressCallback], dict[str, Any]]
JobCallableWithId = Callable[[ProgressCallback, int], dict[str, Any]]


class CancelledJobError(RuntimeError):
    """Raised by cooperative workers when a queued/running job is cancelled."""


class PausedJobError(RuntimeError):
    """Marker used only for typing/documentation; pauses are cooperative waits."""


class JobManager:
    def __init__(self, db: Database, max_workers: int = 2):
        self.db = db
        self.max_workers = max(1, int(max_workers or 1))
        self.inline = os.environ.get("DCT_RUN_JOBS_INLINE") == "1"
        self.executor = None
        self.executors: dict[str, concurrent.futures.ThreadPoolExecutor] = {}
        self._cancel_lock = threading.RLock()
        self._cancel_events: dict[int, threading.Event] = {}
        self._pause_events: dict[int, threading.Event] = {}
        if not self.inline:
            general_workers = self.max_workers
            model_download_workers = max(1, int(os.environ.get("DCT_MODEL_DOWNLOAD_WORKERS", "1") or "1"))
            model_load_workers = max(1, int(os.environ.get("DCT_MODEL_LOAD_WORKERS", "1") or "1"))
            model_inference_workers = max(1, int(os.environ.get("DCT_MODEL_INFERENCE_WORKERS", str(min(2, self.max_workers))) or "1"))
            download_workers = max(1, int(os.environ.get("DCT_DOWNLOAD_WORKERS", "1") or "1"))
            self.executors = {
                "general": concurrent.futures.ThreadPoolExecutor(max_workers=general_workers, thread_name_prefix="dct-job"),
                "download": concurrent.futures.ThreadPoolExecutor(max_workers=download_workers, thread_name_prefix="dct-download"),
                "model_download": concurrent.futures.ThreadPoolExecutor(max_workers=model_download_workers, thread_name_prefix="dct-model-download"),
                "model_load": concurrent.futures.ThreadPoolExecutor(max_workers=model_load_workers, thread_name_prefix="dct-model-load"),
                "model_inference": concurrent.futures.ThreadPoolExecutor(max_workers=model_inference_workers, thread_name_prefix="dct-model-inference"),
            }
            self.executor = self.executors["general"]

    def _lane_for_job(self, job_type: str) -> str:
        key = str(job_type or "").lower()
        if key.startswith("model_download") or key.startswith("annotation_model_download"):
            return "model_download"
        if key in {"download", "downloader", "download_run"} or key.startswith("tag_dictionary") or key.startswith("db_export") or key.endswith("_download") or key.endswith("_sync"):
            return "download"
        if key in {"model_load", "model_unload"} or key.endswith("_model_load") or key.endswith("_model_unload"):
            return "model_load"
        if key in {"model_inference", "model_run", "model_tag_selection"} or "inference" in key:
            return "model_inference"
        return "general"

    def _executor_for_job(self, job_type: str) -> concurrent.futures.ThreadPoolExecutor:
        lane = self._lane_for_job(job_type)
        return self.executors.get(lane) or self.executors["general"]

    def submit(self, job_type: str, params: dict[str, Any], fn: JobCallable) -> int:
        return self.submit_with_job_id(job_type, params, lambda progress, _job_id: fn(progress))

    def submit_with_job_id(self, job_type: str, params: dict[str, Any], fn: JobCallableWithId) -> int:
        job_id = self.db.create_job(job_type, params)
        cancel_event = threading.Event()
        pause_event = threading.Event()
        pause_event.set()
        with self._cancel_lock:
            self._cancel_events[job_id] = cancel_event
            self._pause_events[job_id] = pause_event

        progress_lock = threading.Lock()
        last_progress = 0.0

        def assert_not_cancelled() -> None:
            if cancel_event.is_set():
                raise CancelledJobError("Cancelled by user")
            row = self.db.query_one("SELECT status FROM jobs WHERE id=?", (job_id,))
            if row and str(row.get("status") or "").lower() == "cancelled":
                cancel_event.set()
                raise CancelledJobError("Cancelled by user")

        def wait_if_paused() -> None:
            while not pause_event.is_set():
                assert_not_cancelled()
                # Keep the DB row visibly paused.  The runner resumes as soon as
                # /api/jobs/resume sets this event.
                pause_event.wait(0.35)

        def progress(value: float, message: str = "") -> None:
            nonlocal last_progress
            wait_if_paused()
            assert_not_cancelled()
            safe_value = max(0.0, min(1.0, float(value or 0.0)))
            with progress_lock:
                if safe_value < last_progress:
                    safe_value = last_progress
                else:
                    last_progress = safe_value
            self.db.update_job(job_id, status="running", progress=safe_value, message=message)

        setattr(progress, "cancel_event", cancel_event)
        setattr(progress, "cancel_requested", lambda: cancel_event.is_set())
        setattr(progress, "pause_event", pause_event)
        setattr(progress, "paused", lambda: not pause_event.is_set())
        setattr(progress, "wait_if_paused", wait_if_paused)

        def runner() -> None:
            try:
                wait_if_paused()
                assert_not_cancelled()
                self.db.update_job(job_id, status="running", progress=0.0, message="Started")
                result = fn(progress, job_id)
                assert_not_cancelled()
                self.db.update_job(job_id, status="completed", progress=1.0, message="Completed", result=result, finished=True)
            except CancelledJobError as exc:
                self.db.update_job(job_id, status="cancelled", progress=last_progress, message=str(exc) or "Cancelled by user", error=None, finished=True)
            except Exception as exc:
                if cancel_event.is_set():
                    self.db.update_job(job_id, status="cancelled", progress=last_progress, message="Cancelled by user", error=None, finished=True)
                else:
                    self.db.update_job(job_id, status="failed", message="Failed", error=f"{exc}\n{traceback.format_exc()}", finished=True)
            finally:
                with self._cancel_lock:
                    self._cancel_events.pop(job_id, None)
                    self._pause_events.pop(job_id, None)

        if self.inline or os.environ.get("PYTEST_CURRENT_TEST"):
            runner()
        else:
            self._executor_for_job(job_type).submit(runner)
        return job_id

    def _job_selection_where(self, job_ids: list[int] | None = None, *, download_only: bool = False, statuses: tuple[str, ...] = ("queued", "running")) -> tuple[str, list[Any], str | None]:
        clauses: list[str] = []
        params: list[Any] = []
        if job_ids:
            ids: list[int] = []
            for raw_id in job_ids:
                try:
                    job_id = int(raw_id)
                except Exception:
                    continue
                if job_id > 0:
                    ids.append(job_id)
            if ids:
                clauses.append("id IN (" + ",".join("?" for _ in ids) + ")")
                params.extend(ids)
            else:
                return "", [], "No valid job ids supplied."
        if download_only:
            clauses.append("(LOWER(type) LIKE '%download%' OR LOWER(type) LIKE 'tag_dictionary%' OR LOWER(type) LIKE 'db_export%')")
        if statuses:
            clauses.append("status IN (" + ",".join("?" for _ in statuses) + ")")
            params.extend(statuses)
        where = " AND ".join(clauses) if clauses else "1=1"
        return where, params, None

    def cancel_jobs(self, job_ids: list[int] | None = None, *, download_only: bool = False, include_running: bool = True) -> dict[str, Any]:
        statuses = ("queued", "running", "paused") if include_running else ("queued", "paused")
        where, params, skipped_reason = self._job_selection_where(job_ids, download_only=download_only, statuses=statuses)
        if skipped_reason:
            return {"cancelled": [], "requested_running": [], "count": 0, "download_only": download_only, "include_running": include_running, "skipped": skipped_reason}
        rows = self.db.query(f"SELECT id, type, status, progress FROM jobs WHERE {where} ORDER BY id", tuple(params))
        cancelled: list[int] = []
        requested_running: list[int] = []
        for row in rows:
            job_id = int(row["id"])
            status = str(row.get("status") or "").lower()
            with self._cancel_lock:
                event = self._cancel_events.get(job_id)
                if event:
                    event.set()
                pause_event = self._pause_events.get(job_id)
                if pause_event:
                    pause_event.set()
            self.db.update_job(
                job_id,
                status="cancelled",
                progress=float(row.get("progress") or 0.0),
                message="Cancelled by user" if status == "queued" else "Cancellation requested by user",
                finished=status == "queued",
            )
            cancelled.append(job_id)
            if status == "running":
                requested_running.append(job_id)
        return {
            "cancelled": cancelled,
            "requested_running": requested_running,
            "count": len(cancelled),
            "download_only": download_only,
            "include_running": include_running,
            "note": "Running downloads are stopped cooperatively; very large in-progress file transfers may finish their current file before the worker exits.",
        }


    def pause_jobs(self, job_ids: list[int] | None = None, *, download_only: bool = False, include_running: bool = True) -> dict[str, Any]:
        statuses = ("queued", "running") if include_running else ("queued",)
        where, params, skipped_reason = self._job_selection_where(job_ids, download_only=download_only, statuses=statuses)
        if skipped_reason:
            return {"paused": [], "count": 0, "skipped": skipped_reason, "download_only": download_only}
        rows = self.db.query(f"SELECT id, type, status, progress FROM jobs WHERE {where} ORDER BY id", tuple(params))
        paused: list[int] = []
        already_untracked: list[int] = []
        for row in rows:
            job_id = int(row["id"])
            with self._cancel_lock:
                event = self._pause_events.get(job_id)
                if event:
                    event.clear()
                else:
                    already_untracked.append(job_id)
            self.db.update_job(
                job_id,
                status="paused",
                progress=float(row.get("progress") or 0.0),
                message="Paused by user. Resume before restarting the app, or cancel/retry if the worker was interrupted.",
                finished=False,
            )
            paused.append(job_id)
        return {
            "paused": paused,
            "count": len(paused),
            "download_only": download_only,
            "include_running": include_running,
            "untracked": already_untracked,
            "note": "Pausing is cooperative. Large in-progress file transfers pause at the next progress/checkpoint; queued downloads pause before starting.",
        }

    def resume_jobs(self, job_ids: list[int] | None = None, *, download_only: bool = False) -> dict[str, Any]:
        where, params, skipped_reason = self._job_selection_where(job_ids, download_only=download_only, statuses=("paused",))
        if skipped_reason:
            return {"resumed": [], "count": 0, "skipped": skipped_reason, "download_only": download_only}
        rows = self.db.query(f"SELECT id, type, status, progress FROM jobs WHERE {where} ORDER BY id", tuple(params))
        resumed: list[int] = []
        untracked: list[int] = []
        for row in rows:
            job_id = int(row["id"])
            with self._cancel_lock:
                event = self._pause_events.get(job_id)
                if event:
                    event.set()
                else:
                    untracked.append(job_id)
            self.db.update_job(
                job_id,
                status="queued",
                progress=float(row.get("progress") or 0.0),
                message="Resume requested; worker will continue shortly.",
                finished=False,
            )
            resumed.append(job_id)
        return {
            "resumed": resumed,
            "count": len(resumed),
            "download_only": download_only,
            "untracked": untracked,
            "note": "If a paused job is untracked because the app restarted, cancel/retry it from scratch.",
        }

    def shutdown(self, wait: bool = True) -> None:
        with self._cancel_lock:
            for event in self._cancel_events.values():
                event.set()
        seen: set[int] = set()
        for executor in list(self.executors.values()) or ([self.executor] if self.executor is not None else []):
            if executor is None:
                continue
            ident = id(executor)
            if ident in seen:
                continue
            seen.add(ident)
            executor.shutdown(wait=wait, cancel_futures=True)

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.query("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))
        return [self._decode(row) for row in rows]

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM jobs WHERE id=?", (job_id,))
        return self._decode(row) if row else None

    def clear_jobs(self, job_ids: list[int] | None = None, statuses: list[str] | None = None, clear_all: bool = False, include_running: bool = False) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []
        if job_ids:
            clauses.append("id IN (" + ",".join("?" for _ in job_ids) + ")")
            params.extend(int(x) for x in job_ids)
        if statuses:
            clauses.append("status IN (" + ",".join("?" for _ in statuses) + ")")
            params.extend(str(x) for x in statuses)
        if not clear_all and not clauses:
            return {"deleted": 0, "skipped": "No job ids/statuses supplied."}
        if not include_running:
            clauses.append("status NOT IN ('running')")
        where = " AND ".join(clauses) if clauses else "1=1"
        before = self.db.query_one(f"SELECT COUNT(*) AS n FROM jobs WHERE {where}", params) or {"n": 0}
        self.db.execute(f"DELETE FROM jobs WHERE {where}", params)
        return {"deleted": int(before.get("n") or 0)}

    @staticmethod
    def _decode(row: dict[str, Any]) -> dict[str, Any]:
        import json

        payload = dict(row)
        payload["params"] = json.loads(payload.pop("params_json") or "{}")
        result_json = payload.pop("result_json", None)
        payload["result"] = json.loads(result_json) if result_json else None
        return payload

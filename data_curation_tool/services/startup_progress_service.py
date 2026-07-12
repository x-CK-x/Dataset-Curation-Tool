from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StartupProgressService:
    """Thread-safe live status for startup/background maintenance.

    The FastAPI startup hook can queue slow reconciliation/migration work in a
    background thread.  This service gives the Dashboard a stable endpoint to
    poll, including elapsed time and a conservative ETA derived from the current
    progress value.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        created = _now_iso()
        self._state: dict[str, Any] = {
            "status": "idle",
            "phase": "idle",
            "progress": 0.0,
            "message": "Startup maintenance has not started yet.",
            "started_at": None,
            "updated_at": created,
            "finished_at": None,
            "steps": [],
            "error": None,
            "job_id": None,
            "job_type": None,
            "trigger": None,
        }

    def start(self, message: str = "Startup maintenance started", *, phase: str = "startup", job_id: int | None = None, job_type: str | None = None, trigger: str | None = None) -> None:
        now = _now_iso()
        with self._lock:
            self._state.update({
                "status": "running",
                "phase": str(phase or "startup"),
                "progress": 0.01,
                "message": message,
                "started_at": now,
                "updated_at": now,
                "finished_at": None,
                "steps": [{"at": now, "progress": 0.01, "message": message, "phase": str(phase or "startup")}],
                "error": None,
                "job_id": job_id,
                "job_type": job_type,
                "trigger": trigger,
            })

    def resume(self, message: str = "Startup maintenance resumed", *, phase: str = "startup") -> None:
        """Resume visible startup maintenance without clearing previous context.

        This is used when the user cancels first-run tag sync and later starts
        manual migration. The Dashboard card should become live again instead of
        staying completed/idle/failed.
        """
        now = _now_iso()
        with self._lock:
            if not self._state.get("started_at"):
                self._state["started_at"] = now
            self._state.update({
                "status": "running",
                "phase": phase,
                "message": message,
                "updated_at": now,
                "finished_at": None,
                "error": None,
            })
            steps = list(self._state.get("steps") or [])
            steps.append({"at": now, "progress": self._state.get("progress", 0.0), "message": message, "phase": phase})
            self._state["steps"] = steps[-80:]

    def update(self, progress: float | None = None, message: str | None = None, *, phase: str | None = None, job_id: int | None = None, job_type: str | None = None, trigger: str | None = None) -> None:
        now = _now_iso()
        with self._lock:
            current = float(self._state.get("progress") or 0.0)
            next_progress = current if progress is None else max(0.0, min(1.0, float(progress)))
            self._state["progress"] = next_progress
            if message is not None:
                self._state["message"] = str(message)
            if phase is not None:
                self._state["phase"] = str(phase)
            if job_id is not None:
                try:
                    self._state["job_id"] = int(job_id)
                except Exception:
                    self._state["job_id"] = job_id
            if job_type is not None:
                self._state["job_type"] = str(job_type)
            if trigger is not None:
                self._state["trigger"] = str(trigger)
            if self._state.get("status") in {"idle", "completed", "failed"}:
                self._state["status"] = "running"
                if not self._state.get("started_at"):
                    self._state["started_at"] = now
            self._state["updated_at"] = now
            if message is not None:
                steps = list(self._state.get("steps") or [])
                steps.append({"at": now, "progress": next_progress, "message": str(message), "phase": self._state.get("phase")})
                self._state["steps"] = steps[-80:]


    def attach_job(self, job_id: int | None, job_type: str | None = None, *, trigger: str | None = None, message: str | None = None) -> None:
        """Attach a real Jobs row to the Dashboard startup-maintenance card.

        Manual migrations, post-migration tag syncs, and other startup-like
        maintenance work can be queued after initial startup.  Attaching the job
        keeps the Dashboard circle live instead of leaving it stuck on the last
        startup-only row.
        """
        now = _now_iso()
        with self._lock:
            if job_id is not None:
                try:
                    self._state["job_id"] = int(job_id)
                except Exception:
                    self._state["job_id"] = job_id
            if job_type is not None:
                self._state["job_type"] = str(job_type)
            if trigger is not None:
                self._state["trigger"] = str(trigger)
            if message:
                self._state["message"] = str(message)
                steps = list(self._state.get("steps") or [])
                steps.append({"at": now, "progress": self._state.get("progress", 0.0), "message": str(message), "phase": self._state.get("phase")})
                self._state["steps"] = steps[-80:]
            if self._state.get("status") in {"idle", "completed", "failed", "unknown"}:
                self._state["status"] = "running"
                self._state["started_at"] = self._state.get("started_at") or now
            self._state["updated_at"] = now

    def callback(self, start: float = 0.0, end: float = 1.0, *, phase: str | None = None) -> Callable[[float, str], None]:
        start_f = max(0.0, min(1.0, float(start)))
        end_f = max(start_f, min(1.0, float(end)))

        def _cb(progress: float, message: str = "") -> None:
            try:
                local = max(0.0, min(1.0, float(progress or 0.0)))
            except Exception:
                local = 0.0
            self.update(start_f + (end_f - start_f) * local, message or None, phase=phase)

        return _cb

    def complete(self, message: str = "Startup maintenance complete") -> None:
        now = _now_iso()
        with self._lock:
            self._state.update({
                "status": "completed",
                "phase": "complete",
                "progress": 1.0,
                "message": message,
                "updated_at": now,
                "finished_at": now,
                "error": None,
            })
            steps = list(self._state.get("steps") or [])
            steps.append({"at": now, "progress": 1.0, "message": message, "phase": "complete"})
            self._state["steps"] = steps[-80:]

    def fail(self, error: BaseException | str, message: str = "Startup maintenance failed") -> None:
        now = _now_iso()
        with self._lock:
            self._state.update({
                "status": "failed",
                "phase": "failed",
                "message": message,
                "updated_at": now,
                "finished_at": now,
                "error": str(error),
            })
            steps = list(self._state.get("steps") or [])
            steps.append({"at": now, "progress": self._state.get("progress", 0.0), "message": f"{message}: {error}", "phase": "failed"})
            self._state["steps"] = steps[-80:]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            state = dict(self._state)
            state["steps"] = list(self._state.get("steps") or [])
        started_at = state.get("started_at")
        finished_at = state.get("finished_at")
        now_ts = time.time()
        started_ts = None
        finished_ts = None
        try:
            if started_at:
                started_ts = datetime.fromisoformat(str(started_at).replace("Z", "+00:00")).timestamp()
            if finished_at:
                finished_ts = datetime.fromisoformat(str(finished_at).replace("Z", "+00:00")).timestamp()
        except Exception:
            started_ts = None
        elapsed = 0.0
        if started_ts:
            elapsed = max(0.0, (finished_ts or now_ts) - started_ts)
        progress = max(0.0, min(1.0, float(state.get("progress") or 0.0)))
        eta = None
        if state.get("status") == "running" and progress > 0.03:
            remaining = elapsed * (1.0 - progress) / max(progress, 0.001)
            eta = max(0.0, remaining)
        state["elapsed_seconds"] = elapsed
        state["eta_seconds"] = eta
        state["percent"] = round(progress * 100.0, 1)
        return state

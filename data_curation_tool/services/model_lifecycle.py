from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable

ProgressCallback = Callable[[float, str], None]

MODEL_LIFECYCLE_STAGES: tuple[str, ...] = ("download", "load", "inference", "training")
ACTIVE_STATES = {"queued", "running", "unloading"}
TERMINAL_STATES = {"completed", "failed", "cancelled", "idle"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp_progress(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value if value is not None else 0.0)))
    except Exception:
        return 0.0


class ModelLifecycleTracker:
    """Thread-safe in-memory status tracker for model lifecycle stages.

    The existing job table is still the durable audit log.  This class provides
    a lightweight live status surface that the UI can poll to render circular
    indicators for model downloads, memory loading, inference, and future
    training jobs without changing the semantics of the underlying jobs.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._models: dict[str, dict[str, dict[str, Any]]] = {}

    @staticmethod
    def normalize_model_name(model_name: str | None) -> str:
        text = str(model_name or "unknown-model").strip()
        return text or "unknown-model"

    @staticmethod
    def normalize_stage(stage: str) -> str:
        text = str(stage or "").strip().lower()
        if text not in MODEL_LIFECYCLE_STAGES:
            raise ValueError(f"Unknown model lifecycle stage: {stage}")
        return text

    def _default_stage(self, model_name: str, stage: str) -> dict[str, Any]:
        return {
            "model_name": model_name,
            "stage": stage,
            "state": "idle",
            "active": False,
            "progress": 0.0,
            "percent": 0,
            "message": "Idle",
            "job_id": None,
            "started_at": None,
            "updated_at": None,
            "finished_at": None,
            "error": None,
            "result": None,
        }

    def _ensure_locked(self, model_name: str) -> dict[str, dict[str, Any]]:
        model_name = self.normalize_model_name(model_name)
        if model_name not in self._models:
            self._models[model_name] = {stage: self._default_stage(model_name, stage) for stage in MODEL_LIFECYCLE_STAGES}
        else:
            for stage in MODEL_LIFECYCLE_STAGES:
                self._models[model_name].setdefault(stage, self._default_stage(model_name, stage))
        return self._models[model_name]

    def ensure_model(self, model_name: str | None) -> dict[str, dict[str, Any]]:
        with self._lock:
            return deepcopy(self._ensure_locked(self.normalize_model_name(model_name)))

    def update(
        self,
        model_name: str | None,
        stage: str,
        *,
        state: str | None = None,
        progress: float | None = None,
        message: str | None = None,
        job_id: int | None = None,
        error: str | None = None,
        result: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        model_name = self.normalize_model_name(model_name)
        stage = self.normalize_stage(stage)
        now = now_iso()
        with self._lock:
            stages = self._ensure_locked(model_name)
            row = stages[stage]
            previous_state = row.get("state") or "idle"
            next_state = str(state or previous_state or "idle").lower()
            if state is not None:
                row["state"] = next_state
                if next_state in ACTIVE_STATES and previous_state not in ACTIVE_STATES:
                    row["started_at"] = now
                    row["finished_at"] = None
                    row["error"] = None
                    row["result"] = None
                if next_state in TERMINAL_STATES:
                    row["finished_at"] = now
            if progress is not None:
                row["progress"] = clamp_progress(progress)
            elif state == "queued":
                row["progress"] = 0.0
            elif state == "completed":
                row["progress"] = 1.0
            if message is not None:
                row["message"] = str(message)
            if job_id is not None:
                row["job_id"] = int(job_id)
            if error is not None:
                row["error"] = str(error)
            if result is not None:
                row["result"] = result
            if extra:
                row.update(extra)
            row["active"] = row.get("state") in ACTIVE_STATES
            row["percent"] = int(round(clamp_progress(row.get("progress")) * 100))
            row["updated_at"] = now
            return deepcopy(row)

    def fail(self, model_name: str | None, stage: str, exc: BaseException | str, *, job_id: int | None = None) -> dict[str, Any]:
        return self.update(
            model_name,
            stage,
            state="failed",
            message=str(exc),
            error=str(exc),
            job_id=job_id,
        )

    def complete(self, model_name: str | None, stage: str, *, message: str = "Completed", job_id: int | None = None, result: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.update(
            model_name,
            stage,
            state="completed",
            progress=1.0,
            message=message,
            job_id=job_id,
            result=result,
        )

    def reset(self, model_name: str | None, stage: str | None = None, *, message: str = "Idle") -> dict[str, Any] | dict[str, dict[str, Any]]:
        model_name = self.normalize_model_name(model_name)
        with self._lock:
            if stage:
                normalized = self.normalize_stage(stage)
                self._ensure_locked(model_name)[normalized] = self._default_stage(model_name, normalized)
                self._models[model_name][normalized]["message"] = message
                self._models[model_name][normalized]["updated_at"] = now_iso()
                return deepcopy(self._models[model_name][normalized])
            self._models[model_name] = {s: self._default_stage(model_name, s) for s in MODEL_LIFECYCLE_STAGES}
            for row in self._models[model_name].values():
                row["message"] = message
                row["updated_at"] = now_iso()
            return deepcopy(self._models[model_name])

    def is_active(self, model_name: str | None, stage: str | None = None) -> bool:
        model_name = self.normalize_model_name(model_name)
        with self._lock:
            stages = self._ensure_locked(model_name)
            if stage:
                return bool(stages[self.normalize_stage(stage)].get("active"))
            return any(bool(stages[s].get("active")) for s in MODEL_LIFECYCLE_STAGES)

    def progress_callback(
        self,
        model_name: str | None,
        stage: str,
        downstream: ProgressCallback | None = None,
        *,
        job_id: int | None = None,
    ) -> ProgressCallback:
        normalized_model = self.normalize_model_name(model_name)
        normalized_stage = self.normalize_stage(stage)

        def callback(value: float, message: str = "") -> None:
            self.update(
                normalized_model,
                normalized_stage,
                state="running",
                progress=value,
                message=message or f"{normalized_stage.title()} running",
                job_id=job_id,
            )
            if downstream:
                downstream(value, message)

        return callback

    def model_status(self, model_name: str | None) -> dict[str, Any]:
        model_name = self.normalize_model_name(model_name)
        with self._lock:
            stages = self._ensure_locked(model_name)
            return {"model_name": model_name, "stages": deepcopy(stages), "active": any(bool(row.get("active")) for row in stages.values())}

    def all_statuses(self) -> dict[str, Any]:
        with self._lock:
            for model_name in list(self._models):
                self._ensure_locked(model_name)
            models = deepcopy(self._models)
        aggregate = self._aggregate(models)
        return {"stages": list(MODEL_LIFECYCLE_STAGES), "models": models, "aggregate": aggregate}

    def _aggregate(self, models: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
        aggregate: dict[str, Any] = {}
        now = now_iso()
        for stage in MODEL_LIFECYCLE_STAGES:
            rows = [stages[stage] for stages in models.values() if stage in stages]
            active_rows = [row for row in rows if row.get("active")]
            if active_rows:
                progress = sum(clamp_progress(row.get("progress")) for row in active_rows) / max(1, len(active_rows))
                state = "running" if any(row.get("state") == "running" for row in active_rows) else "queued"
                latest = max(active_rows, key=lambda row: str(row.get("updated_at") or ""))
                aggregate[stage] = {
                    "model_name": latest.get("model_name"),
                    "stage": stage,
                    "state": state,
                    "active": True,
                    "progress": progress,
                    "percent": int(round(progress * 100)),
                    "message": latest.get("message") or f"{stage.title()} running",
                    "job_id": latest.get("job_id"),
                    "active_count": len(active_rows),
                    "updated_at": latest.get("updated_at") or now,
                }
                continue
            non_idle = [row for row in rows if row.get("state") != "idle"]
            if non_idle:
                latest = max(non_idle, key=lambda row: str(row.get("updated_at") or ""))
                aggregate[stage] = deepcopy(latest)
                aggregate[stage]["active_count"] = 0
            else:
                aggregate[stage] = {
                    "model_name": None,
                    "stage": stage,
                    "state": "idle",
                    "active": False,
                    "progress": 0.0,
                    "percent": 0,
                    "message": "Idle",
                    "job_id": None,
                    "active_count": 0,
                    "updated_at": None,
                }
        return aggregate

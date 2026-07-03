from __future__ import annotations

from pathlib import Path
from typing import Any

from ..database import Database
from ..models.registry import ModelRegistry
from ..schemas import ModelChatRequest, ModelRunRequest, ModelTagSelectionRequest, OrchestrationRequest
from .media_service import MediaService
from .model_service import ModelService
from .tag_service import TagService


class OrchestrationService:
    """Agentic, multi-step curation runs over selected media.

    The service intentionally keeps the orchestration plan explicit and auditable:
    every step has a type, model, threshold, prompt, and apply/dry-run behavior.
    Optional LLM/VLM adapters can be inserted into the plan, but the built-in
    assistant and model registry make the endpoint useful before those models are installed.
    """

    def __init__(self, db: Database, media: MediaService, tags: TagService, models: ModelService, registry: ModelRegistry):
        self.db = db
        self.media = media
        self.tags = tags
        self.models = models
        self.registry = registry

    def templates(self) -> list[dict[str, Any]]:
        assistant_model = self.models.default_orchestrator_model_name()
        return [
            {
                "key": "classifier-threshold-check",
                "label": "Classifier threshold check",
                "description": "Run a classifier/tagger over selected images and optionally apply predictions above threshold.",
                "request": {
                    "name": "Classifier threshold check",
                    "goal": "Find and apply tags/categories above a confidence threshold.",
                    "dry_run": True,
                    "apply_tags": False,
                    "steps": [
                        {"kind": "tag", "model_name": "rule-based-filename", "task": "tag", "threshold": 0.35, "apply": False}
                    ],
                },
            },
            {
                "key": "vlm-review-selected",
                "label": "VLM/LLM review selected media",
                "description": "Ask a VLM or assistant to review selected images and propose cleanup tags/captions.",
                "request": {
                    "name": "VLM/LLM review selected media",
                    "goal": "Review selected media for likely missing or incorrect tags.",
                    "dry_run": True,
                    "steps": [
                        {"kind": "vlm_check", "model_name": assistant_model, "prompt": "Review these media items for tag/caption cleanup. Return tags: and caption: lines if useful.", "apply": False}
                    ],
                },
            },
            {
                "key": "unknown-tag-cleanup",
                "label": "Unknown tag/category cleanup",
                "description": "Select tags that are unknown to the active dictionary, then preview or remove them.",
                "request": {
                    "name": "Unknown tag/category cleanup",
                    "goal": "Find tags not known by the selected profile.",
                    "dry_run": True,
                    "steps": [
                        {"kind": "tag_select", "model_name": assistant_model, "prompt": "select unknown tags", "apply": False}
                    ],
                },
            },
        ]

    def media_ids_for_request(self, request: OrchestrationRequest) -> list[int]:
        media_ids = list(request.media_ids)
        if request.dataset_id and not media_ids:
            rows = self.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1 ORDER BY id ASC", (request.dataset_id,))
            media_ids = [row["id"] for row in rows]
        if request.max_items:
            media_ids = media_ids[: max(0, request.max_items)]
        return media_ids

    def run(self, request: OrchestrationRequest, job_id: int, progress) -> dict[str, Any]:
        media_ids = self.media_ids_for_request(request)
        if not media_ids:
            return {"processed": 0, "steps": [], "message": "No media selected"}
        steps = request.steps or []
        if not steps:
            steps = [type("Step", (), {"kind": "tag", "model_name": "rule-based-filename", "task": "tag", "threshold": 0.35, "apply": False, "prompt": None, "categories": [], "tags": [], "options": {}})()]
        step_results: list[dict[str, Any]] = []
        total_work = max(1, len(media_ids) * len(steps))
        work_done = 0
        for step_idx, step in enumerate(steps, start=1):
            kind = step.kind
            if kind in {"classify", "tag", "caption"}:
                applied = 0
                predictions = 0
                for media_id in media_ids:
                    media = self.media.get(media_id)
                    if not media:
                        continue
                    pred = self.registry.predict(step.model_name or "rule-based-filename", Path(media.path), device=self._device_for_step(request), threshold=step.threshold, prompt=step.prompt, **(step.options or {}))
                    payload = {"kind": pred.kind, "tags": pred.tags, "caption": pred.caption, "classes": pred.classes, "raw": pred.raw}
                    self.media.add_prediction(media_id, job_id, step.model_name or "unknown", kind, payload)
                    predictions += 1
                    candidate_tags = [tag for tag, score in (pred.tags or pred.classes) if float(score) >= float(step.threshold)]
                    if (step.apply or request.apply_tags) and candidate_tags and not request.dry_run:
                        current = self.tags.get_tags(media_id)
                        merged = list(current)
                        for tag in candidate_tags:
                            if tag not in merged:
                                merged.append(tag)
                        self.tags.set_tags(media_id, merged, source=f"orchestrate:{step.model_name}", save_sidecar=True, profile_key=request.profile_key, order_strategy="retain")
                        applied += len(candidate_tags)
                    if (step.apply or request.apply_captions) and pred.caption and not request.dry_run:
                        self.db.upsert_caption(media_id, pred.caption, source=f"orchestrate:{step.model_name}")
                        applied += 1
                    work_done += 1
                    progress(work_done / total_work, f"Step {step_idx}/{len(steps)} {kind}: {work_done}/{total_work}")
                step_results.append({"kind": kind, "model_name": step.model_name, "predictions": predictions, "applied": applied})
            elif kind in {"vlm_check", "llm_review"}:
                resolved_model = self.models.resolve_assistant_model_name(step.model_name, purpose="orchestrator")
                response = self.models.chat(ModelChatRequest(
                    model_name=resolved_model,
                    prompt=step.prompt or request.goal or "Review selected media for dataset curation.",
                    dataset_id=request.dataset_id,
                    media_ids=media_ids,
                    use_selected_media=True,
                    apply_suggested_tags=(step.apply or request.apply_tags) and not request.dry_run,
                    apply_suggested_caption=(step.apply or request.apply_captions) and not request.dry_run,
                    device=self._device_for_step(request),
                    options=step.options or {},
                ))
                step_results.append({"kind": kind, "model_name": resolved_model, "response": response})
                work_done += len(media_ids)
                progress(work_done / total_work, f"Step {step_idx}/{len(steps)} {kind}: model review complete")
            elif kind == "tag_select":
                resolved_model = self.models.resolve_assistant_model_name(step.model_name, purpose="orchestrator")
                selection = self.models.select_tags(ModelTagSelectionRequest(
                    media_ids=media_ids,
                    dataset_id=request.dataset_id,
                    criteria=step.prompt or request.goal or "",
                    model_name=resolved_model,
                    profile_key=request.profile_key,
                    categories=step.categories,
                    candidate_tags=step.tags,
                    operation="preview" if request.dry_run or not step.apply else "remove",
                    device=self._device_for_step(request),
                    options=step.options or {},
                ))
                step_results.append({"kind": kind, "model_name": resolved_model, "selection": selection})
                work_done += len(media_ids)
                progress(work_done / total_work, f"Step {step_idx}/{len(steps)} tag selection complete")
            else:
                step_results.append({"kind": kind, "skipped": True, "reason": "Unsupported step kind"})
        return {"processed": len(media_ids), "dry_run": request.dry_run, "steps": step_results, "device_policy": request.device_policy, "devices": request.devices}

    def _device_for_step(self, request: OrchestrationRequest) -> str:
        if request.device_policy == "cpu":
            return "cpu"
        if request.devices:
            return request.devices[0]
        if request.device_policy in {"single_gpu", "multi_gpu", "custom"}:
            return "auto_cuda"
        return "auto"

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..schemas import (
    DatasetPipelineBranchEvaluateRequest,
    DatasetPipelineBranchExportRequest,
    DatasetPipelinePlanRequest,
    DatasetPipelineRulesRequest,
    DownloadRequest,
    ModelChatRequest,
)
from ..utils import save_json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str, fallback: str = "workflow") -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()).strip("._-")
    return text[:90] or fallback


def _json_load(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return deepcopy(default)


STEP_CATALOG: list[dict[str, Any]] = [
    {
        "type": "manual_review_gate",
        "label": "Manual approval / review gate",
        "category": "control",
        "description": "Pause a workflow at a human-checkpoint before destructive, expensive, or subjective actions.",
        "safe_to_auto_run": False,
        "outputs": ["review_note"],
    },
    {
        "type": "create_branch",
        "label": "Create/update global-dataset branch",
        "category": "global_dataset",
        "description": "Create the editable dataset-configuration layer where tags/captions and variants can be changed without touching originals.",
        "safe_to_auto_run": True,
        "outputs": ["branch"],
    },
    {
        "type": "ingest_existing_dataset",
        "label": "Link existing imported dataset into branch",
        "category": "global_dataset",
        "description": "Register selected/imported media into the global original layer and link it into the workflow branch.",
        "safe_to_auto_run": True,
        "outputs": ["branch_items", "global_assets"],
    },
    {
        "type": "sync_tag_dictionary",
        "label": "Sync source tag dictionary",
        "category": "tags",
        "description": "Prepare source-specific valid tags/categories/aliases before labeling/downloading.",
        "safe_to_auto_run": False,
        "outputs": ["tag_dictionary_status"],
    },
    {
        "type": "download",
        "label": "Download authorized source data",
        "category": "download",
        "description": "Run a configured downloader payload and register/reuse global originals where possible.",
        "safe_to_auto_run": False,
        "outputs": ["downloaded_files"],
    },
    {
        "type": "character_reference_rank",
        "label": "Character-reference prune/rank",
        "category": "selection",
        "description": "Use one/few-shot character reference matching to rank and optionally prune a branch without training a new model.",
        "safe_to_auto_run": True,
        "outputs": ["character_reference_run"],
    },
    {
        "type": "build_label_rules",
        "label": "Build label/caption rule packet",
        "category": "labeling",
        "description": "Generate deterministic rules for LoRA/IC-LoRA/ControlNet/embedding dataset preparation.",
        "safe_to_auto_run": True,
        "outputs": ["rules_packet"],
    },
    {
        "type": "build_model_prompt",
        "label": "Build LLM/VLM prompt packet",
        "category": "labeling",
        "description": "Create a compact prompt packet that a selected local/cloud assistant model can use to rewrite/validate labels.",
        "safe_to_auto_run": True,
        "outputs": ["prompt_packet"],
    },
    {
        "type": "assistant_refine_labels",
        "label": "Assistant-guided label refinement",
        "category": "labeling",
        "description": "Ask the selected assistant model for a workflow-specific label/caption refinement plan. Applies nothing unless paired with an apply step.",
        "safe_to_auto_run": False,
        "outputs": ["assistant_response"],
    },
    {
        "type": "dry_run_label_rules",
        "label": "Dry-run label rules",
        "category": "labeling",
        "description": "Preview deterministic branch-sidecar cleanup before writing changes.",
        "safe_to_auto_run": True,
        "outputs": ["rule_application_preview"],
    },
    {
        "type": "apply_label_rules",
        "label": "Apply label rules to branch sidecars",
        "category": "labeling",
        "description": "Write deterministic tag/caption sidecar changes into the branch layer only.",
        "safe_to_auto_run": False,
        "outputs": ["rule_application_job"],
    },
    {
        "type": "plan_augmentations",
        "label": "Plan augmentation/upscale variants",
        "category": "augmentation",
        "description": "Choose branch-local augmentations based on LoRA type and dataset goal.",
        "safe_to_auto_run": True,
        "outputs": ["augmentation_plan"],
    },
    {
        "type": "create_augmentation_variants",
        "label": "Create branch-local variants",
        "category": "augmentation",
        "description": "Create new branch-layer media variants such as headshot crops, style crops, bucket copies, or conservative upscales.",
        "safe_to_auto_run": False,
        "outputs": ["augmentation_job"],
    },
    {
        "type": "regularization_plan",
        "label": "Regularization / prior-preservation plan",
        "category": "training_prep",
        "description": "Create a trainer-aware policy for whether class/regularization data is needed and how to caption it.",
        "safe_to_auto_run": True,
        "outputs": ["regularization_policy"],
    },
    {
        "type": "evaluate_branch",
        "label": "Evaluate branch readiness",
        "category": "quality",
        "description": "Measure branch readiness, caption coverage, tag density, variants, and export readiness.",
        "safe_to_auto_run": True,
        "outputs": ["readiness_metrics"],
    },
    {
        "type": "export_branch",
        "label": "Export final training branch",
        "category": "export",
        "description": "Export sidecars/manifests/media links in the format expected by a target trainer/tool.",
        "safe_to_auto_run": False,
        "outputs": ["export_manifest"],
    },
    {
        "type": "trainer_handoff",
        "label": "Build external trainer handoff",
        "category": "handoff",
        "description": "Create a command/API/MCP handoff packet for Kohya, OneTrainer, Diffusers scripts, ComfyUI, LTX, or generic providers.",
        "safe_to_auto_run": True,
        "outputs": ["handoff_packet"],
    },
    {
        "type": "remote_dispatch_plan",
        "label": "Remote worker dispatch plan",
        "category": "distributed",
        "description": "Plan fork/join work across configured remote workers without executing the remote action yet.",
        "safe_to_auto_run": True,
        "outputs": ["dispatch_plan"],
    },
]

WORKFLOW_TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "full_dataset_curation",
        "label": "Full automated dataset curation",
        "description": "Select a dataset/branch and let the tool plan labeling, pruning, augmentation, evaluation, export, and handoff.",
        "steps": [
            "create_branch", "ingest_existing_dataset", "build_label_rules", "build_model_prompt",
            "dry_run_label_rules", "manual_review_gate", "apply_label_rules", "plan_augmentations",
            "manual_review_gate", "create_augmentation_variants", "regularization_plan", "evaluate_branch", "export_branch", "trainer_handoff",
        ],
    },
    {
        "key": "character_lora_auto_prep",
        "label": "Character LoRA / OC identity prep",
        "description": "Build a branch for a character LoRA, optionally prune by reference, add identity-focused crops, and export.",
        "dataset_goal": "character",
        "adapter_type": "lora",
        "steps": [
            "create_branch", "ingest_existing_dataset", "character_reference_rank", "build_label_rules", "build_model_prompt",
            "dry_run_label_rules", "apply_label_rules", "plan_augmentations", "create_augmentation_variants", "regularization_plan", "evaluate_branch", "export_branch",
        ],
    },
    {
        "key": "style_lora_auto_prep",
        "label": "Style LoRA prep",
        "description": "Prepare style-focused tags/captions, style/detail variants, quality gates, and trainer export.",
        "dataset_goal": "style",
        "adapter_type": "lora",
        "steps": [
            "create_branch", "ingest_existing_dataset", "build_label_rules", "build_model_prompt", "dry_run_label_rules", "apply_label_rules",
            "plan_augmentations", "create_augmentation_variants", "regularization_plan", "evaluate_branch", "export_branch",
        ],
    },

    {
        "key": "character_style_lora_auto_prep",
        "label": "Character + Style / OC + style LoRA prep",
        "description": "Prepare an identity-preserving branch where both the character token and style token are kept explicit, with body/detail crops and quality gates.",
        "dataset_goal": "character_style",
        "adapter_type": "lora",
        "steps": [
            "create_branch", "ingest_existing_dataset", "character_reference_rank", "build_label_rules", "build_model_prompt",
            "dry_run_label_rules", "apply_label_rules", "plan_augmentations", "create_augmentation_variants", "regularization_plan", "evaluate_branch", "export_branch",
        ],
    },
    {
        "key": "concept_lora_auto_prep",
        "label": "Concept LoRA prep",
        "description": "Prepare a concept/object/action branch with concept-centered captions, concept crops, regularization guidance, readiness checks, and export.",
        "dataset_goal": "concept",
        "adapter_type": "lora",
        "steps": [
            "create_branch", "ingest_existing_dataset", "build_label_rules", "build_model_prompt", "dry_run_label_rules", "apply_label_rules",
            "plan_augmentations", "create_augmentation_variants", "regularization_plan", "evaluate_branch", "export_branch",
        ],
    },
    {
        "key": "download_to_training_branch",
        "label": "Download/query to training branch",
        "description": "Sync dictionaries, download authorized source media, link/reuse global originals, then prepare the branch.",
        "steps": [
            "sync_tag_dictionary", "download", "create_branch", "build_label_rules", "build_model_prompt", "dry_run_label_rules",
            "manual_review_gate", "apply_label_rules", "plan_augmentations", "evaluate_branch", "export_branch",
        ],
    },
    {
        "key": "branch_quality_export_only",
        "label": "Existing branch quality gate + export",
        "description": "For a branch already curated: build final rules, evaluate readiness, and export/handoff.",
        "steps": ["build_label_rules", "regularization_plan", "evaluate_branch", "export_branch", "trainer_handoff"],
    },
]


class WorkflowAutomationService:
    """Persistent, user/model editable workflow layer for automating curation.

    Workflows are stored as JSON so users can directly edit them, models can emit
    them, and the GUI can modify the same representation.  Running a workflow is
    conservative: expensive/destructive operations are skipped unless the run
    request explicitly approves unsafe steps.
    """

    def __init__(self, paths: Any, app_context_getter: Callable[[], Any] | None = None):
        self.paths = paths
        self._get_context = app_context_getter
        self.root = paths.runtime / "automation_workflows"
        self.root.mkdir(parents=True, exist_ok=True)
        self.workflows_path = self.root / "workflows.json"
        self.runs_dir = self.root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def catalog(self) -> dict[str, Any]:
        return {
            "step_catalog": deepcopy(STEP_CATALOG),
            "templates": deepcopy(WORKFLOW_TEMPLATES),
            "storage_root": str(self.root),
            "design_contract": {
                "editable_by_user": True,
                "editable_by_model": True,
                "branch_safe_by_default": True,
                "approval_required_for_unsafe_steps": True,
                "global_originals_are_not_mutated": True,
            },
        }

    def list_workflows(self) -> list[dict[str, Any]]:
        payload = _json_load(self.workflows_path, {"workflows": []})
        rows = payload.get("workflows") if isinstance(payload, dict) else payload
        rows = rows if isinstance(rows, list) else []
        return sorted(rows, key=lambda x: str(x.get("updated_at") or x.get("created_at") or ""), reverse=True)

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        for workflow in self.list_workflows():
            if str(workflow.get("id")) == str(workflow_id):
                return workflow
        return None

    def save_workflow(self, workflow: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        workflow = deepcopy(workflow or {})
        if not workflow.get("id"):
            workflow["id"] = f"wf_{_slug(workflow.get('name') or 'workflow')}_{uuid.uuid4().hex[:8]}"
        workflow.setdefault("schema_version", 1)
        workflow.setdefault("created_at", now)
        workflow["updated_at"] = now
        workflow.setdefault("steps", [])
        self.validate_workflow(workflow, strict=False)
        rows = [w for w in self.list_workflows() if str(w.get("id")) != str(workflow.get("id"))]
        rows.append(workflow)
        save_json(self.workflows_path, {"workflows": rows, "updated_at": now})
        (self.root / f"{workflow['id']}.json").write_text(json.dumps(workflow, indent=2, ensure_ascii=False), encoding="utf-8")
        return workflow

    def delete_workflow(self, workflow_id: str) -> dict[str, Any]:
        before = self.list_workflows()
        rows = [w for w in before if str(w.get("id")) != str(workflow_id)]
        save_json(self.workflows_path, {"workflows": rows, "updated_at": _now()})
        single = self.root / f"{workflow_id}.json"
        if single.exists():
            try:
                single.unlink()
            except Exception:
                pass
        return {"ok": True, "deleted": len(before) - len(rows), "workflow_id": workflow_id}

    def create_from_request(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        template_key = str(data.get("template_key") or "full_dataset_curation")
        template = self._template(template_key)
        branch = str(data.get("branch_name") or data.get("global_dataset_branch") or _slug(data.get("name") or data.get("goal") or "workflow_branch"))
        base = {
            "name": data.get("name") or template.get("label") or "Dataset curation workflow",
            "description": template.get("description") or "",
            "goal": data.get("goal") or "Prepare this dataset branch for training.",
            "instructions": data.get("instructions") or "",
            "assistant_model": data.get("assistant_model") or "dataset-assistant",
            "source_dataset_id": data.get("source_dataset_id"),
            "branch_name": branch,
            "target_model": data.get("target_model") or template.get("target_model") or "sdxl",
            "adapter_type": data.get("adapter_type") or template.get("adapter_type") or "lora",
            "dataset_goal": data.get("dataset_goal") or template.get("dataset_goal") or "character",
            "training_tool": data.get("training_tool") or "generic",
            "automation_level": data.get("automation_level") or "guided",
            "memory_policy": data.get("memory_policy") or "persist_prompt_refinements",
            "approval_policy": data.get("approval_policy") or "unsafe_steps_require_approval",
            "created_by": data.get("created_by") or "user_or_assistant",
            "steps": self._steps_from_template(template, data),
        }
        return self.save_workflow(base)

    def plan_from_goal(self, payload: Any, *, use_model: bool = False) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        workflow = self.create_from_request({**data, "template_key": data.get("template_key") or self._infer_template(data)})
        prompt = self._workflow_design_prompt(workflow)
        response = None
        if use_model and self._get_context:
            c = self._get_context()
            request = ModelChatRequest(
                model_name=workflow.get("assistant_model") or "dataset-assistant",
                prompt=prompt,
                dataset_id=workflow.get("source_dataset_id"),
                options={"chat_assistant": True, "workflow_design": True, "min_chat_max_new_tokens": 2048},
            )
            response = c.models.chat(request)
            candidate = self._extract_json_workflow(response.get("response") or "")
            if candidate:
                candidate.setdefault("id", workflow["id"])
                candidate.setdefault("created_at", workflow.get("created_at") or _now())
                workflow = self.save_workflow({**workflow, **candidate, "updated_by_model": True})
        return {"ok": True, "workflow": workflow, "prompt": prompt, "assistant_response": response}

    def refine_workflow(self, workflow_id: str, payload: Any, *, use_model: bool = False) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        instructions = str(data.get("instructions") or "").strip()
        if data.get("workflow") and isinstance(data["workflow"], dict):
            workflow = self.save_workflow({**workflow, **data["workflow"], "last_refine_instructions": instructions})
        prompt = self._workflow_refine_prompt(workflow, instructions)
        response = None
        if use_model and self._get_context:
            c = self._get_context()
            response = c.models.chat(ModelChatRequest(model_name=data.get("assistant_model") or workflow.get("assistant_model") or "dataset-assistant", prompt=prompt, options={"chat_assistant": True, "workflow_refine": True}))
            candidate = self._extract_json_workflow(response.get("response") or "")
            if candidate:
                workflow = self.save_workflow({**workflow, **candidate, "last_refine_instructions": instructions, "updated_by_model": True})
        return {"ok": True, "workflow": workflow, "prompt": prompt, "assistant_response": response}

    def validate_workflow(self, workflow: dict[str, Any] | str, strict: bool = True) -> dict[str, Any]:
        if isinstance(workflow, str):
            workflow = self.get_workflow(workflow) or {}
        known = {x["type"] for x in STEP_CATALOG}
        errors: list[str] = []
        warnings: list[str] = []
        if not workflow:
            errors.append("Workflow is empty or unknown.")
        if not workflow.get("name"):
            warnings.append("Workflow has no human-readable name.")
        steps = workflow.get("steps") or []
        if not isinstance(steps, list) or not steps:
            errors.append("Workflow has no steps.")
        step_ids = set()
        for idx, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                errors.append(f"Step {idx} is not an object.")
                continue
            stype = str(step.get("type") or "").strip()
            if stype not in known:
                errors.append(f"Step {idx} has unknown type: {stype or '(blank)'}")
            sid = str(step.get("id") or f"step_{idx}")
            if sid in step_ids:
                warnings.append(f"Duplicate step id: {sid}")
            step_ids.add(sid)
            if self._step_requires_approval(step) and not step.get("requires_approval", True):
                warnings.append(f"Step {sid} is unsafe but does not explicitly require approval.")
        return {"ok": not errors, "errors": errors, "warnings": warnings, "step_count": len(steps) if isinstance(steps, list) else 0}

    def dry_run(self, workflow_id: str, payload: Any | None = None) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        return self.run_workflow(workflow, data | {"dry_run": True}, progress=None)

    def run_workflow(self, workflow_or_id: dict[str, Any] | str, payload: Any | None = None, progress=None) -> dict[str, Any]:
        if isinstance(workflow_or_id, str):
            workflow = self.get_workflow(workflow_or_id)
            if not workflow:
                raise ValueError(f"Unknown workflow: {workflow_or_id}")
        else:
            workflow = deepcopy(workflow_or_id)
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        dry_run = bool(data.get("dry_run", False))
        approve_unsafe = bool(data.get("approve_unsafe_steps", False))
        start_at = int(data.get("start_at_step", 1) or 1)
        stop_after = data.get("stop_after_step")
        stop_after = int(stop_after) if stop_after not in (None, "") else None
        validation = self.validate_workflow(workflow, strict=False)
        if not validation["ok"]:
            raise ValueError("Workflow validation failed: " + "; ".join(validation["errors"]))
        c = self._require_context()
        run_id = f"run_{_slug(workflow.get('name') or workflow.get('id') or 'workflow')}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        steps = [s for s in workflow.get("steps", []) if s.get("enabled", True)]
        results: list[dict[str, Any]] = []
        total = max(1, len(steps))
        context = self._base_step_context(workflow, data)
        status = "completed"
        for idx, step in enumerate(steps, start=1):
            if idx < start_at:
                continue
            if stop_after is not None and idx > stop_after:
                break
            stype = str(step.get("type") or "")
            if progress:
                progress((idx - 1) / total, f"Workflow step {idx}/{len(steps)}: {step.get('label') or stype}")
            try:
                requires_approval = self._step_requires_approval(step)
                if dry_run:
                    result = self._dry_step(step, context, idx)
                elif requires_approval and not approve_unsafe:
                    result = {"ok": True, "skipped": True, "reason": "requires approval", "requires_approval": True}
                    status = "waiting_for_approval"
                    results.append({"index": idx, "id": step.get("id"), "type": stype, "status": "skipped", "result": result})
                    if data.get("stop_on_approval_gate", True):
                        break
                    continue
                else:
                    result = self._execute_step(c, step, context, idx, progress=progress)
                context.setdefault("step_results", {})[str(step.get("id") or idx)] = result
                results.append({"index": idx, "id": step.get("id"), "type": stype, "status": "ok", "result": result})
            except Exception as exc:
                status = "failed"
                results.append({"index": idx, "id": step.get("id"), "type": stype, "status": "failed", "error": str(exc)})
                if data.get("continue_on_error") is not True:
                    break
        if progress:
            progress(1.0, f"Workflow {status}")
        manifest = {"ok": status in {"completed", "waiting_for_approval"}, "run_id": run_id, "status": status, "dry_run": dry_run, "workflow_id": workflow.get("id"), "workflow_name": workflow.get("name"), "started_at": _now(), "finished_at": _now(), "results": results, "context": context}
        path = self.runs_dir / f"{run_id}.json"
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        manifest["manifest_path"] = str(path)
        return manifest

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self.runs_dir.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[: max(1, int(limit or 50))]:
            item = _json_load(path, {})
            if isinstance(item, dict):
                rows.append({k: item.get(k) for k in ("run_id", "status", "dry_run", "workflow_id", "workflow_name", "started_at", "finished_at") } | {"manifest_path": str(path)})
        return rows

    def _template(self, key: str) -> dict[str, Any]:
        return deepcopy(next((t for t in WORKFLOW_TEMPLATES if t["key"] == key), WORKFLOW_TEMPLATES[0]))

    def _infer_template(self, data: dict[str, Any]) -> str:
        text = " ".join(str(data.get(k) or "") for k in ("name", "goal", "instructions", "dataset_goal")).lower()
        if "download" in text:
            return "download_to_training_branch"
        if ("character" in text or "oc" in text) and "style" in text:
            return "character_style_lora_auto_prep"
        if "concept" in text or "object" in text or "action" in text:
            return "concept_lora_auto_prep"
        if "style" in text and "character" not in text:
            return "style_lora_auto_prep"
        if "character" in text or "oc" in text:
            return "character_lora_auto_prep"
        if "export" in text and "branch" in text:
            return "branch_quality_export_only"
        return "full_dataset_curation"

    def _steps_from_template(self, template: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
        cat_by_type = {x["type"]: x for x in STEP_CATALOG}
        out = []
        branch = str(data.get("branch_name") or _slug(data.get("name") or data.get("goal") or "workflow_branch"))
        for idx, stype in enumerate(template.get("steps") or [], start=1):
            catalog = cat_by_type.get(stype, {"label": stype, "safe_to_auto_run": True})
            params = self._default_params_for_step(stype, data, branch)
            out.append({
                "id": f"s{idx:02d}_{stype}",
                "type": stype,
                "label": catalog.get("label") or stype,
                "enabled": True,
                "requires_approval": not bool(catalog.get("safe_to_auto_run", False)),
                "params": params,
            })
        return out

    def _default_params_for_step(self, stype: str, data: dict[str, Any], branch: str) -> dict[str, Any]:
        common = {
            "branch_name": branch,
            "target_model": data.get("target_model") or "sdxl",
            "adapter_type": data.get("adapter_type") or "lora",
            "dataset_goal": data.get("dataset_goal") or "character",
            "trigger_token": data.get("trigger_token") or "<trigger_token>",
            "style_trigger_token": data.get("style_trigger_token") or "<style_trigger>",
            "additional_notes": data.get("instructions") or data.get("goal") or "",
        }
        if stype == "ingest_existing_dataset":
            return {"dataset_id": data.get("source_dataset_id"), "branch_name": branch, "max_items": data.get("max_items") or 0, "copy_sidecars": True}
        if stype == "sync_tag_dictionary":
            return {"profile_key": data.get("tag_profile") or "e621", "force_download": False}
        if stype == "download":
            return {"download_request": data.get("download_request") or {}, "output_dir": data.get("download_output_dir") or ""}
        if stype == "character_reference_rank":
            return {"target_name": data.get("character_name") or data.get("target_name") or "", "branch_name": branch, "threshold": data.get("character_threshold") or 0.62, "max_items": data.get("max_items") or 5000}
        if stype == "export_branch":
            return {**common, "training_tool": data.get("training_tool") or "generic", "include_media": bool(data.get("include_media", False)), "link_mode": data.get("link_mode") or "reference"}
        if stype == "trainer_handoff":
            return {"training_tool": data.get("training_tool") or "generic", "export_dir": data.get("export_dir") or "", "notes": data.get("instructions") or ""}
        if stype == "manual_review_gate":
            return {"message": "Review prior output before continuing.", "required": True}
        if stype == "remote_dispatch_plan":
            return {"branch_name": branch, "mode": "plan_only"}
        return common

    def _base_step_context(self, workflow: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        return {
            "workflow_id": workflow.get("id"),
            "branch_name": data.get("branch_name") or workflow.get("branch_name") or "default",
            "source_dataset_id": data.get("source_dataset_id") or workflow.get("source_dataset_id"),
            "target_model": data.get("target_model") or workflow.get("target_model") or "sdxl",
            "adapter_type": data.get("adapter_type") or workflow.get("adapter_type") or "lora",
            "dataset_goal": data.get("dataset_goal") or workflow.get("dataset_goal") or "character",
            "training_tool": data.get("training_tool") or workflow.get("training_tool") or "generic",
            "assistant_model": data.get("assistant_model") or workflow.get("assistant_model") or "dataset-assistant",
            "step_results": {},
        }

    def _step_payload(self, step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        params = deepcopy(step.get("params") or {})
        for key in ("branch_name", "source_dataset_id", "target_model", "adapter_type", "dataset_goal", "training_tool"):
            if params.get(key) in (None, "", 0):
                params[key] = context.get(key)
        return params

    def _dry_step(self, step: dict[str, Any], context: dict[str, Any], idx: int) -> dict[str, Any]:
        params = self._step_payload(step, context)
        return {"ok": True, "dry_run": True, "would_execute": step.get("type"), "index": idx, "label": step.get("label"), "params": params, "requires_approval": self._step_requires_approval(step)}

    def _execute_step(self, c: Any, step: dict[str, Any], context: dict[str, Any], idx: int, progress=None) -> dict[str, Any]:
        stype = str(step.get("type") or "")
        params = self._step_payload(step, context)
        branch = str(params.get("branch_name") or context.get("branch_name") or "default")
        target = str(params.get("target_model") or context.get("target_model") or "sdxl")
        adapter = str(params.get("adapter_type") or context.get("adapter_type") or "lora")
        goal = str(params.get("dataset_goal") or context.get("dataset_goal") or "character")
        if stype == "manual_review_gate":
            return {"ok": True, "manual_gate_passed": True, "message": params.get("message") or "Manual gate approved by run request."}
        if stype == "create_branch":
            return c.global_dataset.ensure_branch(branch, purpose=params.get("purpose") or f"Workflow branch: {context.get('workflow_id')}", settings={"workflow_id": context.get("workflow_id"), "target_model": target, "adapter_type": adapter, "dataset_goal": goal})
        if stype == "ingest_existing_dataset":
            dataset_id = int(params.get("dataset_id") or context.get("source_dataset_id") or 0)
            if not dataset_id:
                return {"ok": True, "skipped": True, "reason": "No source_dataset_id supplied."}
            max_items = int(params.get("max_items") or 0)
            sql = "SELECT id FROM media WHERE active=1 AND dataset_id=? ORDER BY id"
            sql_params: list[Any] = [dataset_id]
            if max_items > 0:
                sql += " LIMIT ?"
                sql_params.append(max_items)
            rows = c.db.query(sql, tuple(sql_params))
            media_ids = [int(r["id"]) for r in rows]
            result = c.global_dataset.link_assets(branch_name=branch, media_ids=media_ids, copy_sidecars=bool(params.get("copy_sidecars", True)), note="linked by automation workflow")
            result["source_dataset_id"] = dataset_id
            result["media_ids_seen"] = len(media_ids)
            return result
        if stype == "sync_tag_dictionary":
            profile_key = str(params.get("profile_key") or getattr(c.settings, "default_tag_profile", "e621") or "e621")
            return c.tags.import_default_exports(profile_key=profile_key, user_agent=c.settings.downloader_user_agent, cache_hours=int(getattr(c.settings, "tag_db_export_cache_hours", 336) or 336), progress=progress, replace_existing=True, force_download=bool(params.get("force_download", False)))
        if stype == "download":
            request_data = dict(params.get("download_request") or {})
            if not request_data:
                return {"ok": True, "skipped": True, "reason": "No download_request configured for this workflow step."}
            payload = DownloadRequest(**request_data)
            return c.downloads.run(payload, progress=progress)
        if stype == "character_reference_rank":
            if not params.get("target_name"):
                return {"ok": True, "skipped": True, "reason": "No target_name/character profile supplied."}
            return c.character_reference.rank({"target_name": params.get("target_name"), "branch_name": branch, "threshold": params.get("threshold", 0.62), "max_items": params.get("max_items", 5000), "return_limit": params.get("return_limit", 500)}, progress=progress)
        if stype == "build_label_rules":
            return c.dataset_pipeline.build_rules(DatasetPipelineRulesRequest(target_model=target, adapter_type=adapter, dataset_goal=goal, trigger_token=params.get("trigger_token") or "<trigger_token>", style_trigger_token=params.get("style_trigger_token") or "<style_trigger>", additional_notes=params.get("additional_notes") or ""))
        if stype == "build_model_prompt":
            return c.pipeline_prep.build_prompt({"target_model": target, "adapter_type": adapter, "dataset_goal": goal, "branch_name": branch, "trigger_token": params.get("trigger_token") or "<trigger_token>", "style_trigger_token": params.get("style_trigger_token") or "<style_trigger>", "additional_notes": params.get("additional_notes") or "", "max_items": int(params.get("max_items") or 40)})
        if stype == "assistant_refine_labels":
            prompt = params.get("prompt") or self._assistant_label_refinement_prompt(context, params)
            return c.models.chat(ModelChatRequest(model_name=params.get("assistant_model") or context.get("assistant_model") or "dataset-assistant", prompt=prompt, options={"chat_assistant": True, "workflow_label_refinement": True, "min_chat_max_new_tokens": 2048}))
        if stype == "dry_run_label_rules":
            return c.pipeline_prep.apply_rules({"target_model": target, "adapter_type": adapter, "dataset_goal": goal, "branch_name": branch, "dry_run": True, "use_model": False, "trigger_token": params.get("trigger_token") or "<trigger_token>", "style_trigger_token": params.get("style_trigger_token") or "<style_trigger>", "additional_notes": params.get("additional_notes") or ""})
        if stype == "apply_label_rules":
            return c.pipeline_prep.apply_rules({"target_model": target, "adapter_type": adapter, "dataset_goal": goal, "branch_name": branch, "dry_run": False, "use_model": False, "trigger_token": params.get("trigger_token") or "<trigger_token>", "style_trigger_token": params.get("style_trigger_token") or "<style_trigger>", "additional_notes": params.get("additional_notes") or ""})
        if stype == "plan_augmentations":
            return c.pipeline_prep.augmentation_plan({"target_model": target, "adapter_type": adapter, "dataset_goal": goal, "branch_name": branch, "dry_run": True, "max_items": int(params.get("max_items") or 200)})
        if stype == "create_augmentation_variants":
            return c.pipeline_prep.apply_augmentations({"target_model": target, "adapter_type": adapter, "dataset_goal": goal, "branch_name": branch, "dry_run": False, "max_items": int(params.get("max_items") or 200)})
        if stype == "regularization_plan":
            return c.pipeline_prep.regularization_plan({"target_model": target, "adapter_type": adapter, "dataset_goal": goal, "branch_name": branch})
        if stype == "evaluate_branch":
            return c.dataset_pipeline.evaluate_branch(DatasetPipelineBranchEvaluateRequest(target_model=target, adapter_type=adapter, dataset_goal=goal, branch_name=branch, trigger_token=params.get("trigger_token") or "<trigger_token>", style_trigger_token=params.get("style_trigger_token") or "<style_trigger>", additional_notes=params.get("additional_notes") or ""))
        if stype == "export_branch":
            return c.dataset_pipeline.export_branch(DatasetPipelineBranchExportRequest(target_model=target, adapter_type=adapter, dataset_goal=goal, branch_name=branch, training_tool=params.get("training_tool") or context.get("training_tool") or "generic", include_media=bool(params.get("include_media", False)), link_mode=params.get("link_mode") or "reference", trigger_token=params.get("trigger_token") or "<trigger_token>", style_trigger_token=params.get("style_trigger_token") or "<style_trigger>", additional_notes=params.get("additional_notes") or ""))
        if stype == "trainer_handoff":
            return c.dataset_pipeline.trainer_handoff({"training_tool": params.get("training_tool") or context.get("training_tool") or "generic", "export_dir": params.get("export_dir") or "", "provider_profile": params.get("provider_profile") or "", "notes": params.get("notes") or "workflow handoff"})
        if stype == "remote_dispatch_plan":
            return c.distributed.plan_model_dispatch({"task_type": "workflow", "branch_name": branch, "workflow_id": context.get("workflow_id"), "mode": "plan_only"}) if hasattr(c.distributed, "plan_model_dispatch") else {"ok": True, "planned": True, "note": "Distributed service does not expose plan_model_dispatch in this build."}
        raise ValueError(f"Unsupported workflow step type: {stype}")

    def _step_requires_approval(self, step: dict[str, Any]) -> bool:
        if bool(step.get("requires_approval", False)):
            return True
        catalog = next((x for x in STEP_CATALOG if x["type"] == step.get("type")), {})
        return not bool(catalog.get("safe_to_auto_run", True))

    def _require_context(self) -> Any:
        if not self._get_context:
            raise RuntimeError("Workflow service is not attached to an app context.")
        return self._get_context()

    def _workflow_design_prompt(self, workflow: dict[str, Any]) -> str:
        return (
            "You are designing a Data Curation Tool automation workflow. Return JSON only. "
            "The workflow must preserve global originals, perform edits in branch sidecars/configs, require approval for unsafe steps, "
            "and prepare data for the requested model/training target.\n\n"
            f"Current workflow draft:\n{json.dumps(workflow, indent=2, ensure_ascii=False)}\n\n"
            "Allowed step types:\n" + json.dumps(STEP_CATALOG, indent=2, ensure_ascii=False)
        )

    def _workflow_refine_prompt(self, workflow: dict[str, Any], instructions: str) -> str:
        return (
            "Refine this Data Curation Tool workflow. Return the complete replacement workflow JSON only. "
            "Keep ids stable unless a step is truly replaced. Preserve branch-safe behavior.\n\n"
            f"User instructions:\n{instructions}\n\nWorkflow JSON:\n{json.dumps(workflow, indent=2, ensure_ascii=False)}"
        )

    def _assistant_label_refinement_prompt(self, context: dict[str, Any], params: dict[str, Any]) -> str:
        return (
            "Review the dataset-prep context and propose label/caption refinements for the branch. "
            "Do not fabricate source facts. Preserve critical character/style/concept descriptors. Return a concise action plan plus JSON suggestions.\n\n"
            f"Context:\n{json.dumps(context, indent=2, ensure_ascii=False, default=str)}\n\nParams:\n{json.dumps(params, indent=2, ensure_ascii=False, default=str)}"
        )

    def _extract_json_workflow(self, text: str) -> dict[str, Any] | None:
        raw = str(text or "").strip()
        if not raw:
            return None
        candidates = [raw]
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.S)
        if match:
            candidates.insert(0, match.group(1))
        brace = raw.find("{")
        end = raw.rfind("}")
        if brace >= 0 and end > brace:
            candidates.append(raw[brace:end + 1])
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                if isinstance(data, dict) and data.get("steps"):
                    return data
            except Exception:
                continue
        return None

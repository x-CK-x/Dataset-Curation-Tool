from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool import __version__
from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.workflow_automation_service import WorkflowAutomationService


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_release_version_is_5_8_2() -> None:
    assert __version__ == "5.8.48"


def test_workflow_service_creates_valid_branch_safe_template(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    AppSettings(global_dataset_root=str(tmp_path / "global")).save(paths.settings)
    svc = WorkflowAutomationService(paths)
    workflow = svc.create_from_request({
        "name": "Character LoRA automation",
        "goal": "Prepare a character LoRA branch with identity crops and export.",
        "template_key": "character_lora_auto_prep",
        "source_dataset_id": 123,
        "branch_name": "char_lora_branch",
        "target_model": "sdxl",
        "adapter_type": "lora",
        "dataset_goal": "character",
    })
    assert workflow["id"]
    assert workflow["branch_name"] == "char_lora_branch"
    assert any(step["type"] == "character_reference_rank" for step in workflow["steps"])
    assert any(step["type"] == "create_augmentation_variants" and step["requires_approval"] for step in workflow["steps"])
    validation = svc.validate_workflow(workflow)
    assert validation["ok"] is True
    assert svc.get_workflow(workflow["id"])["name"] == "Character LoRA automation"


def test_workflow_dry_run_records_manifest_without_context_side_effects(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    svc = WorkflowAutomationService(paths)
    workflow = svc.create_from_request({"name": "Dry run only", "template_key": "branch_quality_export_only", "branch_name": "ready_branch"})

    class Context:
        pass

    holder = {"context": Context()}
    svc._get_context = lambda: holder["context"]
    result = svc.dry_run(workflow["id"], {"dry_run": True})
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["results"]
    assert Path(result["manifest_path"]).exists()
    assert all(row["result"].get("dry_run") for row in result["results"] if row["status"] == "ok")


def test_workflow_api_and_frontend_are_wired(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    Database(paths.database)
    AppSettings(global_dataset_root=str(tmp_path / "global")).save(paths.settings)
    app = create_app(paths)
    client = TestClient(app)

    catalog = client.get("/api/workflows/catalog")
    assert catalog.status_code == 200
    assert any(step["type"] == "build_model_prompt" for step in catalog.json()["step_catalog"])

    created = client.post("/api/workflows", json={
        "name": "API workflow",
        "goal": "Prepare a style LoRA dataset.",
        "template_key": "style_lora_auto_prep",
        "branch_name": "style_branch",
        "dataset_goal": "style",
    })
    assert created.status_code == 200, created.text
    workflow = created.json()
    assert workflow["branch_name"] == "style_branch"

    dry = client.post(f"/api/workflows/{workflow['id']}/dry-run", json={"dry_run": True})
    assert dry.status_code == 200, dry.text
    assert dry.json()["dry_run"] is True

    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Automation Workflows" in text
    assert "/api/workflows/plan" in text
    assert "Queue Workflow Run" in text

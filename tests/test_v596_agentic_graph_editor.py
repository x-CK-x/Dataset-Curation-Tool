from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool import __version__
from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.graph_editor_service import GraphEditorService


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_release_version_is_5_8_3() -> None:
    assert __version__ == "5.8.48"


def test_graph_editor_creates_valid_graph_and_converts_to_workflow(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    svc = GraphEditorService(paths)
    graph = svc.create_from_template({
        "name": "Character LoRA graph",
        "template_key": "character_lora_auto_prep",
        "branch_name": "char_branch",
        "target_model": "sdxl",
        "adapter_type": "lora",
        "dataset_goal": "character",
    })
    assert graph["id"].startswith("graph_")
    assert graph["nodes"]
    assert graph["edges"]
    assert "graph LR" in graph["mermaid"]

    workflow = svc.to_workflow(graph)
    assert workflow["source_graph_id"] == graph["id"]
    assert workflow["branch_name"] == "char_branch"
    assert any(step["type"] == "character_reference_rank" for step in workflow["steps"])
    assert any(step["type"] == "create_augmentation_variants" and step["requires_approval"] for step in workflow["steps"])
    validation = svc.validate_graph(graph)
    assert validation["ok"] is True
    assert validation["workflow_step_count"] == len(workflow["steps"])


def test_graph_editor_manual_graph_preserves_topological_order(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    svc = GraphEditorService(paths)
    graph = svc.save_graph({
        "name": "Manual graph",
        "nodes": [
            {"id": "a", "kind": "create_branch", "label": "Branch", "x": 10, "y": 20, "config": {"branch_name": "manual"}},
            {"id": "b", "kind": "build_label_rules", "label": "Rules", "x": 270, "y": 20, "config": {}},
            {"id": "c", "kind": "evaluate_branch", "label": "Evaluate", "x": 530, "y": 20, "config": {}},
        ],
        "edges": [{"id": "e1", "from": "a", "to": "b"}, {"id": "e2", "from": "b", "to": "c"}],
    })
    workflow = svc.to_workflow(graph)
    assert [step["id"] for step in workflow["steps"]] == ["a", "b", "c"]
    assert [step["type"] for step in workflow["steps"]] == ["create_branch", "build_label_rules", "evaluate_branch"]


def test_graph_editor_api_and_frontend_are_wired(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    Database(paths.database)
    AppSettings(global_dataset_root=str(tmp_path / "global")).save(paths.settings)
    app = create_app(paths)
    client = TestClient(app)

    catalog = client.get("/api/graph-editor/catalog")
    assert catalog.status_code == 200
    assert any(node["kind"] == "download" for node in catalog.json()["node_palette"])

    compat_catalog = client.get("/api/graphs/catalog")
    assert compat_catalog.status_code == 200
    assert compat_catalog.json()["execution_backend"] == "automation_workflows"
    assert any(node["kind"] == "download" for node in compat_catalog.json()["node_catalog"])

    created = client.post("/api/graph-editor", json={
        "name": "API graph",
        "template_key": "branch_quality_export_only",
        "branch_name": "ready_branch",
    })
    assert created.status_code == 200, created.text
    graph = created.json()
    assert graph["branch_name"] == "ready_branch"

    workflow_preview = client.post(f"/api/graph-editor/{graph['id']}/to-workflow")
    assert workflow_preview.status_code == 200, workflow_preview.text
    assert workflow_preview.json()["workflow"]["steps"]

    dry = client.post(f"/api/graph-editor/{graph['id']}/dry-run", json={"dry_run": True})
    assert dry.status_code == 200, dry.text
    assert dry.json()["ok"] is True

    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Agentic Graph Editor" in text
    assert "/api/graph-editor/plan" in text
    assert "agenticGraphEditorView" in text

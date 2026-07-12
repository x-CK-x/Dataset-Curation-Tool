from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.attention_visualization_service import AttentionVisualizationService
from data_curation_tool.services.graph_editor_service import GraphEditorService
from data_curation_tool.services.startup_progress_service import StartupProgressService


def test_version_v5813():
    assert __version__ == "5.8.48"


def test_startup_progress_resume_supports_migration_phase():
    svc = StartupProgressService()
    svc.start("initial")
    svc.fail("cancelled", "cancelled")
    svc.resume("manual migration resumed", phase="startup_migration")
    svc.update(0.42, "copying migrated assets", phase="startup_migration")
    snap = svc.snapshot()
    assert snap["status"] == "running"
    assert snap["phase"] == "startup_migration"
    assert snap["progress"] == 0.42
    assert snap["eta_seconds"] is not None


def test_attention_visualization_capabilities_and_plan(tmp_path: Path):
    paths = AppPaths(root=tmp_path, runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs", database=tmp_path / "runtime" / "app.db", settings=tmp_path / "runtime" / "settings.json", thumbnails=tmp_path / "runtime" / "thumbnails", presets=tmp_path / "runtime" / "presets", downloads=tmp_path / "runtime" / "downloads", exports=tmp_path / "runtime" / "exports")
    paths.outputs.mkdir(parents=True, exist_ok=True)
    svc = AttentionVisualizationService(paths)
    caps = svc.capabilities()
    keys = {row["key"] for row in caps["methods"]}
    assert {"classifier_gradcam", "diffusion_unet_cross_attention", "tsne_embedding_map", "hydra_cam_attention"}.issubset(keys)
    plan = svc.plan({"method": "diffusion_unet_cross_attention", "tag": "blue eyes", "media_ids": [1]})
    assert plan["ok"] is True
    assert any(step["id"] == "capture_cross_attention" for step in plan["steps"])


def test_graph_editor_normalizes_standalone_contract_and_simulates(tmp_path: Path):
    paths = AppPaths(root=tmp_path, runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs", database=tmp_path / "runtime" / "app.db", settings=tmp_path / "runtime" / "settings.json", thumbnails=tmp_path / "runtime" / "thumbnails", presets=tmp_path / "runtime" / "presets", downloads=tmp_path / "runtime" / "downloads", exports=tmp_path / "runtime" / "exports")
    paths.runtime.mkdir(parents=True, exist_ok=True)
    svc = GraphEditorService(paths)
    graph = svc.save_graph({
        "id": "standalone_contract",
        "name": "Standalone compatibility",
        "nodes": [
            {"id": "text", "type": "TEXT_INPUT", "title": "Prompt", "x": 1, "y": 2, "text": "prepare dataset"},
            {"id": "bundle", "type": "BUNDLE", "x": 300, "y": 2, "limits": {"maxItems": 4, "maxChars": 1000, "policy": "drop_oldest"}},
            {"id": "out", "type": "OUTPUT", "x": 600, "y": 2},
        ],
        "edges": [{"from": "text", "to": "bundle", "label": "context"}, {"from": "bundle", "to": "out"}],
    })
    by_id = {n["id"]: n for n in graph["nodes"]}
    assert by_id["text"]["kind"] == "text_input"
    assert by_id["bundle"]["kind"] == "bundle_context"
    assert by_id["text"]["config"]["text"] == "prepare dataset"
    result = svc.simulate("standalone_contract", {"stop_on_approval_gate": False})
    assert result["status"] == "completed"
    assert len(result["trace"]) == 3


def test_frontend_contains_live_startup_attention_and_graph_simulation_hooks():
    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function updateStartupProgressDom" in text
    assert "Attention Visualizer" in text
    assert "/api/attention-visualization/run" in text
    assert "/simulate" in text
    assert "/api/graph-editor/events" in text
    assert "/api/graph-editor/execute-session" in text
    assert "/api/graph-editor/execute-node" in text
    assert "data-startup-progress-circle" in text


def test_migration_router_attaches_startup_progress_to_manual_migration():
    text = Path("data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    assert "startup_progress.attach_job" in text
    assert "Manual migration queued; startup maintenance will resume" in text
    assert "manual_migration" in text
    assert "submit_with_job_id" in text

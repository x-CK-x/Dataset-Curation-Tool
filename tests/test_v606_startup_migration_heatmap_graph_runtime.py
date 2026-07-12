from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from data_curation_tool import __version__
from data_curation_tool.services.attention_visualization_service import AttentionVisualizationService
from data_curation_tool.services.graph_editor_service import GraphEditorService
from data_curation_tool.services.startup_progress_service import StartupProgressService


class _Media:
    def __init__(self, path: str):
        self.path = path


class _MediaService:
    def __init__(self, path: Path):
        self.path = path

    def get(self, media_id: int):
        return _Media(str(self.path))


def _paths(tmp_path: Path):
    outputs = tmp_path / "outputs"
    runtime = tmp_path / "runtime"
    models = tmp_path / "models"
    for p in (outputs, runtime, models):
        p.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(outputs=outputs, runtime=runtime, models=models, root=tmp_path)


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"


def test_startup_progress_can_attach_manual_migration_job():
    svc = StartupProgressService()
    svc.start("Manual migration queued", phase="migration", job_type="asset_migration", trigger="manual_migration")
    svc.attach_job(123, "asset_migration", trigger="manual_migration", message="Migration job #123 queued")
    svc.update(0.42, "Copying migrated assets", phase="migration", job_id=123, job_type="asset_migration")
    snap = svc.snapshot()
    assert snap["status"] == "running"
    assert snap["phase"] == "migration"
    assert snap["job_id"] == 123
    assert snap["job_type"] == "asset_migration"
    assert snap["trigger"] == "manual_migration"
    assert snap["percent"] == 42.0
    assert any("Migration job" in step["message"] for step in snap["steps"])


def test_attention_visualization_writes_overlay_and_urls(tmp_path: Path):
    image_path = tmp_path / "image.png"
    Image.new("RGB", (96, 80), (32, 48, 96)).save(image_path)
    service = AttentionVisualizationService(_paths(tmp_path), _MediaService(image_path), None)
    result = service.run({"method": "classifier_gradcam", "tag": "blue eyes", "media_ids": [1]}, progress=None)
    assert result["ok"] is True
    assert result["overlay_path"]
    assert Path(result["overlay_path"]).exists()
    assert result["overlay_url"].startswith("/api/attention-visualization/artifact/")
    assert service.artifact_path(Path(result["overlay_path"]).name).exists()
    supports = service.capabilities()["supports"]
    assert "gradcam" in supports
    assert "diffusion_unet_cross_attention" in supports
    assert "tsne_embedding_projection" in supports


def test_graph_runtime_session_executes_bundle_and_output(tmp_path: Path):
    service = GraphEditorService(_paths(tmp_path))
    graph = {
        "id": "g1",
        "name": "runtime smoke",
        "nodes": [
            {"id": "text", "kind": "text_input", "label": "Prompt", "config": {"text": "curate this dataset"}, "x": 0, "y": 0},
            {"id": "bundle", "kind": "bundle_context", "label": "Bundle", "config": {"max_items": 4, "policy": "truncate_text"}, "x": 260, "y": 0},
            {"id": "out", "kind": "output_artifact", "label": "Output", "config": {}, "x": 520, "y": 0},
        ],
        "edges": [
            {"id": "e1", "from": "text", "to": "bundle", "label": "text"},
            {"id": "e2", "from": "bundle", "to": "out", "label": "result"},
        ],
    }
    result = service.execute_session(graph, {"dry_run": True})
    assert result["status"] == "completed"
    assert result["node_results"]["text"]["status"] == "completed"
    assert result["artifacts"]["bundle"]["kind"] == "bundle"
    assert result["output"]["kind"] == "output"
    catalog = service.catalog()
    assert "node_runtime_outputs" in catalog["runtime_capabilities"]
    assert "graph_session_execution" in catalog["graph_feature_contract"]["ported_features"]

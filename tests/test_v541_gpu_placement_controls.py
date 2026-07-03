from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_model_resource_and_placement_plan_endpoints(tmp_path: Path):
    client = _client(tmp_path)

    status = client.get("/api/models/resource-status")
    assert status.status_code == 200
    payload = status.json()
    assert "devices" in payload
    assert "loaded_models" in payload
    assert "loading_reservations" in payload

    plan = client.post(
        "/api/models/placement/plan",
        json={
            "model_name": "dataset-assistant",
            "device": "cpu",
            "device_ids": [],
            "sharding_strategy": "none",
            "max_memory": {},
            "torch_dtype": "auto",
            "quantization": "none",
            "runtime_engine": "transformers",
            "tensor_parallel_size": 1,
            "options": {},
        },
    )
    assert plan.status_code == 200
    plan_payload = plan.json()
    assert plan_payload["model_name"] == "dataset-assistant"
    assert plan_payload["can_load"] is True
    assert plan_payload["errors"] == []
    assert "estimated_vram_gb" in plan_payload

    client.close()


def test_unload_endpoint_is_noop_when_nothing_loaded(tmp_path: Path):
    client = _client(tmp_path)
    response = client.post("/api/models/unload", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["unloaded"] == []
    assert payload["job_id"] is None
    client.close()


def test_frontend_exposes_gpu_placement_and_unload_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    styles = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")

    assert "modelResourcePanel" in app_js
    assert "modelLoadControls" in app_js
    assert "/api/models/placement/plan" in app_js
    assert "/api/models/resource-status" in app_js
    assert "Check VRAM / Placement" in app_js
    assert "gpu-pick-row" in app_js
    assert "state.modelPlacementPlans[m.name] = plan" in app_js
    assert "queueModelLoad(m, placementControls" in app_js
    assert "Unload queued as job" in app_js

    assert ".resource-panel" in styles
    assert ".device-grid" in styles
    assert ".model-placement-controls" in styles
    assert ".gpu-pick-row" in styles

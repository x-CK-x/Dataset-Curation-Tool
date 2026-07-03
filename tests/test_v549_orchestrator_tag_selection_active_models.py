from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_orchestrator_plan_recommends_model_gpu_placement_without_queueing(tmp_path: Path):
    client = _client(tmp_path)
    response = client.post(
        "/api/models/orchestrator/plan",
        json={
            "orchestrator_model_name": "dataset-assistant",
            "target_model_names": ["redrocket-jtp-3"],
            "tasks": ["tag"],
            "media_ids": [1, 2],
            "require_user_approval": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["orchestrator_model_name"] == "dataset-assistant"
    assert payload["user_approval_required"] is True
    assert payload["message"].lower().startswith("review")
    rec = payload["recommendations"][0]
    assert rec["model_name"] == "redrocket-jtp-3"
    assert "placement" in rec
    assert "placement_request" in rec
    assert rec["queue_supported"] is True


def test_orchestrator_queue_requires_explicit_user_approval(tmp_path: Path):
    client = _client(tmp_path)
    run = {"model_name": "redrocket-jtp-3", "task": "tag", "media_ids": [], "device": "cpu"}
    rejected = client.post(
        "/api/models/orchestrator/queue-runs",
        json={"orchestrator_model_name": "dataset-assistant", "user_approved": False, "runs": [run]},
    )
    assert rejected.status_code == 400
    assert "approval" in rejected.json()["detail"].lower()

    accepted = client.post(
        "/api/models/orchestrator/queue-runs",
        json={"orchestrator_model_name": "dataset-assistant", "user_approved": True, "runs": [run]},
    )
    assert accepted.status_code == 200
    assert accepted.json()["count"] == 1
    assert accepted.json()["queued"][0]["model_name"] == "redrocket-jtp-3"


def test_frontend_orchestrator_tag_selection_and_active_model_affordances_present():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")

    assert "function sortedTagSelectionModels" in app_js
    assert "modelOptionNode" in app_js
    assert "Models are sorted: local VLMs, local LLMs" in app_js
    assert "Hover an option to see its category" in app_js
    assert "primeModelLifecycleForSelection(selectedModel())" in app_js
    assert "refreshModelStatuses(false).then(updateLiveStatusDom)" in app_js
    assert "refreshEditorSelectedTagDom" in app_js
    assert "result?.selected_tags || []" in app_js
    assert "orchestratorPlannerCard('assistant tab')" in app_js
    assert "/api/models/orchestrator/queue-runs" in app_js
    assert "sortedModelsForModelsTab" in app_js
    assert "active-model-card" in app_js
    assert ".model-category-select option.model-option-vlm" in css
    assert ".active-model-chip" in css
    assert ".orchestrator-rec" in css

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def test_assistant_config_endpoint_and_orchestration_templates_use_selected_model(tmp_path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    with TestClient(create_app(paths)) as client:
        initial = client.get("/api/models/assistant-config").json()
        assert initial["assistant_model_name"] == "dataset-assistant"
        assert any(row["name"] == "gemma-4-e4b-it" for row in initial["available_models"])

        updated = client.put(
            "/api/models/assistant-config",
            json={"assistant_model_name": "gemma-4-e4b-it", "orchestrator_model_name": "gemma-4-e4b-it"},
        ).json()
        assert updated["assistant_model_name"] == "gemma-4-e4b-it"
        assert updated["orchestrator_model_name"] == "gemma-4-e4b-it"

        templates = client.get("/api/orchestration/templates").json()
        vlm_template = next(t for t in templates if t["key"] == "vlm-review-selected")
        assert vlm_template["request"]["steps"][0]["model_name"] == "gemma-4-e4b-it"


def test_assistant_config_rejects_non_assistant_models(tmp_path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    with TestClient(create_app(paths)) as client:
        response = client.put("/api/models/assistant-config", json={"assistant_model_name": "rule-based-filename"})
        assert response.status_code == 400
        assert "not an assistant" in response.text


def test_frontend_assistant_control_and_load_unload_buttons_exist():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Assistant / Orchestrator Model Control" in app_js
    assert "/api/models/assistant-config" in app_js
    assert "Set Selected as Both Defaults" in app_js
    assert "Load Selected Assistant Model" in app_js
    assert "Unload Selected Model" in app_js
    assert "assistantCapableModelFilter" in app_js


def test_backend_assistant_model_resolution_uses_explicit_builtin_and_orchestrator_default(tmp_path):
    app = create_app(AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs"))
    models = app.state.context.models
    app.state.context.settings.assistant_model_name = "gemma-4-e4b-it"
    app.state.context.settings.orchestrator_model_name = "gemma-4-e4b-it"
    assert models.resolve_assistant_model_name("", purpose="assistant") == "gemma-4-e4b-it"
    assert models.resolve_assistant_model_name("dataset-assistant", purpose="assistant") == "dataset-assistant"
    assert models.resolve_assistant_model_name("dataset-assistant", purpose="orchestrator") == "gemma-4-e4b-it"

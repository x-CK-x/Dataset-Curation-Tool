from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_settings_have_assistant_thinking_defaults():
    s = AppSettings()
    assert s.assistant_thinking_mode in {"off", "fast", "balanced", "deep"}
    assert s.assistant_reasoning_effort in {"none", "low", "medium", "high", "max"}
    assert s.assistant_show_visible_plan is True
    assert s.assistant_planning_passes >= 0


def test_chat_returns_visible_plan_when_reasoning_enabled(tmp_path: Path):
    client = _client(tmp_path)
    response = client.post(
        "/api/models/chat",
        json={
            "model_name": "dataset-assistant",
            "prompt": "Help me plan how to inspect tags for this dataset.",
            "options": {
                "chat_assistant": True,
                "assistant_reasoning": True,
                "thinking_mode": "balanced",
                "reasoning_effort": "medium",
                "show_visible_plan": True,
                "planning_passes": 1,
                "plan_max_new_tokens": 384,
                "min_chat_max_new_tokens": 512,
            },
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["visible_plan"]
    assert payload["reasoning"]["enabled"] is True
    assert payload["reasoning"]["hidden_chain_of_thought_exposed"] is False
    assert payload["history"][-1]["response"]["visible_plan"]
    client.close()


def test_frontend_has_visible_planning_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "assistantReasoningControls" in app_js
    assert "Think longer / visible plan controls" in app_js
    assert "visiblePlanPanel" in app_js
    assert "reasoningOptionsFromControls" in app_js
    assert "Assistant Thinking / Visible Planning Defaults" in app_js
    assert "visible-plan-panel" in css

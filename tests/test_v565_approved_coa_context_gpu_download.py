from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import ModelChatRequest


def _app_client(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    return app, TestClient(app)


def test_conversation_coa_is_parsed_and_run_from_assistant_message(tmp_path: Path):
    app, client = _app_client(tmp_path)
    ctx = app.state.context
    req = ModelChatRequest(model_name="dataset-assistant", prompt="create a tool plan", options={"chat_assistant": True})
    conv_id = ctx.models._ensure_conversation(req, {})
    assistant_id = ctx.models._append_chat_message(
        conv_id,
        "assistant",
        "COA 1:\n```python\nprint('approved-coa-ran')\n```",
        "dataset-assistant",
        {},
        {},
    )
    parsed = client.post("/api/agent-tools/conversation-coas", json={"conversation_id": conv_id, "message_id": assistant_id})
    assert parsed.status_code == 200, parsed.text
    assert parsed.json()["count"] == 1
    assert parsed.json()["options"][0]["tool_calls"][0]["tool"] == "run_python_script"

    queued = client.post(
        "/api/agent-tools/run-conversation-coa",
        json={
            "conversation_id": conv_id,
            "message_id": assistant_id,
            "coa_index": 0,
            "user_approved": True,
            "enable_for_this_run": True,
            "model_name": "dataset-assistant",
            "relay_result": False,
        },
    )
    assert queued.status_code == 200, queued.text
    job = client.get(f"/api/jobs/{queued.json()['job_id']}").json()
    assert job["status"] == "completed", job
    assert "approved-coa-ran" in job["result"]["plan_result"]["results"][0]["result"]["stdout"]
    client.close()


def test_chat_returns_context_budget_and_can_force_compact_memory(tmp_path: Path):
    _app, client = _app_client(tmp_path)
    response = client.post(
        "/api/models/chat",
        json={
            "model_name": "dataset-assistant",
            "prompt": "summarize this " + ("large context " * 500),
            "options": {"chat_assistant": True, "context_length": 1024, "force_memory_condense": True, "show_visible_plan": False},
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["context_budget"]["context_limit_tokens"] == 1024
    assert payload["context_budget"]["tokens_used_estimate"] > 0
    assert payload["context_budget"]["percent_used"] >= 0
    client.close()


def test_agent_status_reports_detected_tool_binaries(tmp_path: Path):
    _app, client = _app_client(tmp_path)
    payload = client.get("/api/agent-tools/status").json()
    assert "tool_binaries" in payload
    assert "python" in payload["tool_binaries"]
    assert payload["tool_definitions"]
    client.close()


def test_frontend_has_hardwired_coa_context_download_gpu_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "/api/agent-tools/conversation-coas" in app_js
    assert "/api/agent-tools/run-conversation-coa" in app_js
    assert "Approve + Run" in app_js
    assert "contextBudgetPanel" in app_js
    assert "tokens used" in app_js
    assert "modelDownloadQueueSummaryPanel" in app_js
    assert "GB left" in app_js
    assert "physical total" in app_js
    assert "Refresh Filtered Model List" in app_js

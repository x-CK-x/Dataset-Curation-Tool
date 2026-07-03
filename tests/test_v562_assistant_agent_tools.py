from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.agent_tools_service import AgentToolsService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_agent_tool_definitions_and_status(tmp_path: Path):
    client = _client(tmp_path)
    status = client.get("/api/agent-tools/status")
    assert status.status_code == 200
    payload = status.json()
    assert payload["require_user_approval"] is True
    assert payload["sandbox_mode"] in {"workspace", "local", "docker"}
    definitions = client.get("/api/agent-tools/definitions").json()["tools"]
    names = {row["name"] for row in definitions}
    assert {"run_shell_command", "run_python_script", "read_file", "open_browser"}.issubset(names)
    client.close()


def test_approved_python_tool_call_runs_as_job(tmp_path: Path):
    client = _client(tmp_path)
    workspace = client.get("/api/agent-tools/status").json()["workspace"]
    response = client.post(
        "/api/agent-tools/execute-tool-call",
        json={
            "tool_call": {"tool": "run_python_script", "arguments": {"script": "print('tool-ok')", "cwd": workspace, "timeout_seconds": 20}},
            "user_approved": True,
        },
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "completed"
    assert job["result"]["ok"] is True
    assert "tool-ok" in job["result"]["stdout"]
    relay = client.post("/api/agent-tools/relay-result", json={"job_id": job_id, "model_name": "dataset-assistant", "surface": "pytest"})
    assert relay.status_code == 200
    assert "response" in relay.json()
    client.close()


def test_unapproved_command_fails_and_risk_parse_present(tmp_path: Path):
    client = _client(tmp_path)
    workspace = client.get("/api/agent-tools/status").json()["workspace"]
    response = client.post("/api/agent-tools/command", json={"command": "echo nope", "cwd": workspace, "user_approved": False})
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "failed"
    assert "approval" in job["error"].lower()
    risk = client.post("/api/agent-tools/risk", json={"command": "rm -rf /", "shell": "bash"}).json()
    assert risk["risk"] == "high"
    parsed = client.post("/api/agent-tools/parse-tool-calls", json={"text": '{"tool_calls":[{"tool":"list_path","arguments":{"path":"."}}]}'}).json()
    assert parsed["tool_calls"][0]["tool"] == "list_path"
    client.close()


def test_frontend_assistant_surfaces_have_agent_tools_panel():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Agent Tools" in app_js
    assert "agentToolsInlinePanel" in app_js
    assert "Generate Tool Plan From This Context" in app_js
    assert "/api/agent-tools/plan" in app_js
    assert "tag-selection-${title}" in app_js
    assert "Code Assistant" in app_js


def test_plan_json_extraction_and_tool_schema_names():
    text = '```json\n{"summary":"demo","steps":[{"tool":"run_shell_command","arguments":{"command":"echo ok"}}]}\n```'
    plan = AgentToolsService._extract_json_plan(text)
    assert plan and plan["summary"] == "demo"

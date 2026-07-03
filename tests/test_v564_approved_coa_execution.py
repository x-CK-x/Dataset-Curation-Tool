from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.config import AppSettings
from data_curation_tool.services.agent_tools_service import AgentToolsService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_settings_expose_coa_execution_toggle():
    s = AppSettings()
    assert s.agent_tools_enable_approved_coa_execution is True
    assert s.agent_tools_auto_relay_after_execution is True


def test_parse_practical_coa_formats(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    service = AgentToolsService(paths, AppSettings(), None)
    parsed = service.parse_tool_calls("""
COA:
```powershell
Get-ChildItem -Force
```
```python
print('hello')
```
""")
    assert [row["tool"] for row in parsed] == ["run_shell_command", "run_python_script"]
    assert parsed[0]["arguments"]["shell"] == "powershell"
    assert "Get-ChildItem" in parsed[0]["arguments"]["command"]
    assert "print" in parsed[1]["arguments"]["script"]


def test_run_plan_default_enabled_and_override_still_allowed(tmp_path: Path):
    client = _client(tmp_path)
    plan = [{"tool": "run_python_script", "arguments": {"script": "print('coa-ok')"}}]
    blocked = client.post("/api/agent-tools/run-plan", json={"plan": plan, "user_approved": False})
    assert blocked.status_code == 200
    blocked_job = client.get(f"/api/jobs/{blocked.json()['job_id']}").json()
    assert blocked_job["status"] == "failed"
    assert "User approval is required" in blocked_job["error"]

    allowed = client.post("/api/agent-tools/run-plan", json={"plan": plan, "user_approved": True, "enable_for_this_run": True})
    assert allowed.status_code == 200
    job = client.get(f"/api/jobs/{allowed.json()['job_id']}").json()
    assert job["status"] == "completed", job
    assert job["result"]["ok"] is True
    assert "coa-ok" in job["result"]["results"][0]["result"]["stdout"]
    client.close()


def test_agent_tool_chat_contract_reaches_dataset_assistant(tmp_path: Path):
    client = _client(tmp_path)
    response = client.post("/api/models/chat", json={"model_name": "dataset-assistant", "prompt": "Use PowerShell to list files.", "options": {"chat_assistant": True, "agent_tools_chat": True, "show_visible_plan": False}})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["agent_tools_chat"] is True
    last_user = [m for m in payload["history"] if m["role"] == "user"][-1]
    assert last_user["context"]["agent_tools_available"] is True
    assert "tool-call" in last_user["context"]["agent_tools_execution_contract"]
    client.close()


def test_frontend_has_approved_coa_execution_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "enable approved COA execution" in app_js
    assert "Approve + Run COA Plan" in app_js
    assert "/api/agent-tools/run-plan" in app_js
    assert "agent_tools_chat" in app_js

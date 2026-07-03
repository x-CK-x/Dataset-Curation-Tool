from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.agent_tools_service import AgentToolsService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_agent_plan_accepts_media_context_fields_and_debug_log(tmp_path: Path):
    client = _client(tmp_path)
    response = client.post(
        "/api/agent-tools/plan",
        json={
            "goal": "List the workspace using a safe shell command.",
            "model_name": "dataset-assistant",
            "surface": "pytest-tag-editor",
            "media_ids": [123],
            "external_paths": [str(tmp_path / "image.png")],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["debug_log_path"].endswith(".jsonl")
    assert "tool_definitions" in payload
    logs = client.get("/api/agent-tools/debug-logs").json()
    assert logs["count"] >= 1
    client.close()


def test_python_tool_call_supports_requirements_metadata_and_debug_log(tmp_path: Path):
    client = _client(tmp_path)
    workspace = client.get("/api/agent-tools/status").json()["workspace"]
    response = client.post(
        "/api/agent-tools/python",
        json={
            "script": "# requirements: \nprint('debug-python-ok')",
            "requirements": [],
            "create_venv": False,
            "cwd": workspace,
            "timeout_seconds": 30,
            "user_approved": True,
        },
    )
    assert response.status_code == 200, response.text
    job_id = response.json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "completed", job
    assert job["result"]["ok"] is True
    assert "debug-python-ok" in job["result"]["stdout"]
    assert Path(job["result"]["debug_log_path"]).is_file()
    client.close()


def test_parse_python_requirements_from_model_output(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    service = AgentToolsService(paths, AppSettings(), None)
    parsed = service.parse_tool_calls(
        """
```requirements
requests
pillow
```
```python
import requests
print('ok')
```
"""
    )
    py = [row for row in parsed if row["tool"] == "run_python_script"][0]
    assert py["arguments"]["requirements"] == ["requests", "pillow"]
    assert py["arguments"]["create_venv"] is True


def test_frontend_exposes_debug_logs_smoke_test_and_approve_run():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "agentDebugLogsPanel" in app_js
    assert "/api/agent-tools/smoke-test" in app_js
    assert "Approve + Run COA Plan" in app_js
    assert "media_ids: ids" in app_js
    assert "external_paths" in app_js


def test_gpu_service_tracks_identity_fields_in_source():
    src = Path("data_curation_tool/services/gpu_service.py").read_text(encoding="utf-8")
    assert "uuid,pci.bus_id" in src
    assert "cuda_visible_devices" in src
    assert "Windows Task Manager GPU numbers can differ" in src

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.code_assistant_service import CodeAssistantService


class _DummyModelService:
    def chat(self, request):
        return {
            "conversation_id": request.conversation_id or 1,
            "model_name": request.model_name,
            "response": "```diff\ndiff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('old')\n+print('new')\n```",
            "history": [{"id": 1, "role": "assistant", "content": "ok"}],
        }


def test_named_api_token_profiles_resolve_and_mask():
    settings = AppSettings(
        huggingface_token="hf_legacy",
        openrouter_token="sk-or-legacy",
        api_token_profiles={
            "huggingface": [{"name": "main", "token": "hf_main", "default": True}, {"name": "backup", "token": "hf_backup"}],
            "openrouter": [{"name": "kimi", "token": "sk_kimi"}],
            "runpod": [{"name": "serverless", "token": "rp_123", "default": True}],
            "vastai": [{"name": "vast", "token": "vast_123"}],
            "lambda_labs": [{"name": "lambda", "token": "lambda_123"}],
        },
    )
    assert settings.resolve_api_token("huggingface") == "hf_main"
    assert settings.resolve_api_token("huggingface", "backup") == "hf_backup"
    assert settings.resolve_api_token("openrouter", "kimi") == "sk_kimi"
    assert settings.resolve_api_token("runpod") == "rp_123"
    safe = settings.to_safe_dict(include_secrets=False)
    assert safe["api_token_profiles"]["openrouter"][0]["token"] == "********"
    assert safe["api_token_profiles"]["huggingface"][1]["token"] == "********"


def test_code_assistant_scans_reads_and_extracts_patch(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("print('old')\n", encoding="utf-8")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
    service = CodeAssistantService(_DummyModelService())
    scan = service.scan(str(root))
    assert scan["file_count"] == 2
    assert any(row["path"] == "app.py" for row in scan["files"])
    assert not any("node_modules" in row["path"] for row in scan["files"])
    read = service.read_files(str(root), ["app.py"])
    assert "print('old')" in read["files"][0]["content"]
    chat = service.chat(root_path=str(root), prompt="fix app.py", model_name="dataset-assistant", files=["app.py"])
    diff = service.extract_first_unified_diff(chat["response"])
    assert "diff --git" in diff
    check = service.apply_patch(str(root), diff, check_only=True)
    assert check["message"] == "Patch check passed"


def test_v556_api_endpoints_and_frontend_controls_present(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    client = TestClient(create_app(paths))
    assert client.post("/api/jobs/pause", json={"download_only": True, "include_running": True}).status_code == 200
    assert client.post("/api/jobs/resume", json={"download_only": True}).status_code == 200
    assert client.post("/api/code/scan", json={"root_path": str(tmp_path)}).status_code == 200
    assert client.post("/api/cloud/runpod/run", json={"endpoint_id":"ep","input":{}}).status_code == 500
    assert client.post("/api/cloud/vastai/request", json={"path":"/instances/"}).status_code == 500
    assert client.post("/api/cloud/lambda/request", json={"path":"/instances"}).status_code == 500
    client.close()
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Code Assistant" in app_js
    assert "Pause Downloads" in app_js
    assert "Resume Downloads" in app_js
    assert "conversationHistoryPanel" in app_js
    assert "model_download_serial_queue" in app_js
    assert "OpenRouterVideoGenerationRequest" in Path("data_curation_tool/routers/models.py").read_text(encoding="utf-8")

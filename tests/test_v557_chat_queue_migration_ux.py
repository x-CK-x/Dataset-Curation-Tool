from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def test_chat_conversation_state_save_and_memory_summary(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    client = TestClient(create_app(paths))
    first = client.post("/api/models/chat", json={"model_name": "dataset-assistant", "prompt": "remember that this image uses a custom tag policy", "use_selected_media": False}).json()
    conv_id = first["conversation_id"]
    saved = client.put(f"/api/models/chat/conversations/{conv_id}/state", json={"scope": "tag-editor", "media_ids": [123], "active_tags": ["tag_a", "tag_b"], "title": "saved tag state"}).json()
    assert saved["state"]["media_ids"] == [123]
    assert saved["conversation"]["title"] == "saved tag state"
    # Force enough turns to trigger deterministic cached memory condensation.
    for i in range(20):
        client.post("/api/models/chat", json={"model_name": "dataset-assistant", "prompt": f"turn {i} with details", "conversation_id": conv_id, "use_selected_media": False})
    convo = client.get(f"/api/models/chat/conversations/{conv_id}").json()
    assert "memory_summary" in convo["state"]
    assert "Condensed conversation memory" in convo["state"]["memory_summary"]


def test_frontend_chat_thread_and_explicit_model_download_queue_ui_present():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "chat-thread" in app_js
    assert "✎ Edit message" in app_js
    assert "Save edit and continue from here" in app_js
    assert "Save current state" in app_js
    assert "modelDownloadModeControl" in app_js
    assert "Serial queue: one model file transfer at a time" in app_js
    assert "Download mode:" in app_js
    assert "chat-bubble.user" in css
    assert "memory-summary" in css


def test_migrated_qwen_vlm_with_valid_payload_is_downloaded_not_repair(tmp_path: Path):
    root = tmp_path
    group = root / "models" / "hf" / "Qwen--Qwen3-VL-2B-Instruct"
    group.mkdir(parents=True)
    (group / "config.json").write_text("{}", encoding="utf-8")
    (group / "model.safetensors").write_bytes(b"valid weights")
    paths = AppPaths.create(runtime=root / "runtime", models=root / "models", outputs=root / "outputs")
    client = TestClient(create_app(paths))
    rows = client.get("/api/models").json()
    row = next(item for item in rows if item["name"] == "qwen3-vl-2b")
    assert row["downloaded"] is True
    assert row["download_state"] == "downloaded"
    assert row["download_integrity"]["issues"] == []
    assert "downloaded" in row["status_badges"]

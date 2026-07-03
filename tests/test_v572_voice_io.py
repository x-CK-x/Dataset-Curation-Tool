from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(tmp_path / "runtime", tmp_path / "models", tmp_path / "outputs")
    app = create_app(paths)
    return TestClient(app)


def test_voice_catalog_contains_stt_and_tts_rows(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    payload = client.get("/api/voice/models").json()
    stt = {row["name"] for row in payload["stt"]}
    tts = {row["name"] for row in payload["tts"]}
    assert "whisper-large-v3-turbo" in stt
    assert "parakeet-tdt-0-6b-v3" in stt
    assert "kokoro-82m" in tts
    assert "coqui-xtts-v2" in tts


def test_voice_settings_can_be_saved_and_status_reflects_them(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    values = {
        "voice_stt_enabled": True,
        "voice_tts_enabled": True,
        "voice_stt_model_name": "distil-whisper-large-v3",
        "voice_tts_model_name": "mms-tts-eng",
        "voice_stt_load_policy": "on_demand",
        "voice_tts_load_policy": "on_demand",
        "voice_browser_input_device_id": "mic-test",
        "voice_browser_output_device_id": "speaker-test",
    }
    assert client.put("/api/settings", json={"values": values}).status_code == 200
    status = client.get("/api/voice/status").json()
    assert status["settings"]["stt_model_name"] == "distil-whisper-large-v3"
    assert status["settings"]["tts_model_name"] == "mms-tts-eng"
    assert status["settings"]["input_device_id"] == "mic-test"
    assert status["settings"]["output_device_id"] == "speaker-test"


def test_voice_transcribe_saves_upload_and_uses_fake_adapter(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    app = client.app
    c = app.state.context

    class FakeAdapter:
        def is_available(self):
            return True
        def load(self, device="auto", **kwargs):
            self.loaded = True
        def unload(self):
            self.loaded = False
        def transcribe(self, audio_path, language=None, **kwargs):
            assert Path(audio_path).exists()
            return {"text": "hello from voice", "raw": {"language": language}}

    c.registry.get_record("whisper-large-v3-turbo").adapter = FakeAdapter()
    response = client.post(
        "/api/voice/transcribe",
        files={"file": ("sample.webm", b"not-real-audio", "audio/webm")},
        data={"model_name": "whisper-large-v3-turbo", "language": "en"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["text"] == "hello from voice"
    assert data["model_name"] == "whisper-large-v3-turbo"
    assert Path(data["audio_path"]).exists()

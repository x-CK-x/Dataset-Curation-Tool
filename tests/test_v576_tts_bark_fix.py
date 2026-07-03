from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(tmp_path / "runtime", tmp_path / "models", tmp_path / "outputs")
    app = create_app(paths)
    return TestClient(app)


def test_tts_synthesize_accepts_numpy_audio_without_truth_value_error(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    app = client.app
    c = app.state.context
    client.put("/api/settings", json={"values": {"voice_tts_enabled": True, "voice_tts_model_name": "bark-small-tts"}})

    class FakeTTSAdapter:
        def is_available(self):
            return True
        def load(self, device="auto", **kwargs):
            self.loaded = True
        def unload(self):
            self.loaded = False
        def synthesize(self, text, output_path, voice=None, language=None, **kwargs):
            # This mirrors HF Bark/Transformers pipelines that return numpy arrays.
            audio = np.linspace(-0.1, 0.1, 800, dtype=np.float32)
            # Exercise the shared HF adapter bug path: no boolean evaluation of arrays.
            from data_curation_tool.models.adapters import HFTextToSpeechAdapter
            return HFTextToSpeechAdapter._write_wav(output_path, audio, 24000)

    c.registry.get_record("bark-small-tts").adapter = FakeTTSAdapter()
    response = client.post("/api/voice/synthesize", json={"text": "hello", "model_name": "bark-small-tts"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["ok"] is True
    assert data["url"].endswith(".wav")
    assert Path(data["path"]).exists()


def test_tts_synthesize_reports_tts_not_stt_enable_state(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    # STT enabled alone should not satisfy TTS.
    client.put("/api/settings", json={"values": {"voice_stt_enabled": True, "voice_tts_enabled": False}})
    response = client.post("/api/voice/synthesize", json={"text": "hello", "model_name": "bark-small-tts"})
    assert response.status_code == 500
    assert "Text-to-speech is disabled" in response.text


def test_frontend_tts_settings_buttons_enable_and_save_tts_before_testing():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "currentVoiceSettings" in src
    assert "Enable + Load TTS Now" in src
    assert "Enable + Test TTS Output" in src
    assert "voice_tts_enabled: true" in src

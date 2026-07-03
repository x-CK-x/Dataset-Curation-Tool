from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.models.adapters import HFTextToSpeechAdapter
from data_curation_tool.paths import AppPaths


class _ArrayPipeline:
    def __call__(self, text: str, **kwargs):
        assert text
        # Bark-like output: NumPy array under the audio key.  This previously
        # crashed when code used result.get("audio") or result.get("waveform").
        return {"audio": np.array([0.0, 0.25, -0.25], dtype=np.float32), "sampling_rate": 16000}


class _ListPipeline:
    def __call__(self, text: str, **kwargs):
        return [
            {"waveform": np.array([0.1, 0.2], dtype=np.float32), "sampling_rate": 22050},
            {"waveform": np.array([0.3], dtype=np.float32), "sampling_rate": 22050},
        ]


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(tmp_path / "runtime", tmp_path / "models", tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_tts_adapter_handles_numpy_audio_without_ambiguous_truth_value(tmp_path: Path):
    adapter = HFTextToSpeechAdapter("dummy")
    adapter.pipeline = _ArrayPipeline()
    adapter.backend = "transformers"
    out = tmp_path / "array.wav"
    result = adapter.synthesize("hello", out)
    assert result["ok"] is True
    assert result["sampling_rate"] == 16000
    assert result["samples"] == 3
    with wave.open(str(out), "rb") as wav:
        assert wav.getframerate() == 16000
        assert wav.getnchannels() == 1
        assert wav.getnframes() == 3


def test_tts_adapter_handles_list_pipeline_outputs(tmp_path: Path):
    adapter = HFTextToSpeechAdapter("dummy")
    adapter.pipeline = _ListPipeline()
    adapter.backend = "transformers"
    out = tmp_path / "list.wav"
    result = adapter.synthesize("hello", out)
    assert result["ok"] is True
    assert result["sampling_rate"] == 22050
    assert result["samples"] == 3


def test_voice_synthesize_endpoint_returns_structured_tts_error(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    response = client.post("/api/voice/synthesize", json={"text": "hello", "model_name": "missing-model"})
    assert response.status_code == 500
    assert "Text-to-speech synthesis failed" in response.text


def test_frontend_tts_controls_are_separate_from_stt_controls():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "voice_tts_enabled: voiceTtsEnabled.checked" in src
    assert "voice_stt_enabled: voiceSttEnabled.checked" in src
    assert "Enable + Load TTS Now" in src
    assert "Enable + Test TTS Output" in src
    assert "loaded_voice_models?.tts" in src

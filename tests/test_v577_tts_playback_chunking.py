from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from data_curation_tool.models.adapters import HFTextToSpeechAdapter
from data_curation_tool.services.voice_service import VoiceService


def _write_short_wav(path: Path, sr: int = 16000, frames: int = 16) -> None:
    arr = (np.ones(frames, dtype=np.int16) * 1024).tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(arr)


class _Settings:
    voice_tts_enabled = True
    voice_stt_enabled = True
    voice_tts_model_name = "fake-tts"
    voice_stt_model_name = "fake-stt"
    voice_tts_load_policy = "always"
    voice_tts_chunk_long_text = True
    voice_tts_max_chunk_chars = 80
    voice_tts_chunk_pause_ms = 0


class _Adapter:
    def __init__(self):
        self.calls: list[str] = []
    def synthesize(self, text, output_path, **kwargs):
        self.calls.append(str(text))
        _write_short_wav(Path(output_path))
        return {"ok": True, "chars": len(str(text))}


class _Registry:
    def __init__(self, adapter):
        self.adapter = adapter
        self._loaded = {"fake-tts": adapter}
    def is_loaded(self, name):
        return name in self._loaded


def test_voice_service_chunks_and_stitches_long_tts_text(tmp_path: Path):
    adapter = _Adapter()
    service = VoiceService(paths=None, settings=_Settings(), registry=_Registry(adapter))
    service.outputs_dir = tmp_path / "tts"
    service.logs_dir = tmp_path / "logs"
    text = "This is a sentence. " * 20
    result = service.synthesize({"text": text, "model_name": "fake-tts", "options": {"max_chunk_chars": 80}})
    assert result["ok"] is True
    assert result["chunked"] is True
    assert result["chunk_count"] > 1
    assert len(adapter.calls) == result["chunk_count"]
    assert Path(result["path"]).exists()
    assert Path(result["path"]).stat().st_size > 44


def test_tts_nested_audio_dict_output_is_normalized(tmp_path: Path):
    audio = np.asarray([0.0, 0.5, -0.5], dtype=np.float32)
    payload = {"audio": {"array": audio, "sampling_rate": 22050}}
    arr, sr, keys = HFTextToSpeechAdapter._extract_pipeline_audio(payload)
    assert sr == 22050
    assert np.asarray(arr).shape == audio.shape
    assert "audio" in keys


def test_frontend_exposes_voice_toggles_and_last_audio_player():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "voiceSurfaceToggles" in src
    assert "lastVoiceOutputPanel" in src
    assert "chunk/stitch long TTS text" in src
    assert "Speech WAV was generated, but the browser did not autoplay it" in src

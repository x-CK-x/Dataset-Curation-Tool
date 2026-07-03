from __future__ import annotations

from pathlib import Path

import numpy as np

from data_curation_tool.models.adapters import HFTextToSpeechAdapter
from data_curation_tool.services.voice_service import VoiceService


class _Settings:
    voice_tts_enabled = False
    voice_stt_enabled = False
    voice_tts_model_name = "bark-small-tts"
    voice_stt_model_name = "whisper-large-v3-turbo"


def test_tts_pipeline_audio_array_does_not_use_ambiguous_truth_value(tmp_path: Path):
    adapter = HFTextToSpeechAdapter("suno/bark-small")
    adapter.backend = "transformers"
    adapter.model_id = "suno/bark-small"

    class FakePipeline:
        def __call__(self, text, **kwargs):
            assert "voice_preset" in kwargs or kwargs == {}
            return {"audio": np.asarray([0.0, 0.25, -0.25], dtype=np.float32), "sampling_rate": 16000}

    adapter.pipeline = FakePipeline()
    out = tmp_path / "tts.wav"
    result = adapter.synthesize("hello", out, voice="v2/en_speaker_6")
    assert result["ok"] is True
    assert result["sampling_rate"] == 16000
    assert out.exists()
    assert out.stat().st_size > 44


def test_voice_synthesize_can_use_loaded_tts_even_if_settings_snapshot_is_stale_disabled(tmp_path: Path):
    service = VoiceService(paths=None, settings=_Settings(), registry=None)
    service.loaded_voice_models["tts"] = "bark-small-tts"
    # A manually loaded TTS model should bypass a stale disabled settings value.
    service._ensure_enabled("tts", {"model_name": "bark-small-tts"})


def test_frontend_tts_test_saves_and_forces_tts_enabled():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Enable + Test TTS Output" in src
    assert "force_enabled: true" in src
    assert "voice_tts_enabled: true" in src
    assert "loaded_voice_models?.tts" in src

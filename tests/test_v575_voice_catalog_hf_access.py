from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(tmp_path / "runtime", tmp_path / "models", tmp_path / "outputs")
    app = create_app(paths)
    return TestClient(app)


def test_expanded_voice_catalog_keeps_existing_and_adds_missing_bark_qwen_chatterbox(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    payload = client.get("/api/voice/models").json()
    stt = {row["name"]: row for row in payload["stt"]}
    tts = {row["name"]: row for row in payload["tts"]}

    # Existing rows are retained.
    assert "whisper-large-v3-turbo" in stt
    assert "parakeet-tdt-0-6b-v3" in stt
    assert "kokoro-82m" in tts
    assert "coqui-xtts-v2" in tts

    # Newly exposed rows cover families that were previously absent/partial.
    for key in ["qwen3-asr-0-6b-hf", "qwen3-asr-1-7b-hf", "distil-whisper-large-v3-5", "moonshine-tiny"]:
        assert key in stt
    for key in ["bark-large-tts", "chatterbox-tts", "qwen3-tts-1-7b-customvoice", "vibevoice-1-5b", "dia-1-6b", "higgs-tts-3-4b"]:
        assert key in tts


def test_hf_access_metadata_is_exposed_in_models_api_and_voice_catalog(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _client(tmp_path)
    models = {row["name"]: row for row in client.get("/api/models").json()}
    assert models["pyannote-speaker-diarization-3-1"]["requires_hf_token"] is True
    assert models["pyannote-speaker-diarization-3-1"]["hf_access"] == "gated"
    assert "hf token/terms required" in models["pyannote-speaker-diarization-3-1"]["status_badges"]
    assert models["mistral-voxtral-tts-4b"]["hf_access"] == "hf_token_recommended"
    assert "hf token recommended" in models["mistral-voxtral-tts-4b"]["status_badges"]

    voice = client.get("/api/voice/models").json()
    tts = {row["name"]: row for row in voice["tts"]}
    assert tts["mistral-voxtral-tts-4b"]["hf_access"] == "hf_token_recommended"
    assert tts["mistral-voxtral-tts-4b"]["requires_hf_token"] is False


def test_frontend_renders_hf_token_status_chips_and_voice_option_labels():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function modelHFAccessLabel" in src
    assert "HF TOKEN / TERMS REQUIRED" in src
    assert "HF TOKEN RECOMMENDED" in src
    assert "hf-token-required-chip" in src
    assert "modelHFAccessTitle" in src

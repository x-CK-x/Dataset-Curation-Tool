# v5.75 — Expanded Voice Model Catalog + Hugging Face Access Indicators

This release expands the Speech-to-Text and Text-to-Speech model catalog while retaining every model row that already existed.

## Why this exists

Some voice models on Hugging Face are public and download normally. Others require a Hugging Face token, accepted model terms, a recent Transformers build, or a model-specific runtime package. Earlier versions did not make that clear enough in the Models tab, so a model could look like a normal downloadable row even when access/runtime constraints were the real issue.

## What changed

### Expanded STT catalog

Added catalog rows for additional ASR/STT families including:

- OpenAI Whisper tiny/base/small/medium/large-v2/large-v3/large-v3-turbo.
- Faster-Whisper Large v3.
- Distil-Whisper large-v2, large-v3, and large-v3.5.
- Qwen3-ASR 0.6B and 1.7B HF rows.
- NVIDIA Parakeet, Canary, Canary-Qwen, and Nemotron streaming speech rows.
- Microsoft VibeVoice-ASR.
- CohereLabs Transcribe 03-2026.
- Mistral Voxtral Mini Realtime ASR.
- BosonAI Higgs Audio STT.
- Useful Sensors Moonshine tiny/base.
- FunAudioLLM SenseVoiceSmall.
- Meta MMS / Wav2Vec2-BERT rows.

### Expanded TTS catalog

Added catalog rows for additional TTS families including:

- Bark large in addition to Bark small.
- More Meta MMS language rows.
- Parler-TTS mini, mini v1.1, and large.
- ResembleAI Chatterbox, Chatterbox Turbo, and Chatterbox Turbo ONNX.
- Qwen3-TTS base/custom-voice/voice-design rows.
- Microsoft VibeVoice realtime and 1.5B rows.
- Nari Labs Dia and Dia2 rows.
- CosyVoice2 and Fun-CosyVoice3 rows.
- Spark-TTS.
- BosonAI Higgs TTS rows.
- Orpheus, Sesame CSM, Zyphra ZONOS2, IndexTTS-2, OpenBMB VoxCPM2, and Mistral Voxtral TTS rows.

### HF token / gated access visibility

Model rows can now expose:

```json
{
  "hf_access": "public | hf_token_recommended | gated | restricted",
  "requires_hf_token": true,
  "hf_access_note": "...",
  "license_note": "..."
}
```

The Models tab now shows visible chips:

- `HF TOKEN / TERMS REQUIRED`
- `HF TOKEN RECOMMENDED`

The same metadata is also included in model dropdown hover text and the Voice STT/TTS model selectors.

### Gated/terms-aware examples

The pyannote diarization rows are marked as requiring a Hugging Face token and terms acceptance. These rows are deliberately categorized as `audio_diarization`, not plain STT, so they appear in the Models tab for audio/video curation but do not pollute the push-to-record transcription selector.

## Caveats

Adding a catalog row does not guarantee that every model family has a production-grade adapter yet. Some modern TTS/STT models require project-specific packages or very new Transformers support. The row makes the model visible, downloadable, and status-trackable; runtime adapters can be hardened incrementally as those libraries stabilize.

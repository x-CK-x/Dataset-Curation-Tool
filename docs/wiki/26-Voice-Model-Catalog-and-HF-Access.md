# Voice Model Catalog and Hugging Face Access

<!-- DCT_VISUAL_START -->
![Voice model catalog and Hugging Face access visual guide](assets/images/voice_model_catalog_hf_access.png)
<!-- DCT_VISUAL_END -->


The application includes voice model rows in the same Models tab used for VLMs, LLMs, taggers, captioners, classifiers, detection models, and segmentation models.

## Model categories

- **Speech-to-text** rows are used by push-to-record voice input.
- **Text-to-speech** rows are used by optional assistant reply playback.
- **Audio diarization** rows are for future audio/video-with-audio curation workflows, such as speaker segmentation. They appear in the Models tab but are not treated as normal STT models.

## Access chips

Some Hugging Face repositories require more than an anonymous download.

The Models tab can show:

- `HF TOKEN / TERMS REQUIRED` — create/use a Hugging Face token and accept any model terms on the repository page before downloading.
- `HF TOKEN RECOMMENDED` — public row, but a token can prevent rate-limit/access surprises or may be required by that provider/repo packaging.

## Practical guidance

1. Add your Hugging Face token in **Settings → API Tokens**.
2. Open **Models** and filter to `stt`, `tts`, or `audio_diarization`.
3. Check the model chip/hover text before downloading.
4. Download models in serial queue mode for large voice checkpoints.
5. Use `on_demand` STT/TTS load policy when VRAM is constrained.
6. Use `always loaded` only for small models or when you want faster voice interaction.

## Runtime notes

Some rows are catalog visibility rows for rapidly changing model families. They may require optional runtime packages such as NeMo, FunASR, Parler-TTS, Chatterbox, CosyVoice, Dia, or project-specific Transformers support.

For voice cloning or reference-voice TTS, only use voices where you have explicit consent and rights.

# 58 — Preprocessing, Scroll Stability, Graph Editor, and LingBot World Models

v5.8.28 focuses on preserving the working model-loader state while correcting the next set of blocking workflow issues.

## Legacy Thouph tagger preprocessing

The three Thouph rows now use model-specific preprocessing:

- EVA02 ViT-Large 448: exact 448×448 resize and CLIP mean/std.
- EVA02-CLIP ViT-Large 7704: 224×224 CLIP preprocessing, with the tall/wide aspect-ratio branch from the batched helper.
- Experimental EfficientNetV2-M 8035: PyTorch path uses the Thouph 512-area aspect-preserving thumbnail and ImageNet mean/std; ONNX fallback still honors fixed graph input dimensions.

## Models-tab refresh behavior

Automatic polling is now a soft render. When the user is scrolling, editing, or using a dropdown, the refresh is deferred. The Models tab also uses explicit scroll keys for the model catalog/download sections.

## Tag Editor prediction sorting

Added sorting by:

- average prediction
- specific selected model prediction
- most models detecting a tag
- smallest standard deviation
- median prediction
- mode prediction

## Agentic Graph Editor

Local graph preset helpers were restored so the Agentic Graph Editor can render and preserve local graph snapshots/presets.

## Multimodal audio/voice/video scope

The Multimodal Dataset Builder now exposes explicit voice-profile consent/provenance state, audio-video sync annotations, audio/STT/TTS/voice-conversion task profiles, and a voice consent manifest export profile.

## LingBot-Video rows

The Models tab includes LingBot-Video Dense, MoE 30B-A3B, Qwen3.6 rewriter base, and rewriter LoRA rows. These are command/runtime rows, not still-image taggers. Use the LingBot command/run endpoints with a local LingBot repository path containing `scripts/inference.py`.

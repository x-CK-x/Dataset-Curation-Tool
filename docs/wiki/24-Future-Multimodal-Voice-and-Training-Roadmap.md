# Future Multimodal Voice and Training Roadmap

<!-- DCT_VISUAL_START -->
![Voice roadmap visual guide](assets/images/voice_roadmap_best_practices_faq_dev.png)
<!-- DCT_VISUAL_END -->


This page captures planned future objectives for the project. It is intentionally a roadmap and design target, not a promise that all items are production-ready in the current build.

## Core direction

The tool is intended to support dataset curation across these modalities:

- Images.
- Audio.
- Video.
- Video with synchronized audio.
- 3D models/assets.

Training features are currently preliminary. Their long-term value is in turning curated datasets into reproducible training runs with clear readiness checks, job logs, checkpoints, review queues, and exportable results.

## Immediate baseline already present

Current builds already include early groundwork:

- Image import, gallery review, tag editing, captions, metadata, and model-assisted curation.
- Video frame extraction and audio extraction in Media Tools.
- STT/TTS push-to-record and speak-output scaffolding.
- Model download/load/unload, GPU placement, CPU offload, and lifecycle status indicators.
- Assistant/orchestrator panels, human-approved COA execution, and job/debug logging.
- Preliminary 3D/pose/FlexAvatar/Blender bridge workflows.

## Future audio curation goals

Planned audio curation should include:

1. Import audio files and audio extracted from video.
2. Preserve provenance, metadata, and source links.
3. Generate transcripts with segment timestamps.
4. Add word-level timestamps where supported.
5. Add speaker diarization and speaker-turn labels when useful.
6. Add audio-event, music, SFX, environment, mood, language, and quality tags.
7. Support manual correction of transcripts, timestamps, speaker labels, and tags.
8. Export datasets for STT, TTS, voice conversion, audio classification, audio captioning, and multimodal training.

Candidate STT/alignment/diarization backends to evaluate later include Whisper/WhisperX-style transcription/alignment, pyannote-style diarization, and NVIDIA Parakeet/Canary-style ASR families. These should remain optional so the base install stays stable.

## Future video-with-audio curation goals

Video should eventually be treated as synchronized data streams:

- Frame/image stream.
- Audio stream.
- Transcript/subtitle stream.
- Scene/action/object annotations.
- Audio-event/music/SFX annotations.
- Metadata and generation/source metadata.

Planned labels should support:

- frame-level annotations;
- clip-level annotations;
- timestamp-level tags;
- transcript-linked tags;
- object/action/scene descriptions;
- audio-video alignment records.

## Ethical voice cloning and voice conversion

Voice cloning support should require explicit provenance and rights tracking. The app should not silently treat arbitrary audio as cloneable voice data.

Future voice-cloning/voice-conversion workflows should require a voice consent/provenance manifest before training or runtime voice selection. A starter JSON template is included at:

```text
docs/templates/voice_dataset_consent_manifest_template.json
```

The manifest should track:

- source speaker/voice profile;
- consent status;
- allowed and disallowed uses;
- license/rights holder notes;
- source audio paths;
- review status;
- training approval;
- compatible runtime TTS/voice-conversion backends;
- generated-output restrictions.

## Candidate voice backends to evaluate later

Candidate open-source backend families include:

- XTTS-style voice cloning / multilingual TTS.
- OpenVoice-style instant voice cloning / tone-color transfer.
- RVC-style retrieval-based voice conversion.
- F5-TTS/Kokoro/Bark/SpeechT5-style TTS output families.

These should be optional integrations. Each backend should have an installer, dependency isolation strategy, model download status, GPU/VRAM estimate, and clear license/usage notes.

## Future GUI tabs

Potential future tabs:

- **Audio Curation**: waveform viewer, transcript editor, speaker turns, audio tags, clip extraction.
- **Voice Dataset Builder**: consent manifest, source audio review, cleaning, segmentation, transcript validation, split creation.
- **Voice Library**: approved voices, compatible TTS backends, default runtime voice, license/consent status.
- **Voice Training**: training planner, config editor, GPU/VRAM estimate, job queue, checkpoint browser, evaluation.
- **Video Timeline**: frame/audio/transcript timeline, timestamp labels, clips, exports.
- **Multimodal Export**: image/audio/video/3D dataset packaging for target training frameworks.

## Training workflow principles

Training should remain human-auditable:

1. Run dataset readiness checks before training.
2. Show estimated VRAM, RAM, disk, runtime, and checkpoint requirements.
3. Keep all generated configs under a reproducible output folder.
4. Queue training as Jobs with pause/cancel/retry where supported.
5. Log stdout/stderr and structured status.
6. Save model cards or training reports after completion.
7. Keep evaluation separate from training so outputs can be reviewed before use.

## Integration policy

Heavy or fragile training/voice/video backends should not become mandatory base dependencies. Prefer:

- optional install scripts;
- isolated Conda envs or venvs;
- Docker where appropriate;
- explicit model download cards;
- clear license and consent warnings;
- human-approved execution through Jobs.

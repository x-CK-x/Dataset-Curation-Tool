# v5.73 Future Multimodal Voice / Audio / Video / 3D Training Roadmap

This release does **not** try to ship full voice cloning or audio/video training in one unstable step. It captures the requested long-term direction in the app and GitHub-wiki-ready documentation so future implementation work has a concrete target.

## Added

- New in-app tab: **Future Modalities**.
- New GitHub Wiki page: `docs/wiki/24-Future-Multimodal-Voice-and-Training-Roadmap.md`.
- New consent/provenance template: `docs/templates/voice_dataset_consent_manifest_template.json`.
- Wiki sidebar/home links for the new page.
- Version bumped to `5.73.0`.

## Roadmap scope captured

The project roadmap now explicitly covers:

- Image dataset curation.
- Audio dataset curation.
- Video dataset curation.
- Video with synchronized audio.
- 3D model/asset curation.
- Preliminary training workflows for future versions.
- Ethical voice cloning and voice-conversion workflows using documented consent/provenance.
- Optional integration of specialized open-source voice/TTS/voice-conversion backends.
- Future GUI tabs for voice dataset setup, training setup, voice library management, and multimodal export.

## Voice cloning guardrails

Future voice cloning support should require a manifest for each speaker/voice profile. The manifest should track:

- Speaker or voice-profile identifier.
- Consent status.
- Source audio origin.
- Rights/license notes.
- Allowed use cases.
- Disallowed use cases.
- Dataset paths.
- Model/checkpoint paths.
- Generated-output restrictions.
- Review/approval status.

The application should not silently treat arbitrary audio as cloneable voice data.

## Candidate backend families to evaluate later

These are roadmap candidates, not hard dependencies:

- STT/alignment/diarization: Whisper, WhisperX, pyannote-style diarization, NVIDIA Parakeet/Canary families.
- TTS/voice cloning: XTTS v2, OpenVoice, Kokoro, F5-TTS, Bark-style systems.
- Voice conversion: RVC-style retrieval-based voice conversion and related optional backends.
- Audio/video labeling: sound event classification, music/SFX tagging, action/scene detection, frame/audio timeline alignment.

All heavy backends should stay optional and isolated so the base app install remains stable.

## Training remains preliminary

Training tabs should mature gradually:

1. Dataset readiness checks.
2. Training planning with VRAM/storage estimates.
3. Human-approved job execution.
4. Checkpoints/logging/resume.
5. Evaluation and review queues.
6. Exportable reports.


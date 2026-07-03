# Voice Input and Speech Output

<!-- DCT_VISUAL_START -->
![Voice input and speech output visual guide](assets/images/voice_roadmap_best_practices_faq_dev.png)
<!-- DCT_VISUAL_END -->


Voice I/O lets you use your microphone as an editable message source for assistant chats and optionally play assistant replies as audio.

## First supported mode: push-to-record

This is the reliable mode currently implemented.

1. Go to **Settings → Voice Input / Speech Output**.
2. Enable speech-to-text.
3. Choose an STT model.
4. Choose the microphone device.
5. Open an assistant chat surface.
6. Click **Start Voice**.
7. Speak.
8. Click **Stop & Transcribe**.
9. Edit the generated text.
10. Click the normal Send button.

This keeps the user in control and avoids always-on microphone processing.

## STT model loading policy

Use **on demand** when VRAM is constrained. The app loads the STT model for transcription and then unloads it if it was not already loaded.

Use **always loaded** when you want faster transcription and have enough RAM/VRAM.

## Text-to-speech

Enable TTS when you want assistant replies spoken aloud.

You can either:

- click **Speak** under individual assistant messages; or
- enable **auto-speak assistant replies**.

Set the output device in Settings. Browser support depends on `setSinkId`; unsupported browsers will use the system default output device.

## Recommended starting models

Speech-to-text:

- Whisper Large v3 Turbo for general local transcription.
- Distil-Whisper Large v3 for a lighter/faster option.
- NVIDIA Parakeet / Canary if you install the optional NVIDIA NeMo stack.

Text-to-speech:

- Kokoro 82M for fast lightweight local output.
- Kokoro ONNX for low-overhead deployment.
- XTTS v2 when voice cloning/reference speakers are needed.

## Future live/wake-word mode

Wake-word or Siri-like operation would require a permanent capture loop and an always-running VAD/wake-word/STT stack. That is intentionally left for a later implementation after the push-to-record path is stable.


## Troubleshooting TTS

Use **Enable + Load TTS Now** when testing a speech model from Settings. This explicitly enables the TTS side, saves the selected TTS model/runtime settings, and loads the model. STT and TTS enable states are separate. Bark and other Hugging Face TTS pipelines can return NumPy arrays under `audio`/`waveform`; v5.76 handles those outputs directly and writes a WAV file for playback.

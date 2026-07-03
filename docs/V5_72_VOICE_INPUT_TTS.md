# v5.72 Voice Input and Speech Output

This build adds a first-pass, robust voice workflow for assistant chat surfaces.

## What is implemented now

- Push-to-record speech-to-text.
- User-controlled start/stop buttons in assistant chat composers.
- Editable transcription text before sending to the LLM/VLM.
- Optional text-to-speech playback for assistant responses.
- Browser microphone/speaker selection in Settings.
- STT/TTS model catalog rows in the normal Models tab.
- STT/TTS load policy controls:
  - `on_demand`: load only when used, then unload when possible.
  - `always`: preload/keep resident when possible.

## Why this approach first

Wake-word/live audio requires a permanently running capture loop and another always-on model. The first implementation avoids that risk and keeps VRAM under user control. It behaves like a keyboard replacement: record, transcribe, edit, send.

## Settings

Open **Settings → Voice Input / Speech Output**.

Important fields:

- Enable speech-to-text.
- STT model.
- STT policy: on-demand or always loaded.
- STT device/GPU IDs/dtype/quantization.
- Enable text-to-speech.
- TTS model.
- TTS policy: on-demand or always loaded.
- TTS voice/speaker.
- Auto-speak assistant replies.
- Microphone device.
- Speaker output device.

Browser device labels may appear blank until microphone permission has been granted. Use **Refresh Browser Audio Devices**.

## Model catalog rows

Speech-to-text rows include:

- Whisper Large v3 Turbo.
- Whisper Large v3.
- Distil-Whisper Large v3.
- NVIDIA Parakeet TDT 0.6B v3.
- NVIDIA Parakeet RNNT 1.1B.
- NVIDIA Canary 1B v2.

Text-to-speech rows include:

- Kokoro 82M.
- Kokoro ONNX.
- Coqui XTTS v2.
- Bark Small.
- SpeechT5.
- MMS English TTS.
- F5-TTS.

Some families need optional packages beyond the base install. The app imports those lazily so a missing TTS package does not break the whole application.

## Push-to-record workflow

1. Choose STT model/settings.
2. Open Tag Editor assistant, Assistant tab, Code Assistant, or another chat composer.
3. Click **Start Voice**.
4. Speak.
5. Click **Stop & Transcribe**.
6. Review/edit the generated text in the message box.
7. Click the normal Send button.

## TTS workflow

Enable TTS in Settings, choose a model, and either:

- click **Speak** under an assistant message; or
- enable **auto-speak assistant replies**.

The browser attempts to route playback to the configured output device using `HTMLMediaElement.setSinkId` when supported by the browser.

## Known caveats

- Wake-word mode is not implemented yet.
- Browser microphone access requires HTTPS or localhost permissions.
- Some TTS models require optional packages or reference speaker audio.
- NVIDIA NeMo ASR rows are cataloged and lazily attempted; install NeMo ASR extras when using those models.

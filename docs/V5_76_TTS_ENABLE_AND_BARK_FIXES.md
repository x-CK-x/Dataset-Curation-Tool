# v5.76 — TTS Enable-State and Bark/Transformers Audio Fixes

This release fixes the first practical text-to-speech playback issues reported after the expanded voice catalog work.

## Fixes

- Fixed the TTS enable-state workflow in Settings. Loading or testing a TTS model now explicitly enables and saves the TTS settings before the operation runs, so the app no longer behaves as if only STT was enabled.
- The TTS settings card now labels the buttons as **Enable + Load TTS Now** and **Enable + Test TTS Output** to make the state transition explicit.
- Fixed Hugging Face/Bark-style TTS outputs that return NumPy arrays. The old `audio or waveform` fallback could raise:

  ```text
  ValueError: The truth value of an array with more than one element is ambiguous.
  ```

- Added safer extraction of `audio`, `waveform`, `speech`, `wav`, or `array` fields from TTS pipeline outputs without boolean-evaluating arrays.
- Improved WAV writing for mono and common channel-first/channel-last audio array layouts.
- Reduced repeated non-fatal Bark/Transformers `max_new_tokens`/`max_length` warning spam during synthesis.
- Added structured STT/TTS error logs under:

  ```text
  runtime/voice/logs/
  ```

- Voice API synthesis/transcription errors now return structured HTTP errors instead of producing only a raw ASGI traceback.

## Practical note

For Bark and other Hugging Face TTS models, make sure the selected TTS model is downloaded and the voice runtime dependencies are installed. Use:

```text
install_voice_runtime.bat
```

or:

```text
install_voice_runtime.sh
```

if the base environment does not yet have the optional voice packages installed.

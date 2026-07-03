# v5.76 — TTS Enable-State + Bark Output Fixes

This patch fixes the first practical TTS playback issues found after adding the expanded voice catalog.

## Fixes

- The Settings tab **Enable + Load TTS Now** and **Enable + Test TTS Output** flows now save the TTS-enabled state before testing or returning to assistant chat surfaces.
- Assistant **Speak** uses an already-loaded TTS model if the frontend has a stale settings snapshot.
- Backend TTS enable checks now allow an explicitly loaded TTS model or a per-request enabled override, while still keeping disabled-by-default behavior for normal use.
- Hugging Face/Bark-style TTS pipeline outputs no longer crash on NumPy arrays with `ValueError: The truth value of an array with more than one element is ambiguous`.
- TTS pipeline output normalization now handles common audio keys, tuples, lists, Torch tensors, and sample-rate variants.
- Bark-style voice/speaker hints are attempted when supported, with a fallback to plain synthesis when a pipeline rejects voice-specific arguments.

## User workflow

1. Open **Settings → Voice Input / Speech Output**.
2. Select a TTS model such as **Bark Small TTS**.
3. Click **Enable + Load TTS Now** or **Enable + Test TTS Output**.
4. Return to an assistant chat and click **Speak** on an assistant response.

If a TTS model still fails, check the error text and `runtime/voice/logs/` debug file path returned by the backend.

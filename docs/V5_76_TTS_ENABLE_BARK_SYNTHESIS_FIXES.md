# v5.76 — TTS Enable-State and Bark/HF Synthesis Fixes

This patch fixes the first round of text-to-speech runtime issues found while testing Bark Small from the assistant/image-editor chat surface.

## Fixes

- The TTS adapter no longer uses boolean `or` selection on NumPy arrays returned by Hugging Face text-to-speech pipelines.
- Bark-style outputs such as `{ "audio": numpy.ndarray, "sampling_rate": ... }` are handled explicitly.
- Pipeline outputs using `waveform`, `speech`, `wav`, or `array` keys are also accepted.
- List outputs are concatenated into one WAV file.
- WAV writing now handles mono, channel-first, and channel-last audio shapes more safely.
- Voice API errors now return structured `HTTPException` details instead of leaking full ASGI stack traces to the browser.
- TTS enable/load/test actions are kept separate from STT enable/load/test state.
- Loading TTS from Settings explicitly enables and persists the TTS side.
- Testing TTS from Settings explicitly enables/persists the selected TTS settings before synthesis.
- The Speak helper now allows already-loaded TTS models to speak even if the stale frontend setting snapshot still says TTS is disabled.

## Notes

If Bark Small was downloaded with an older build, use **Queue Update** / **Re-download Update** if the model folder is missing support files. This patch fixes the runtime array handling error reported as:

```text
ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
```

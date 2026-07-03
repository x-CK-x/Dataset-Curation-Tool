# v5.77 TTS Playback and Long-Text Fixes

This build fixes the first practical text-to-speech playback issues reported after the voice model catalog expansion.

## Changes

- Added visible STT and TTS checkboxes in assistant chat surfaces so voice input/output can be toggled near the chat box instead of only in Settings.
- Added a persistent **Last speech output / playback** panel with an HTML audio player, **Play again**, and **Open/Download WAV** controls.
- Browser autoplay failures no longer look like nothing happened. If the browser refuses playback, the WAV stays visible and can be played manually.
- Added cache-busted audio URLs and no-store headers for generated WAV files.
- Added long-text TTS chunking and WAV stitching so Bark-like/local TTS models do not silently read only the first part of a long answer.
- Added TTS chunk controls to Settings:
  - chunk/stitch long TTS text
  - max characters per chunk
  - pause milliseconds between chunks
- Improved Hugging Face TTS output normalization for nested audio dictionaries such as `{audio: {array, sampling_rate}}`.

## Why this matters

Some TTS models have practical prompt/text limits and may stop early without throwing a clear exception. v5.77 treats long TTS as a sequence of smaller synthesis requests, then stitches the WAV chunks together into one file before handing it to the browser.

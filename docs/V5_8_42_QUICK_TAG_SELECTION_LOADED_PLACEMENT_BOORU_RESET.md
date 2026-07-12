# v5.8.42 — Quick Tag Selection, Loaded Placement, Booru Reset, and Thumbnail Reliability

This patch fixes the Quick Tag multi-select queue regression, preserves menu/queue scroll during live status updates, adds a use-loaded-placement mode for already-resident models, restores string-emitted tag application/score persistence, improves thumbnail prewarming throughput, and adds booru metadata tag reset actions for single media and selected batches.

## Key behavior

- Ctrl/Cmd-click, Shift-click, and Ctrl/Cmd+A selections in the Quick Tag model queue are persisted in `state.quickModelQueueSelection` and are used by Queue Download/Update, Queue Load, Queue Unload, and Queue Selected Models.
- The Quick Tag model queue panel preserves its internal scroll position while job status rows patch live.
- The model menu is patched from shared model lifecycle state, keeping the Models tab and Tag Editor controls synchronized without requiring inactive tab re-renders.
- `use_loaded_model_placement` allows inference to use the device/sharding residency of a model that is already loaded, instead of failing because a stale new CUDA selector points elsewhere.
- Bare-string tag outputs are now treated as score `1.0` thresholded labels, so they can be persisted and applied instead of being silently dropped.
- Booru tag reset reads `.download.json`, re-fetches the selected source post by ID, replaces tags from fresh metadata, updates the sidecar, and writes a persistent failure report for missing/unfetchable media.

## Validation

Validated with Python compilation, JavaScript syntax check, shell syntax checks, targeted regression tests, and ZIP integrity.

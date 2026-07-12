# v5.8.43 — Gallery Thumbnails, Quick Tag Selection, Booru Reset Jobs, and Integrity Classifiers

## Scope

This patch focuses on four reliability/performance issues:

1. Gallery thumbnails must not make the browser wait on large original images while thumbnails are still being generated.
2. The Quick Tag multi-model selector must allow real Ctrl/Cmd-click deselection and Shift-click range selection.
3. Reset-tags-from-booru must be a visible queued job with progress instead of appearing to do nothing during network fetches.
4. Nightshade / Glaze / poisoned-data integrity classifier registration and run controls should be available before the user supplies the final models.

## Thumbnail changes

- Added non-blocking thumbnail responses with a lightweight SVG placeholder.
- Added `/api/media/thumbnails/status` so the frontend can hydrate visible thumbnails as soon as worker output exists.
- Added optional OpenCV/CUDA resize path behind `DCT_THUMB_GPU=1` when OpenCV with CUDA support is installed.
- Gallery image tags now use `decoding="async"` and data attributes for live hydration.

## Quick Tag selector changes

- Added a DOM-selection path that no longer unions stale `state.quickModelQueueSelection` into every change event.
- Ctrl/Cmd-click can now deselect highlighted rows.
- Shift-click range selection remains supported.
- Queue buttons use the persisted selected list, not just the last clicked option.

## Booru reset changes

- Added `POST /api/media/reset-tags-from-booru/job`.
- The synchronous endpoint remains available for compatibility.
- The Tag Editor and Batch Tags reset buttons now queue a `booru_tag_reset` job, update the Jobs state immediately, and refresh affected media when the job completes.

## Integrity classifier changes

- Added `IntegrityClassifierService` and `/api/integrity-classifiers/*` endpoints.
- Added Models-tab registration controls for local EfficientNet/EfficientNetV2/ONNX/Torch/TensorFlow classifier profiles plus labels.
- Added Tag Editor and Batch Tags integrity-check cards.
- Results are stored as model prediction metadata and persisted to `runtime/integrity_checks/`.

## Notes

The integrity classifier path is intentionally isolated from the working tagger registry so adding custom Nightshade/Glaze classifiers cannot break the existing WD, PixAI, Thouph, Hydra, JTP, or other tagger loaders.

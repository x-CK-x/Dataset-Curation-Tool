# v5.8.40 — Gallery Thumbnails, Prediction Scores, Quick Tag, and Workflows

v5.8.40 focuses on the review loop after import and model inference.

## Gallery performance

- Thumbnail generation is scheduled through a bounded CPU worker pool.
- Imports queue thumbnail generation for newly registered media.
- The frontend can prewarm thumbnails for the current Gallery page.
- Media-page rendering continues to use batched metadata/tag/caption lookups from earlier releases.

## Prediction-score persistence

- Model prediction payloads continue to be stored in the predictions table.
- Per-tag scores are persisted in `tag_prediction_scores`.
- The Tag Editor shows a compact score table for the active media.
- Stored scores can be reviewed later without rerunning the same model.

## Quick Tag fixes

- The default threshold remains `0.70`.
- Blank/invalid/zero Quick Tag threshold values are repaired to `0.70`.
- Only threshold-passing tags are applied to media.
- Lower-scored candidates remain stored as prediction scores.
- The multi-model queue selector preserves scroll and selection during live refresh.
- CUDA ID and sharding controls are available in the Quick Tag section.
- Selected models can be queued for load, unload, or inference.

## Agentic workflow categories

Workflow templates now show colored category metadata in the selector and README cards. New certified dry-run templates cover:

- tag-based multi-model score review;
- caption-only image dataset prep;
- LTX/Wan multimodal caption/export planning;
- audio-video sync and caption QA.

These templates are local dry-run baselines. Adding real model calls, media processing, external tools, or trainer launches still requires the corresponding local components to be configured.

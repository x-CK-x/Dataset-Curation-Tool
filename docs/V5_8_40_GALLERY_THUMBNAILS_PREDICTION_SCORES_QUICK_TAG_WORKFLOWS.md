# v5.8.40 — Gallery Thumbnails, Prediction Scores, Quick Tag Controls, and Workflow Categories

## Scope

This patch focuses on user-visible responsiveness and correctness in the media review path:

- faster Gallery thumbnail availability;
- persisted per-media/model prediction-score review;
- Quick Tag threshold stability;
- threshold-correct tag application;
- GPU/sharding controls in the Quick Tag queue;
- load/unload queue buttons for selected Quick Tag models;
- selection/scroll stability for the Quick Tag multi-model menu;
- additional certified agentic graph templates with workflow-category coloring.

## Gallery and thumbnails

Thumbnail generation is now queued through a bounded CPU thread pool from `MediaService.schedule_thumbnail_prewarm(...)`. The Gallery page path schedules thumbnail work for visible rows, and import batch registration also queues thumbnails for newly imported media.

The frontend can also call:

```text
POST /api/media/thumbnails/prewarm
```

for the currently visible media IDs. This keeps heavy thumbnail work out of the main UI render path and lets machines with many CPU cores generate previews concurrently.

## Persisted model prediction scores

Model inference continues to store the complete prediction payload, and tag/class scores are persisted into `tag_prediction_scores` keyed by media, model, kind, and tag.

The Tag Editor now surfaces those stored scores in a compact table for the active media. The user can inspect model-relative score history later without rerunning the same models.

## Quick Tag threshold fix

Quick Tag now has an explicit frontend state value:

```text
quickTagThreshold = 0.70
```

Blank, invalid, zero, or NaN threshold values are repaired back to the default. The backend also computes an `effective_threshold` for model runs and treats Quick Tag blank/zero thresholds as `0.70` rather than `0.0`.

## Threshold-correct tag application

Inference candidate tags are filtered by score before committing tags to the image. Only tags with:

```text
score >= effective_threshold
```

are added to the tag list when `apply_tags` is enabled. Lower-scored candidates remain available as stored prediction scores, but they are not committed as active tags.

## Quick Tag GPU and queue controls

The Tag Editor Quick Tag card now includes CUDA ID checkboxes and a sharding selector. The selected placement is sent through load, unload, and inference queue requests.

Added controls:

```text
Queue Load Selected
Queue Unload Selected
Queue Selected Models
```

The existing single-model quick run still works, but the multi-model queue path now preserves dropdown selection and scroll state during live updates.

## Agentic workflow categories and new templates

Workflow templates now expose category metadata and color coding in both the workflow selector and the Agentic Workflow README cards.

New certified dry-run templates:

```text
advanced_tag_based_multi_model_score_review
advanced_caption_only_image_dataset_prep
advanced_ltx_wan_multimodal_caption_export
advanced_audio_video_sync_caption_review
```

Each template is designed to complete in local dry-run mode without requiring downloaded models, GPU inference, real media files, external tools, shell commands, or trainer installs.

## Files of interest

```text
data_curation_tool/services/media_service.py
data_curation_tool/services/dataset_service.py
data_curation_tool/services/model_service.py
data_curation_tool/routers/media.py
data_curation_tool/static/app.js
data_curation_tool/static/styles.css
data_curation_tool/services/graph_editor_service.py
docs/agentic_workflows/*.md
```

## Validation notes

This patch is validated through Python syntax checks, frontend JavaScript syntax checks, shell script syntax checks, focused regression tests, and ZIP integrity checks. Live Windows browser timing, real GPU inference, and large Gallery performance under the user's full local dataset must still be verified on the target workstation.

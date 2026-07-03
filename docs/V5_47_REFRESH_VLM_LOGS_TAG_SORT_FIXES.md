# v5.47 Refresh, VLM Input, Logs, and Tag Sort Fixes

## Fixed: Jobs / Models refresh disruption

The polling loop still refreshes job state and model lifecycle state, but it now avoids expensive full rebuilds while the user is interacting with dense tabs.

Key behavior:

- Jobs and Models both expose live-refresh toggles.
- Visible job progress/status/message cells update in place through `updateLiveStatusDom()`.
- Model lifecycle circles update in place where possible.
- The model list is periodically reconciled on model-related tabs so migrated/downloaded/loaded state appears without a hard page reload.
- Full rerenders are deferred briefly after interactions on Jobs, Models, Gallery, and Tag Editor.

## Fixed: slow gallery image selection

Gallery tile clicks no longer re-render the full gallery grid. Selection now updates only CSS state for the affected tiles and the selected-count display.

This prevents each click from rebuilding thumbnails and restarting tag-score hover lookups.

## Fixed: Hugging Face VLM `chat` + `images` input error

The HF VLM adapter now sends image objects embedded directly in the chat message content first, which matches the newer Transformers image-text chat pipeline behavior. It then falls back through older input formats for compatibility.

This addresses errors like:

```text
Invalid input: you passed `chat` and `images` as separate input
```

## Added: copy/download full logs and synchronous model errors

The Jobs tab has stronger full-detail controls:

- View full log
- Refresh this log
- Copy full details
- Download log file
- Copy row error when present

The Tag Editor's `LLM/VLM/Assistant Tag Selection for This Image` card also records direct `/api/models/select-tags` failures in a visible full-log panel with:

- Copy Error
- Download Error

The backend now returns a detailed tag-selection failure payload containing the selected model, media ids, operation, error message, and traceback. This is for local debugging when a failure occurs before a background job exists.

## Added: manual predicted-tag sorting controls

The Tag Editor now includes:

- Sort Predicted by Category
- Sort Predicted by Accuracy
- Sort All by Category

The predicted/scored sort buttons only move tags with stored model prediction scores. Tags with no prediction score are kept at the end in their current order because those may be manually curated or intentionally hand-ordered.

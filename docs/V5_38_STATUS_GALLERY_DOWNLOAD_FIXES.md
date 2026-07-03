# v5.38 status, gallery, scroll, and downloader stability fixes

This patch is intentionally additive and preserves the v5.37 model lifecycle status-circle work.

## Model load / inference UI refresh

- Model dropdown choices are now held in explicit frontend state rather than relying on DOM restoration after each 3-second status poll.
- Model selects managed by lifecycle cards are excluded from generic form persistence, preventing stale form memory from changing the selected model after a render.
- Queueing model download, load, and run actions now refresh both model lifecycle status and the Jobs list immediately, so the user does not need to reload the browser page to see that work was queued.
- `/api/models/status` reconciles active lifecycle rows with durable Jobs rows. If a worker completed but the visible lifecycle row was stale, polling status now corrects it from the Jobs table.

## Gallery render-loop and scroll stability

- Gallery model-score requests are cached by media id plus tag signature.
- A score response only triggers a render if the underlying cached score changed.
- Completed/failed model jobs invalidate the score cache so new predictions can still appear.
- Full-page renders snapshot and restore the window scroll position and nested scroll containers. This prevents the global viewer and tab scrollbars from snapping back to the top during polling.

## Downloader parallel dedupe and defaults

- Parallel preset workers only run when the explicit parallel-presets checkbox/request flag is enabled.
- Cross-preset dedupe now uses post identity keys, hashes, and file identifiers in addition to URL strings. This prevents duplicate downloads when the same source post appears through multiple expanded category/tag presets with slightly different file URLs.
- Download All Posts is enabled by default.
- Default safety timing is now: API/page delay 7 seconds, file delay 7 seconds, timeout 60 seconds, retries 3, retry backoff 2 seconds.

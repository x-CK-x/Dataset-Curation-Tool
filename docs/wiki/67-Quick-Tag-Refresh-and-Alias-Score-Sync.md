# 67 — Quick Tag Refresh and Alias/Score Sync

v5.8.37 fixes a Tag Editor issue where a quick tag/rating inference job could complete successfully, but the ordered tag list and prediction score rows did not refresh until the user left and re-entered the tab.

## What changed

- The quick model dropdown updates its lifecycle circles immediately when the selected model changes.
- Completed model-inference jobs now refresh affected media rows and prediction scores without requiring a tab switch.
- Stale tag drafts are cleared for affected media before the UI redraws.
- Completed jobs now return full candidate/applied tag maps and candidate score rows.
- The frontend uses those maps as an optimistic fallback if the media refresh is delayed.
- Applied model tags are normalized through the selected tag profile, alias table, implication table, tag text mode, and ordering strategy.

## Expected behavior

After running a quick tag/rating model with **Apply emitted labels as tags** enabled:

1. The model's inference circle should move while the job runs.
2. The job should complete in Jobs.
3. The Tag Editor should update the ordered tag chips on the same tab.
4. Prediction values should be available in hover panels and in the latest quick-run preview.
5. The user should not need to switch tabs and back to see the update.

## Normalization contract

The model adapter may emit native tags, classes, aliases, or model-specific labels. The application now routes those labels through the active tag dictionary profile before they are saved as training-data tags.

The raw model output is still preserved in the prediction payload for debugging and audit purposes.

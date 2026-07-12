# v5.8.37 — Quick Tag Refresh and Alias/Score Sync

This release fixes the Tag Editor quick-tag feedback loop and tightens the model-output normalization path used when taggers apply labels directly to media.

## User-facing fixes

### Quick Tag dropdown lifecycle refresh

Selecting a model in the **Quick Tag / Rating Model for This Image** dropdown now updates the progress-circle strip immediately. The selected model's download/load/inference/training circles are swapped in place without requiring a tab switch or a full page rebuild.

The dropdown still keeps the v5.8.36 readiness cues:

- loaded models are highlighted as ready;
- downloaded but unloaded models are visually distinct;
- not-downloaded rows remain dimmed.

### Completed inference refreshes the Tag Editor

When a quick tag/rating job reaches a terminal state, the frontend now:

1. fetches the completed job;
2. determines the affected media IDs;
3. clears stale tag-editor drafts for those media rows;
4. refreshes the affected media rows from the backend;
5. requests prediction-score rows for the current tags and model-output candidates;
6. hard-refreshes the active media review tab while preserving scroll position.

This is intended to fix the failure mode where the job completed and reported applied tags, but the Tag Editor did not show the new tags or prediction values until the user switched tabs.

### Optimistic fallback for slow media refresh

The backend model-inference result now includes:

```json
{
  "candidate_tags_by_media": {},
  "candidate_scores_by_media": {},
  "applied_tags_by_media": {}
}
```

If the media endpoint is slow to return, the frontend can patch the current media item's tag list from the completed job payload before the normal `/api/media/{id}` refresh returns.

### Visible latest prediction preview

The quick model card now shows a compact preview of the last model-inference job for the current media item, including candidate tags and available score values. The full canonical tag list remains in the ordered tag editor.

## Backend normalization change

Applied model tags now continue through the selected tag profile with alias and implication handling enabled by default. The quick-tag request sends:

```json
{
  "tag_profile": "<active profile>",
  "tag_text_mode": "underscores|spaces",
  "order_strategy": "<active ordering strategy>",
  "apply_model_tag_aliases": true,
  "apply_model_tag_implications": true
}
```

The backend still preserves the raw model output for auditability, but the saved/applied tags use the normalized active-profile form. This keeps model outputs from PixAI, WD, Thouph, Hydra, JTP, and similar taggers aligned with the user's selected tag dictionary preset whenever a known alias or implication path exists.

## Files changed

See `docs/V5_8_37_FILE_CHANGES.json` for the full inventory.

# Best Practices and Workflows

<!-- DCT_VISUAL_START -->
![Best practices and workflows visual guide](assets/images/best_practices_operations_playbook.png)
<!-- DCT_VISUAL_END -->


This page collects practical usage patterns.

## Recommended curation loop

1. Import a small dataset sample.
2. Load tag dictionary.
3. Review in Gallery.
4. Edit tags manually on a few images.
5. Run model predictions in preview mode.
6. Use assistant validation.
7. Apply only high-confidence changes.
8. Sort predicted tags if needed.
9. Save.
10. Scale to larger batches.

## Tag quality workflow

Use multiple passes:

1. Manual cleanup of obvious errors.
2. Classifier/tagger suggestions.
3. VLM validation of visible tags.
4. Assistant missing-tag suggestions.
5. Prune questionable tags.
6. Final manual review.

## Batch workflow

Use **Batch Tags** when applying model logic across many selected images.

Recommendations:

- Start with preview/sample.
- Use lower concurrency for large VLMs.
- Keep destructive apply operations separate from exploratory prompts.
- Use Jobs logs to audit failures.

## Compare workflow

Use **Compare** for:

- Picking best duplicate/near-duplicate images.
- Comparing tags/captions side-by-side.
- Testing model suggestions across two images.
- Reviewing image variants.

## Model workflow

For local models:

1. Download or migrate.
2. Rescan.
3. Confirm `DOWNLOADED`.
4. Check memory estimate.
5. Select GPU(s).
6. Load.
7. Run preview.
8. Unload when done.

For API models:

1. Add token profile.
2. Select API/cloud model.
3. Use chat/assistant/code workflows.
4. Keep provider-specific cost/rate limits in mind.

## Multi-GPU workflow

- Put small independent models on separate GPUs when possible.
- Shard only models that need it or benefit from it.
- Do not overcommit VRAM.
- Keep one GPU free when doing interactive work if possible.
- Unload unused models before starting a large VLM.

## Migration workflow across new builds

1. Extract new build.
2. Do not immediately re-download everything.
3. Open Install Migration.
4. Add old installs newest first.
5. Move/copy models and tag exports.
6. Refresh/rescan Models and Tag Dictionaries.
7. Repair/update only models with missing support files.
8. Delete old install only after confirming the new install works.

## Symlink workflow

Use symlinks for large model folders rather than keeping every build's models under its own ZIP extract.

Best shared assets:

- `models/hf/`
- `models/ultralytics/`
- `models/checkpoints/`
- `models/custom/`
- `runtime/tag_exports/`

Avoid sharing the same writable `runtime/app.db` across multiple running instances.

## Assistant workflow

- Use conversational chat for reasoning.
- Use tag-selection panel for structured tag operations.
- Use preview mode first.
- Use Finish Last Output if the model stops mid-answer.
- Clear memory when the conversation has gone in the wrong direction.
- Switch to a stronger model mid-conversation when needed.

## Code Assistant workflow

- Select only relevant files.
- Ask for a plan before a patch.
- Apply patches only after review.
- Run tests.
- Feed test failures back into the chat.
- Keep backups.

## Tab quick reference

| Tab | Primary purpose |
| --- | --- |
| Dashboard | High-level status and entry point. |
| Import | Bring local media into the app. |
| Gallery | Browse/filter/select media. |
| Tag Editor | Edit tags/captions and use image assistant. |
| Detection & Boxes | Bounding box workflows. |
| Segmentation & Masks | Mask/polygon workflows. |
| Pose & 3D | Keypoints, bones, pose workflows. |
| 3D Studio | 3D generation/asset workflows. |
| 3D Viewport | View 3D assets. |
| ComfyUI Bridge | Send/receive assets from ComfyUI. |
| FlexAvatar | Optional 3D head avatar workflow. |
| Compare | Side-by-side image/tag comparison. |
| Batch Tags | Batch tag/caption/model operations. |
| Prediction Analytics | Inspect model prediction quality. |
| Media Tools | Extract frames/audio and process media. |
| Reference Finder | Find/reference character or concept examples. |
| Source Browser | Controlled browser/source review workflows. |
| Assistant | General assistant/orchestrator control. |
| Orchestrate | Plan/user-approve multi-step model workflows. |
| Models | Download/load/unload/manage models. |
| Augment | Augmentation or external enhancement flows. |
| Downloads | Source downloads. |
| Presets | Saved settings/presets. |
| Tag Dictionaries | DB exports, autocomplete, categories. |
| Database | Database maintenance. |
| Install Migration | Move/copy assets from prior installs. |
| Code Assistant | Project-aware coding assistant. |
| Settings | Global settings and token profiles. |
| Help & Workflows | In-app guidance. |
| Jobs | Logs, progress, cancel/pause/retry. |

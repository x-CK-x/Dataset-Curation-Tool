# v5.8.28 — Thouph Preprocessing, Refresh Stability, Graph Render, LingBot World Models

## Summary

v5.8.28 preserves the working legacy vision-model loader state and adds targeted fixes for the next reported blockers:

- Thouph legacy tagger preprocessing is now model-specific instead of forcing every legacy row through the same static resize path.
- Automatic Models-tab polling and status refreshes are treated as soft renders so they do not close open dropdowns or reset nested scroll containers while the user is interacting with the page.
- Tag Editor model-score sorting adds average, specific-model, detection-count, standard-deviation, median, and mode prediction sort modes.
- Agentic Graph Editor local preset helpers are restored so the tab can render instead of throwing `graphEditorLocalPresets`/preset-helper errors.
- Multimodal Dataset Builder gains voice-profile consent/provenance schema, AV sync annotations, audio/TTS/voice-conversion/audio-video task profiles, and API endpoints.
- LingBot-Video Dense, MoE, Qwen rewriter base, and rewriter LoRA rows are added to the Models tab with a command/runtime adapter and optional job-backed launch endpoint.

## Thouph preprocessing updates

The three legacy Thouph taggers now have separate preprocessing contracts:

| Model row | Preprocessing contract |
|---|---|
| `thouph-eva02-vit-large-448-8046` | Exact 448×448 torchvision-style resize, CLIP mean/std, sigmoid multilabel scores. |
| `thouph-eva02-clip-vit-large-7704` | 224×224 CLIP preprocessing with bicubic interpolation; very tall/wide images follow the original short-edge resize + center-crop branch. |
| `thouph-experimental-efficientnetv2-m-8035` | PyTorch path uses the original 512-area aspect-preserving thumbnail with ImageNet normalization. ONNX fallback still uses static graph dimensions when the ONNX session exposes a fixed input shape. |

This matters because the EfficientNet PyTorch model was previously being forced into a static 448×448 tensor. The original script preserves aspect ratio through a thumbnail step before tensor conversion, which can materially change confidence distributions and tag dropoff.

## Refresh stability updates

The frontend now distinguishes soft automatic refreshes from explicit hard renders. Automatic polling uses a defer path when the user is scrolling, editing a field, or using a dropdown. The Models tab also has stable scroll keys for the catalog/download sections so nested scroll positions can be restored after safe renders.

Important behavior:

- Open dropdowns should no longer be closed by background status polling.
- The Models tab page scroll should not snap to top during model-status refresh.
- The downloaded/catalog scroll container should preserve its position across safe refreshes.
- Manual tab changes still render immediately.

## Tag Editor prediction sort modes

New toolbar sort controls:

- `Sort Avg Pred ↓`
- `Sort Specific Model ↓`
- `Sort Most Detected`
- `Sort StdDev ↑`
- `Sort Median ↓`
- `Sort Mode ↓`

A model selector appears in the tag strip when prediction rows exist for the current image. `Sort Specific Model ↓` uses that selector.

## Agentic Graph Editor render fix

The static frontend now includes local preset storage helpers:

- `graphEditorLocalPresets`
- `graphEditorWriteLocalPresets`
- `graphEditorSaveLocalPreset`
- `graphEditorLoadLocalPreset`
- `graphEditorDeleteLocalPreset`
- `graphEditorDownloadSnapshot`

These restore the missing functions that could cause Agentic Graph Editor to fail during render.

## Audio, voice, and video+audio dataset scope

Multimodal Dataset Builder now stores voice/speaker work as an explicit consent/provenance workflow instead of a silent automatic feature. New schema/API support includes:

- `voice_profiles`
- `av_sync_annotations`
- `/api/multimodal/voice/profiles`
- `/api/multimodal/voice/profiles/{profile_id}`
- `/api/multimodal/audio-video/sync`

New task/export profile coverage includes:

- Audio STT datasets
- TTS / voice datasets with consent manifests
- Voice-conversion paired datasets
- Audio-video alignment / sync datasets
- Voice consent/provenance manifest export profile

## LingBot-Video / world-model rows

New model rows:

- `lingbot-video-runtime-repo`
- `lingbot-video-dense-1-3b`
- `lingbot-video-moe-30b-a3b`
- `lingbot-video-rewriter-base-qwen36-27b`
- `lingbot-video-rewriter-lora`

The adapter intentionally does not expose these rows as image taggers. LingBot-Video is represented as a command/runtime bridge for the upstream `scripts/inference.py` workflow.

New API endpoints:

```text
POST /api/models/lingbot/command
POST /api/models/lingbot/run
```

`/command` returns the exact command line. `/run` queues the command as a job when the user supplies or configures a local LingBot runtime repository containing `scripts/inference.py`.

## Validation

Selected validation run:

```text
python -m compileall -q data_curation_tool integrations scripts tests
node --check data_curation_tool/static/app.js
bash -n install.sh update.sh
pytest -q tests/test_v619_scroll_onnx_gpu_legacy_load_regression.py tests/test_v618_eva_attention_pool_live_refresh.py tests/test_v618_eva_attn_pool_live_refresh.py tests/test_v618_eva_attn_pool_refresh_status.py tests/test_v617_gpu_hydra_eva_gallery_refresh.py tests/test_v616_migration_tag_database_stall_fix.py tests/test_v615_migration_progress_and_group_fastpath.py tests/test_v614_fast_same_drive_model_migration.py tests/test_v613_migration_parallel_first_run_sync.py tests/test_v612_migration_local_cache_weekly_sync.py tests/test_v611_eva_norm_pre_graph_editor_handlers.py tests/test_v610_graph_canvas_migration_progress.py tests/test_v609_graph_palette_prediction_refresh_eva_fix.py tests/test_v608_dashboard_migration_progress_refresh.py tests/test_v607_legacy_tagger_preprocess_scroll_fix.py tests/test_v605_model_prediction_normalization_unload_ui.py tests/test_v578_3d_mcp_booru_logic.py tests/test_v620_multimodal_builder_3d_mcp_tag_highlight.py tests/test_v621_thouph_preprocess_scroll_graph_sort_world_models.py
```


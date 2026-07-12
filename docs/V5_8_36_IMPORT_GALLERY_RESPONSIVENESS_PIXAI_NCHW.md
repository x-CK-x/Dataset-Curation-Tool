# v5.8.36 — Import/Gallery Responsiveness and PixAI NCHW Inference Fix

## Purpose

This patch resolves the current workflow blocker: after loading models and moving into import/gallery work, browser interactions could feel delayed, Gallery controls were slow, imported media could appear duplicated, and PixAI Tagger v0.9 failed inference with an ONNX input-layout error.

## Changes

### Passive polling no longer rebuilds heavy media tabs continuously

The 3-second app poll still refreshes jobs/model lifecycle state, but it no longer forces Gallery, Tag Editor, Compare, Batch Tags, Prediction Analytics, and annotation views to fully rebuild on every tick. These tabs now repaint only when relevant state actually changes:

- model job completion,
- inference/media refresh,
- dataset import completion,
- model loaded/downloaded state changes,
- explicit user refresh actions.

This keeps lifecycle rings and status text current without interrupting user clicks, folder selection, Gallery buttons, or tag editing.

### Folder picker made less fragile under model load

Native folder/file dialogs now run in a short-lived child Python process. This prevents Tk dialog state from living inside the long-running FastAPI process and makes the picker less vulnerable to heavyweight model/import activity in the main process.

The Import tab now provides immediate UI feedback when the picker is being opened, and queueing an import no longer performs a full `refreshAll()` before switching to Jobs.

### Gallery duplicate reduction

When **Skip exact duplicates** is enabled, imports now seed their SHA-256 duplicate map from all active media, not only from the newly-created dataset. Re-importing an already-known folder therefore skips already-known files instead of creating another visible Gallery row for each file.

The default all-datasets Gallery view also hides exact duplicate SHA rows where possible, keeping the most recent active row for each hash.

### Gallery page render speed

Gallery/media page rendering now batches tag and caption lookups. The old page conversion performed per-media tag and caption queries; the new path uses one tag query and one caption query for the visible page.

### Quick tag/rating model dropdown cues

Model option rows now expose availability cues:

- loaded models: green highlighted/strong option,
- downloaded models: blue-tinted option,
- missing downloadable models: dim option.

A small legend was added to the quick tag/rating model card.

### PixAI Tagger v0.9 ONNX input layout

PixAI’s ONNX runtime error showed that the model expected `[N,3,448,448]`, while the WD ONNX preprocessing path was feeding `[N,448,448,3]`. The isolated WD/PixAI adapter now detects ONNX input layout from the loaded session and chooses:

- WD ONNX: NHWC/BGR float tensor path,
- PixAI/other NCHW ONNX: channel-first tensor path with the DeepGHS preprocessing contract: white-background RGB, bilinear 448×448 resize, `ToTensor`, and mean/std normalization of 0.5.

This change is isolated to the WD/PixAI adapter and does not alter Thouph, JTP, Hydra, or other working tagger paths.

## Validation

Validated in the package build:

```text
python -m compileall -q data_curation_tool integrations scripts tests
node --check data_curation_tool/static/app.js
bash -n install.sh update.sh
pytest -q tests/test_v630_import_gallery_pixai_nchw_responsiveness.py tests/test_v629_download_finalize_cuda12_onnx_refresh.py tests/test_v628_graph_edges_model_lifecycle_onnx_workflows.py tests/test_v627_download_progress_guaranteed_graphs.py tests/test_v626_migrated_model_local_load_no_redownload.py tests/test_v625_graph_selection_menu_wd_pixai_augment_attention.py tests/test_v624_graph_editor_partial_region_refresh.py tests/test_v623_graph_editor_immediate_render_and_chat_fix.py tests/test_v622_attention_overlay_graph_chat_threshold.py tests/test_v621_thouph_preprocess_scroll_graph_sort_world_models.py tests/test_v620_multimodal_builder_3d_mcp_tag_highlight.py tests/test_v619_scroll_onnx_gpu_legacy_load_regression.py
```

Live browser timing, actual PixAI ONNX inference on the user's RTX workstation, and folder-dialog latency under active model load still need confirmation on the target system.

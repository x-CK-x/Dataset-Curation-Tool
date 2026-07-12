# v5.8.27 — Multimodal Dataset Builder, 3D Provider Rows, MCP Training Handoffs, and Model-Score Tag Highlighting

## Summary

This update adds a trainer-neutral **Multimodal Dataset Builder** extension for image/video/audio dataset preparation while preserving the existing image-first curation workflow. The new builder stores media assets, clips, structured caption revisions, audio annotations, visual annotations, training samples, and dataset exports in dedicated tables, then exports reviewed samples into LTX-2.3 and Wan 2.2 trainer-specific formats.

## Added backend support

New router:

```text
data_curation_tool/routers/multimodal_dataset_builder.py
```

New service:

```text
data_curation_tool/services/multimodal_dataset_service.py
```

New tables are created on service startup:

```text
media_assets
clips
caption_revisions
audio_annotations
visual_annotations
training_samples
dataset_exports
```

The service includes probe/import logic, clip suggestion/creation, structured caption rendering, training sample creation, validation, export jobs, trainer command scaffolds, and agentic captioning pipeline plan scaffolds.

## Added export profiles

The Multimodal Dataset Builder can now prepare:

```text
LTX-2.3 JSONL
LTX-2.3 JSON
LTX-2.3 CSV
Wan 2.2 Musubi TOML + sidecar captions
Wan 2.2 Musubi metadata JSONL
Wan 2.2 DiffSynth metadata.csv
Wan 2.2 SimpleTuner data_backend_config JSON
AI Toolkit folder/config skeleton
Generic JSONL manifest
```

LTX export rows use the recognized media/reference/mask column names:

```text
video
audio
caption
reference_video
reference_audio
video_mask
audio_mask
```

Validation checks now include LTX frame and spatial bucket rules and Wan/Musubi target-frame rules.

## Added frontend tab

A new top-level tab is available:

```text
Multimodal Dataset Builder
```

The tab includes cards for:

- Media Inspector / Import
- Clip Builder
- Structured Caption Editor
- Training Sample / Compatibility
- Dataset Export Wizard
- Agentic Captioning / Audio-Video Pipeline Plan
- Training MCP Framework overview
- Last Multimodal Result

## Added 3D catalog/provider rows

The 3D catalog now includes explicit rows for:

```text
Tripo P1.0 Smart Mesh / P1 API
Rodin / Hyper3D Production API
Hunyuan3D 3.1 / Tencent Cloud 3D API
```

These rows are marked as hosted/cloud/API providers. The local/open-source Hunyuan path remains represented by the existing Hunyuan3D 2.x/2.1 rows.

## Added MCP training framework handoffs

The MCP tool catalog now includes additional external training framework contracts:

```text
Musubi Tuner / Wan Video LoRA
DiffSynth-Studio / Wan Training
SimpleTuner / Wan S2V
AI Toolkit / Video+Image Diffusion Trainer
ComfyUI Training Nodes / Workflow Training
```

The existing LTX Trainer MCP row was expanded with audio/video, AV2AV, A2V, V2A, T2A, reference, and mask handoff capabilities.

## Added model-score tag highlighting

The Tag Editor now has a per-model tag score highlighter. It lets the user choose one model, multiple models, or all model rows that produced scores for the current image. Matching chips get a visual outline and can be selected into the editor highlight set.

Controls include:

```text
Any selected model
All selected models
Average selected score
Minimum score percentage
Select Matching Model Tags
Clear Model Filter
```

This works on top of the existing per-model prediction hover panel and does not replace manual tag editing.

## Validation performed

The following checks were run in the assistant environment:

```text
python -m compileall -q data_curation_tool integrations scripts tests
node --check data_curation_tool/static/app.js
pytest -q tests/test_v619_scroll_onnx_gpu_legacy_load_regression.py tests/test_v620_multimodal_builder_3d_mcp_tag_highlight.py
```

Live browser, GPU model inference, ffmpeg/ffprobe probing on user media, cloud API calls, and external trainer execution were not available in the assistant environment and should be tested locally.

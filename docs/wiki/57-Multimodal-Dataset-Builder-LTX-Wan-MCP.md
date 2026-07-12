# Multimodal Dataset Builder, LTX/Wan Exports, Training MCPs, and Model-Score Tag Highlighting

This page documents the v5.8.27 additions for video/audio/image dataset preparation.

## Multimodal Dataset Builder tab

The new tab is additive. Existing Gallery, Tag Editor, Batch Tags, Dataset Pipeline, Automation Workflows, and Model inference behavior remains unchanged.

The builder uses a trainer-neutral internal schema:

```text
Asset -> Clip -> Caption Revision -> Training Sample -> Export
```

The current UI exposes:

- media path probing/import
- clip suggestion and clip creation
- structured caption JSON editing
- caption rendering into trainer-ready text
- LTX and Wan task profile selection
- sample creation and export validation
- export jobs for LTX, Wan, AI Toolkit, and generic manifests
- training/MCP handoff command scaffolds

## LTX-2.3 export support

Export profiles:

```text
ltx_jsonl
ltx_json
ltx_csv
```

Supported columns:

```text
video
audio
caption
reference_video
reference_audio
video_mask
audio_mask
```

The validator checks:

- frame counts where `frames % 8 == 1`
- width/height multiples of 32
- required audio/video/reference fields for the selected task profile
- non-empty captions

## Wan 2.2 export support

Export profiles:

```text
wan_musubi_toml
wan_musubi_jsonl
wan_diffsynth_csv
wan_simpletuner_json
ai_toolkit
generic_manifest
```

The validator checks Musubi target-frame values using `N*4+1` and verifies required audio/image/reference fields for S2V/I2V-style samples when declared in the sample overrides/profile.

## Training MCPs

New or expanded MCP entries include:

```text
LTX Trainer
Musubi Tuner
DiffSynth-Studio
SimpleTuner
AI Toolkit
ComfyUI Training Nodes
```

These entries are handoff contracts. They do not silently launch training without user action. The generated exports and command templates should be reviewed before running any external trainer.

## New 3D provider rows

The 3D catalog now has explicit provider rows for:

```text
Tripo P1.0 Smart Mesh / P1 API
Rodin / Hyper3D Production API
Hunyuan3D 3.1 / Tencent Cloud 3D API
```

These are classified as hosted/cloud/API rows. Hunyuan3D 2.x/2.1 remains the local/open-source path in the catalog.

## Tag Editor model-score highlighter

The Tag Editor now has a model score highlighter panel inside the ordered tag editor. It can highlight tags by:

- one selected model
- several selected models
- all model rows used on the current image
- any/all/average score matching
- minimum score threshold

Matching chips receive a visible outline and can be selected into the editor highlight set using **Select Matching Model Tags**.

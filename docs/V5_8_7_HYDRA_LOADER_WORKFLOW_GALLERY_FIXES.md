# v5.8.7 — Hydra Loader, Workflow Template, and Gallery Fixes

This release fixes one more RedRocket Hydra 3.5 local inference incompatibility and addresses several frontend workflow/gallery bugs found during real use.

## Hydra 3.5 local inference

Hydra's repo-native `inference.py` can call `Loader.heuristic_max_workers(...)` and instantiate `Loader(..., max_workers=...)`. Some downloaded Hydra source snapshots expose only `Loader.heuristic_workers(...)` and do not accept `max_workers` in `Loader.__init__`. The app now patches the downloaded local source before load/inference to provide both compatibility seams.

The patch still keeps the previous `MpQueue[str]` / `Queue[str]` runtime-annotation cleanup. The model weights and tag metadata are not edited.

Patch marker:

```text
models/hf/RedRocket--Hydra/.dct_hydra_compat_patch_v2.json
```

First backup:

```text
models/hf/RedRocket--Hydra/utils/loader.py.dctbak
```

## Automation workflow presets

The Automation Workflows page now exposes and supports presets for:

- full dataset curation
- character LoRA / OC identity prep
- character + style / OC + style LoRA prep
- style LoRA prep
- concept LoRA prep
- download/query to training branch
- existing branch quality gate + export

The goal dropdown also keeps style, character, character+style, concept, IC-LoRA, ControlNet, and embedding options visible even when the dataset-pipeline catalog is still loading.

## Gallery and dense-tab refresh

Explicit Gallery actions now force a render after the API returns. This prevents the dense-tab interaction guard from deferring visible updates until the user switches tabs. The Gallery page value is clamped both in the backend media service and in the frontend page controls, so Next cannot browse beyond the last real page.

Release version: `5.8.7`.

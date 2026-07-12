# v5.8.6 — Hydra Python Queue Patch and Z3D Removal

This release is a focused model-catalog/runtime bugfix.

## Hydra 3.5 inference fix

Some local RedRocket Hydra 3.5 repository snapshots can fail on Windows/Python 3.11 before inference starts with:

```text
TypeError: type 'Queue' is not subscriptable
```

The failing upstream source annotation is equivalent to `MpQueue[str]`. On Python runtimes where `multiprocessing.Queue` is not subscriptable at import time, the module import fails before Hydra reaches the model code.

The app now patches the downloaded local Hydra source tree before load/inference:

- target file: `models/hf/RedRocket--Hydra/utils/loader.py`
- replacement: queue annotations such as `MpQueue[str]`, `Queue[int]`, and `mp.Queue[str]` become `MpQueue`, `Queue`, and `mp.Queue`
- backup: the first original file is preserved as `loader.py.dctbak`
- marker: `.dct_hydra_py311_queue_patch.json`

The patch only edits the downloaded Hydra Python utility source. It does not alter model weights, tag metadata, or user datasets.

## Z3D / Zack3D removal

The unavailable Z3D/Zack3D legacy tagger entry was removed from:

- legacy tagger config registry
- Models catalog
- legacy model tests
- documentation tables

The remaining legacy taggers are still available:

| Model | Provider | Notes |
|---|---|---|
| Thouph EVA02-CLIP ViT-Large 7704 | Hugging Face | ONNX/EVA02-CLIP tagger config |
| Thouph EVA02 ViT-Large 448 8046 | Hugging Face | PyTorch/ONNX-compatible legacy config |
| Thouph Experimental EfficientNetV2-M 8035 | Hugging Face | EfficientNetV2-M legacy config |

## Version

Release version: `5.8.6`.

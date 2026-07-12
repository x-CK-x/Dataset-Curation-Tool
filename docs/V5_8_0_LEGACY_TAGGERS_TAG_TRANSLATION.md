# v5.8.0 — Legacy Tagger Catalog, Local Inference, and Tag/Caption Translation

This release promotes the legacy/local image taggers from the original Data Curation Tool model configuration into the modern model catalog.

## Added tagger rows

The Models tab now includes:

| Model | Runtime | Input | Tags | Notes |
|---|---:|---:|---:|---|
| Thouph EVA02-CLIP ViT-Large 7704 | ONNX or PyTorch pickle | 224×224 | 7,704 | CLIP mean/std, sigmoid multilabel output, placeholder padding. |
| Thouph EVA02 ViT-Large 448 8046 | PyTorch pickle or ONNX | 448×448 | 8,046 | CLIP mean/std, explicit/questionable/safe output labels. |
| Thouph Experimental EfficientNetV2-M 8035 | ONNX or PyTorch pickle | thumbnail-area preprocessing | 8,035 | ImageNet mean/std and original aspect-ratio thumbnail preprocessing. |

## Runtime behavior

The shared `LegacyVisionTaggerAdapter` handles:

- per-model input dimensions;
- ONNX Runtime execution when `.onnx` files are present;
- PyTorch pickle execution when complete `.pth` model objects are present;
- model-specific mean/std normalization;
- tag JSON/CSV loading;
- output-dimension extension and placeholder filtering;
- threshold/top-k filtering;
- rating tag passthrough when a model emits rating labels.

## Integration surfaces

The legacy taggers are now cataloged as `tagger` models with the same capabilities used by Hydra/JTP:

- Models tab;
- Tag Editor quick model runs;
- Compare and Batch Tags;
- annotation-context quick runs;
- orchestration/model-selection surfaces;
- Remote Devices model dispatch, when the worker has the same model files.

## Tag alias and implication cleanup

Model-emitted tags now pass through the active profile alias/implication cleanup before being previewed or applied. For e621-style taggers this means aliases can resolve to canonical tags and implications can add required parent/consequent tags when the local dictionary contains those relationships.

## Tag/caption format translation

The Tag Dictionaries tab includes a new translator card. It can:

- translate a tag string from one profile to another;
- use deterministic alias/exact matching first;
- preserve unknown tags or mark them as unresolved;
- output booru tag strings, comma captions, natural captions, or JSON packets;
- optionally send an unresolved-mapping prompt packet to a selected local/cloud LLM or VLM.

This is intended for cross-profile workflows such as e621-style taggers feeding Danbooru/Gelbooru-style captions or custom training-caption formats.

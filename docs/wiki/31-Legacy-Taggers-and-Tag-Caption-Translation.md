# Legacy Taggers and Tag/Caption Translation

![Model lifecycle and GPU dashboard](assets/images/model_lifecycle_and_gpu_dashboard.png)

v5.8 adds model-catalog support for the local taggers from the original model configuration and adds a profile-aware tag/caption translation workflow.

## Added legacy taggers

| Catalog row | Source | Runtime | Preprocessing | Output |
|---|---|---|---|---|
| Thouph EVA02-CLIP ViT-Large 7704 | Hugging Face | ONNX or PyTorch pickle | 224×224, CLIP mean/std | e621 multilabel tags |
| Thouph EVA02 ViT-Large 448 8046 | Hugging Face | PyTorch pickle or ONNX | 448×448, CLIP mean/std | e621 tags plus rating labels |
| Thouph Experimental EfficientNetV2-M 8035 | Hugging Face | ONNX or PyTorch pickle | aspect-ratio thumbnail area, ImageNet mean/std | e621 multilabel tags |

These rows appear as `tagger` models in the Models tab and are available anywhere the app accepts local image taggers: Tag Editor, Compare, Batch Tags, annotation-context cards, and orchestration/model-selection surfaces.

## Local model loading

The shared legacy adapter searches the downloaded model folder for the expected model file and tag metadata file. It supports `.onnx`, `.pth`, `.pt`, `.json`, and `.csv` metadata layouts.

For ONNX models, install `onnxruntime`. For PyTorch pickle models, install the standard model runtime stack: `torch`, `torchvision`, `timm`, `numpy`, and `pillow`.

## Alias and implication cleanup

When a tagger emits tags, the app now runs the predicted labels through the active booru profile before preview/apply:

1. normalize the model label;
2. resolve aliases from the active profile;
3. add known implications/consequents from the local tag dictionary;
4. apply the active tag text mode, either underscores or spaces.

This is especially useful for e621-style taggers because the model may emit aliases or terms that need profile-aware cleanup before training export.

## Tag/caption translation

Open **Tag Dictionaries → Tag / Caption Format Translator**.

The translator supports:

| Option | Purpose |
|---|---|
| Source profile | Profile that owns the current tags. |
| Target profile | Profile the tags should be translated into. |
| Output format | Booru tag string, comma caption, natural caption, or JSON packet. |
| Preserve unknowns | Keep unmapped terms instead of dropping them. |
| Ask LLM/VLM | Send unresolved mappings to a selected local/cloud model. |

The deterministic pass is intentionally conservative. It resolves exact tags and aliases first, then marks uncertain terms for the LLM/VLM instead of silently inventing target-profile tags.

## Recommended workflow

1. Sync the tag dictionaries for the source and target booru profiles.
2. Run a tagger on a small sample and inspect the prediction preview.
3. Use the translator to convert e621-style tags into the target profile or caption style.
4. Send unresolved mappings to a selected model only after the deterministic mapping packet is generated.
5. Apply the final tags/captions to a branch dataset rather than mutating the global original layer.

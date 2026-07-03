# v5.27 Class-aware spatial inference

## Why identical outputs occurred

The earlier spatial adapter accepted a user-entered class name but did not resolve it to the model's trained class ID. Closed-set YOLO results were then renamed to the typed value after inference. As a result, changing `cat` to `dog` could display the same boxes and confidence values under a different label.

SAM, SAM-HQ, and SAM2 are promptable segmentation models, but a plain class-name string is not a spatial prompt. Automatic mask generation is class-agnostic, so changing only a text label does not change the masks.

## Corrected model semantics

### Closed-set detection and segmentation models

For Ultralytics/YOLO-family checkpoints, the app reads `model.names` or safe sidecar metadata, resolves the requested class to one or more class IDs, and passes those IDs to inference. Unsupported class names now fail with suggestions instead of silently relabeling unrelated objects.

The app also post-filters returned rows by class ID in case a custom/exported backend ignores the runtime filter.

### Text-conditioned models

Open-vocabulary adapters expose `text_conditioned` prompt semantics. Their free-form prompt is sent to the actual model adapter and is expected to influence geometry.

### SAM, SAM-HQ, and SAM2

These are exposed as `class_agnostic` models. Users may:

1. Clear the class token and generate automatic class-agnostic masks.
2. Draw or copy a bbox prompt into segmentation.
3. Enable **Semantic Class → Detector → SAM Pipeline**. The detector resolves the requested class, returns every matching bbox up to the configured limit, and each bbox is sent to SAM as a separate prompt.

A semantic class token without a bbox or detector guide is rejected so the tool cannot imply that text changed SAM geometry when it did not.

## Multiple-output controls

Detection and YOLO segmentation pass these controls to inference:

- confidence threshold
- NMS IoU threshold
- `max_det`
- class-aware or class-agnostic NMS
- test-time augmentation
- input image size
- high-resolution mask output where supported

SAM/SAM2 automatic generation exposes:

- points per side
- predicted-IoU threshold
- stability threshold
- mask-box NMS
- crop layers
- crop point downscale
- minimum mask region area
- maximum proposal count

Prompted SAM/SAM2 can return multiple alternatives per bbox and can process multiple bbox prompts in one run.

## Custom model class discovery

The app attempts to derive supported classes from:

- Ultralytics `model.names`
- `data.yaml`, `dataset.yaml`, or other YAML metadata
- `config.json` / `id2label` / `label2id`
- `classes.txt`, `labels.txt`, `names.txt`, and `.names`
- CSV class tables
- ONNX metadata
- safetensors metadata

Arbitrary custom checkpoints are not directly unpickled merely to inspect metadata. If a class list cannot be found, place a sidecar class file next to the checkpoint or load/validate the model through its supported runtime.

## Clearing generated output

Each spatial tab now distinguishes:

- **Clear Generated Preview**: clears unsaved boxes/masks and removes unreferenced preview mask files.
- **Delete Saved Model Boxes/Masks**: deletes model/API/VLM-generated saved annotations for the current image while preserving user-created annotations.

# v5.8.14 Legacy Tagger Runtime and Scroll Stability Fixes

This update fixes two legacy local tagger inference failures and reduces UI scroll jitter during live-refresh renders.

## Legacy EfficientNetV2-M static input fix

The legacy EfficientNetV2-M tagger now guarantees a final `1 x 3 x 448 x 448` tensor before ONNX or PyTorch inference. The previous area-thumbnail preprocessing path could leave the tensor at an image-derived size such as `552 x 473`, which ONNX Runtime rejects for the fixed-input classifier.

## Legacy EVA/timm pickle compatibility fix

Older pickled EVA models may be missing optional attributes expected by newer `timm` forward paths. The adapter now patches missing `reg_token`/`mask_token` attributes to `None` before moving the model to device and running inference.

## Scroll stability fix

The frontend no longer schedules multi-second scroll restoration after ordinary renders. Scroll restoration is tokenized and short-lived, with aggressive restore only on explicit tab switches. This prevents live job/model/gallery refreshes from fighting the user’s own scrolling.

## Validation

Selected regression tests compile the app, validate the frontend, and verify the legacy preprocessing and EVA compatibility patches.

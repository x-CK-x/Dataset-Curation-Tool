# Legacy Tagger Inference and Scroll Stability Fixes

v5.8.14 fixes two inference issues in the legacy tagger adapter and reduces the erratic scrollbar behavior seen during live UI refreshes.

## Fixed EfficientNetV2-M input size

The legacy EfficientNetV2-M tagger requires a static `448 x 448` input. The adapter now enforces that final size before inference, even if a preprocessing mode stages the image through aspect-ratio preservation.

## Fixed EVA pickle compatibility

The legacy EVA tagger can be loaded from an older PyTorch/timm pickle. If the loaded object lacks nullable EVA attributes such as `reg_token` or `mask_token`, the adapter adds them as `None`, matching the neutral behavior expected by the newer `timm` runtime.

## Fixed scroll jitter

The frontend now uses short-lived, tokenized scroll restoration. Normal background refreshes should no longer repeatedly snap the main panel back while the user is scrolling.

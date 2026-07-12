# GPU, Hydra, EVA, and Gallery Refresh Fixes

v5.8.24 fixes several model/runtime issues:

- Hydra 3.5 is listed as a local tagger by default, not as an MCP-oriented model.
- Legacy EVA taggers receive more compatibility defaults for newer `timm` versions.
- CUDA assignment is stricter: the app should fail loudly rather than silently running a requested GPU model on CPU.
- ONNX Runtime receives an explicit CUDA `device_id` for legacy ONNX taggers.
- Model-page interactions should be faster because the static model catalog is cached briefly.
- Gallery and tag views refresh their data when returning to the tab and after relevant completed jobs.
- Prediction hover colors use a larger fixed palette to avoid overlapping colors across multiple model predictions.

# v5.8.24 — GPU Placement, Hydra Catalog, EVA Compatibility, and UI Refresh Fixes

This release addresses several runtime and UI regressions reported after v5.8.23.

## Changes

- Hydra 3.5 is now classified as a normal local tagger by default. Its catalog row no longer advertises MCP/model-offload capability tags that caused it to appear in the wrong model category.
- Legacy EVA/timm compatibility now includes `q_norm`, `k_norm`, and `qk_norm` defaults for old pickled EVA checkpoints running under newer `timm` code.
- Legacy ONNX taggers now fail loudly if a CUDA GPU was explicitly selected but ONNX Runtime does not provide `CUDAExecutionProvider`.
- Legacy ONNX taggers now pass `device_id` to ONNX Runtime’s CUDA provider, so `cuda:1` does not silently become provider GPU 0.
- Legacy PyTorch taggers no longer silently fall back to CPU when a requested CUDA device cannot be used.
- Runtime inference now prefers explicit `device_ids` over stale CPU/offloaded placement metadata.
- Model catalog listing uses a short static cache to avoid repeatedly scanning large local model folders during normal model-page interactions.
- Gallery/Tag Editor/Compare/Prediction Analytics now force relevant media refreshes when entering the tab or after completed download/model jobs.
- Prediction hover colors use a fixed high-contrast hue palette so multiple model rows are easier to distinguish.

## Operational note

If a model is already loaded on the wrong GPU or has been CPU-offloaded from a previous run, unload it once and load it again with the intended GPU selection. After this release, the tool should no longer silently use CPU or an unintended ONNX CUDA device when the user has selected a GPU.

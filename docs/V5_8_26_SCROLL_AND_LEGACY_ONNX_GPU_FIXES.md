# v5.8.26 — Scroll Stability and Legacy ONNX/GPU Load Fixes

This update fixes two regressions found after v5.8.25.

## Fixed scroll jumping during automatic refresh

Automatic polling refreshes were still able to replace the active app shell while the user was reading or scrolling. In some cases, stale shell scroll memory restored the outer window or nested scroll containers back to old positions, which made the scrollbar jump back to the top every few seconds.

v5.8.26 changes the refresh path so automatic updates defer while active scrolling is detected and the shell no longer restores the outer window scroll during normal in-tab renders. User-triggered refresh buttons can still force an immediate refresh, but polling/status updates should not fight the current scroll position.

## Fixed legacy tagger load regressions

The EfficientNetV2-M legacy tagger is now restored to the original runtime preference from `model_configs.py`: PyTorch checkpoint first, ONNX only as fallback. This avoids loading an ONNX artifact first when the available runtime lacks `CUDAExecutionProvider`.

For ONNX-only legacy taggers such as EVA02-CLIP, the installer requirements now prefer `onnxruntime-gpu` instead of CPU-only `onnxruntime`. Existing environments should run `update.bat` or `update.sh` to replace CPU-only ONNX Runtime with the GPU runtime. If a CUDA ONNX provider is still unavailable, ONNX-only rows can load on CPU with an explicit warning instead of failing at model-load time, while PyTorch fallback rows use the PyTorch checkpoint on the requested CUDA device when available.

## Files changed

See `docs/V5_8_26_FILE_CHANGES.json`.

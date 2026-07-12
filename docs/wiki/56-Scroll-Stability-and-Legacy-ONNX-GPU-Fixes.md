# Scroll Stability and Legacy ONNX/GPU Fixes

v5.8.26 addresses two issues:

1. app-wide scrollbars jumping back to the top during automatic polling refreshes;
2. legacy ONNX taggers failing to load on CUDA systems when only CPU ONNX Runtime was installed.

## Scroll behavior

The app now treats automatic refreshes differently from explicit user refreshes. Polling updates defer while the user is actively scrolling and do not restore the outer window scroll from stale shell memory. This preserves the current position in the main tab and nested scroll areas.

## Legacy ONNX GPU behavior

Install/update requirements now use `onnxruntime-gpu>=1.18`. Existing installs should run the updater so ONNX taggers can use CUDA providers.

For legacy rows with both ONNX and PyTorch artifacts, the adapter now prefers the PyTorch checkpoint when the ONNX CUDA provider is unavailable. For ONNX-only rows, the adapter can load on CPU with a warning instead of failing immediately, but GPU inference still requires `onnxruntime-gpu` and a working CUDA provider.

## Practical update step

Run:

```bat
update.bat
```

or on Linux:

```bash
./update.sh
```

Then restart the app and reload the affected tagger models.

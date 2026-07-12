# v5.8.35 — Download Finalization, CUDA-12 ONNX Runtime, and Model-Row Refresh

## Purpose

This release fixes two blocking model-management issues observed after v5.8.34:

1. A model could finish downloading while the Models tab continued to show **NOT DOWNLOADED** or **INCOMPLETE/CORRUPT** until a later full catalog refresh.
2. PixAI / WD ONNX taggers could install or repair to an ONNX Runtime GPU wheel that expected CUDA 13 DLLs, producing errors such as missing `cublasLt64_13.dll` on CUDA-12 workstations.

The patch keeps strict GPU placement. If a user explicitly selects `cuda:0` or `cuda:1`, the ONNX adapter must actually activate `CUDAExecutionProvider` for that selected device. It does not silently accept CPU execution for explicit CUDA placement.

## Download completion refresh

### Backend

Added a narrow single-model reconciliation path:

```text
POST /api/models/reconcile/{model_name}
```

The endpoint:

- recomputes local completeness for exactly one model row;
- marks the download lifecycle stage as completed when the payload is valid;
- returns the patched row and lifecycle state;
- invalidates the model catalog cache only after a verified local payload is found;
- avoids a full model-root scan on the critical path immediately after a download job finishes.

This prevents the UI from waiting several minutes for the next expensive full catalog refresh before replacing stale **NOT DOWNLOADED** / **INCOMPLETE/CORRUPT** badges.

### Frontend

The model-download job watcher now handles a completed job by calling the single-model reconciliation endpoint rather than awaiting:

```text
refreshModelsPanel({ force: true })
```

The Models tab now patches the affected row immediately, updates the lifecycle strip, and renders the current panel without resetting scroll position or scanning every model folder.

## Slow or stalled downloads

Hugging Face model downloads now set conservative default Hub timeouts before importing `huggingface_hub`:

```text
HF_HUB_DOWNLOAD_TIMEOUT=60
HF_HUB_ETAG_TIMEOUT=60
```

The directory-progress monitor now emits a heartbeat once per second and adds an explicit stalled-transfer message when no new local bytes have appeared for a configurable interval:

```text
DCT_MODEL_DOWNLOAD_STALL_NOTICE_SEC=75
```

The job remains running, but the user gets a visible message that the app is still waiting on the network/Hugging Face transfer rather than silently hanging.

## ONNX Runtime GPU repair

The ONNX Runtime GPU dependency is now pinned to the CUDA-12-compatible line with runtime extras:

```text
onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23
```

This replaces the previous broad spec:

```text
onnxruntime-gpu>=1.18,<2
```

The broad spec could resolve to an ONNX Runtime wheel that expects CUDA 13, which is not compatible with the user's CUDA-12 workstation environment.

Updated files:

```text
environment.yml
requirements.txt
requirements-models.txt
requirements-annotation-models.txt
scripts/repair_onnxruntime_runtime.py
```

The repair script now checks and reports:

- imported `onnxruntime.__file__`;
- callable `InferenceSession`;
- callable `get_available_providers`;
- installed CPU/GPU distribution metadata;
- whether `preload_dlls` exists;
- whether CUDA/cuDNN/MSVC DLL preloading succeeds;
- available execution providers in the current process;
- available execution providers in a fresh interpreter after repair.

## WD/PixAI ONNX adapter behavior

For the isolated WD/PixAI tagger adapter, CUDA session creation now:

1. imports PyTorch first when available, so PyTorch-shipped CUDA DLLs are visible;
2. calls `onnxruntime.preload_dlls(cuda=True, cudnn=True, msvc=True)` when available;
3. verifies that `CUDAExecutionProvider` exists before creating the session;
4. creates the session with the selected `device_id`;
5. rejects the load if the active providers do not include `CUDAExecutionProvider` for explicit CUDA placement.

The error message now points to the repair command:

```bat
python scripts\repair_onnxruntime_runtime.py --ensure-gpu --force
```

or:

```bat
update.bat
```

## Required action for existing installs

After extracting v5.8.35 over an existing install, run:

```bat
update.bat
```

For a focused ONNX Runtime repair, run:

```bat
python scripts\repair_onnxruntime_runtime.py --ensure-gpu --force
```

This is required because Python package metadata and DLL dependencies live inside the active Conda environment. Replacing project source files alone cannot repair an already-installed wrong ONNX Runtime GPU wheel.

## Files changed

See:

```text
docs/V5_8_35_FILE_CHANGES.json
```

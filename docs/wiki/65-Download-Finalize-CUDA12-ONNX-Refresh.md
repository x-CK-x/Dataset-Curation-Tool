# v5.8.35 — Download Finalize, CUDA-12 ONNX, and Refresh Fix

## What this fixes

v5.8.35 addresses a model-management failure mode where a model download completed but the Models tab continued showing stale badges such as **NOT DOWNLOADED** or **INCOMPLETE/CORRUPT** until a much later full refresh.

It also repairs the ONNX Runtime GPU dependency path so the app does not install a CUDA-13 ONNX Runtime wheel on a CUDA-12 workstation.

## Immediate model-row reconciliation

Completed download jobs now call:

```text
POST /api/models/reconcile/{model_name}
```

This validates only the model that just finished downloading and patches that row immediately. It avoids waiting on a full scan of every model folder and migrated model root.

## Download stall visibility

Hugging Face downloads now expose clearer job messages when local bytes stop changing for a while. The job stays active, but the user sees that the app is still waiting on the transfer rather than doing nothing.

Configurable timeout/stall settings:

```text
HF_HUB_DOWNLOAD_TIMEOUT=60
HF_HUB_ETAG_TIMEOUT=60
DCT_MODEL_DOWNLOAD_STALL_NOTICE_SEC=75
```

## CUDA-12 ONNX Runtime pin

The dependency is now:

```text
onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23
```

This avoids installing a newer CUDA-13 ONNX Runtime wheel that expects DLLs such as `cublasLt64_13.dll`.

## Existing installs

Run:

```bat
update.bat
```

or directly:

```bat
python scripts\repair_onnxruntime_runtime.py --ensure-gpu --force
```

The source-code update alone cannot repair an already-installed wrong Python wheel in the Conda environment.

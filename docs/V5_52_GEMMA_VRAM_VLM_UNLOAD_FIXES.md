# v5.52 Gemma VRAM, VLM Input, and Unload Fixes

## What changed

### 1. Runtime memory is now shown before use

Model dropdowns and model cards now show memory estimates before you run or load a model. For rows that include precision-specific metadata, the UI shows profiles such as:

```text
bf16 ~26.7GB / fp16 ~26.7GB / 8bit ~13.4GB / 4bit ~6.7GB
```

This is intended to make it clear that checkpoint/download size is not the same thing as runtime VRAM allocation.

### 2. Gemma 4 memory profiles are used directly

The placement planner now uses `runtime_vram_profiles` when a catalog row has them. For Gemma 4:

- `gemma-4-e2b-it`: BF16/FP16 11.4 GB, 8-bit 5.7 GB, 4-bit 2.9 GB
- `gemma-4-e4b-it`: BF16/FP16 17.9 GB, 8-bit 8.9 GB, 4-bit 4.5 GB
- `gemma-4-12b-it`: BF16/FP16 26.7 GB, 8-bit 13.4 GB, 4-bit 6.7 GB

If a selected precision does not fit, the placement error now includes the lower-memory alternatives.

### 3. Conservative driver-free VRAM readings no longer hard-block by default

On Windows, NVIDIA/driver-reported free VRAM can be lower than what appears idle in Task Manager. The app now separates:

- physical total VRAM
- app reservation budget
- app-reserved VRAM
- driver-reported free VRAM
- driver-limited available VRAM

By default, placement decisions use the app reservation budget and show a warning when driver-free memory is lower. Set `strict_driver_free_memory_checks=true` in settings if you prefer strict driver-free enforcement.

### 4. Gemma 4 VLM input path fixed

Gemma 4 requires newer multimodal input handling. The VLM adapter now tries:

- `any-to-any` pipeline for Gemma 4
- `image-text-to-text` pipeline fallback
- `AutoModelForMultimodalLM` fallback
- image-token fallback for older `image-text-to-text` pipeline variants

The downloader allow-list now includes:

```text
chat_template*
*.jinja
```

Older downloads may be missing `chat_template.jinja`. Use **Re-download / Update** for the Gemma model if you previously downloaded it before v5.52.

### 5. Unload now clears long-lived adapter references

The registry keeps adapter objects alive in model catalog rows. Earlier unload paths removed the loaded-model record but could leave `pipeline`, `model`, or `processor` attributes populated on the adapter object. v5.52 explicitly moves model objects to CPU when possible, clears those attributes, runs Python GC, and calls CUDA cache cleanup.

## Practical notes for 24 GB GPUs

A single 24 GB card should be able to run Gemma 4 E2B/E4B in 16-bit mode based on the catalog profiles. Gemma 4 12B in BF16/FP16 is listed at roughly 26.7 GB runtime memory, so it should use 8-bit or 4-bit quantization, CPU/cloud, or multi-GPU sharding.

If the model still fails to load after the planner says it should fit, open the job details/logs. The actual runtime may still fail if the local Transformers/PyTorch build is too old, bitsandbytes is missing for quantization, CUDA memory is fragmented, or another process owns VRAM outside the app’s reservation tracker.

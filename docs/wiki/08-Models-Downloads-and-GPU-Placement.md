# Models, Downloads, and GPU Placement

<!-- DCT_VISUAL_START -->
![Models, downloads, GPU placement, and jobs visual guide](assets/images/model_lifecycle_gpu_jobs.png)
<!-- DCT_VISUAL_END -->


The **Models** tab is the central control surface for local models, API/cloud models, downloads, loading/unloading, lifecycle status, VRAM planning, and custom model registration.

## Model states

Model rows and dropdowns can show status badges such as:

| Badge | Meaning |
| --- | --- |
| DOWNLOADED | Local reusable files are present. |
| NOT DOWNLOADED | The model is known in the catalog but no local copy exists. |
| SUPPORT WARNING | Weights exist, but optional/repairable support files may need update. |
| NEEDS REPAIR/UPDATE | Hard integrity issue such as missing folder or zero-byte weight file. |
| LOADED xN | One or more in-memory instances are loaded. |
| ACTIVE | Model is currently loaded/active. |
| CUSTOM | User-added custom model. |

Dropdowns include status so the user can see whether a model is downloaded/loaded before selecting it.

## Lifecycle circles

The app tracks four model lifecycle phases:

1. Download.
2. Load into RAM/VRAM.
3. Inference.
4. Training.

Unload uses a distinct unloading state and color so it does not look like the model is still loaded. After unload completes, load/inference status resets.

## Downloading models

Recommended large-model download mode:

```text
Serial queue: one model file transfer at a time
```

Use this for large Hugging Face models, unstable network connections, VPN switching, or when previous parallel downloads corrupted or timed out.

Parallel transfers can be used when:

- The network is stable.
- The storage device can handle multiple writes.
- The host is not already saturated.
- The model repo is made of many smaller files.

## Pause, resume, stop, and retry

Use **Jobs** for download operations:

- Pause Downloads.
- Resume Downloads.
- Stop Checked Jobs.
- Retry failed download from scratch.

Pausing is cooperative. A large file may pause at the next checkpoint/progress callback.

## Loading models

Before loading:

1. Pick the model.
2. Check memory estimate.
3. Select GPU IDs.
4. Pick dtype/quantization.
5. Choose sharding strategy if needed.
6. Load.

## GPU placement controls

Common controls:

| Control | Use |
| --- | --- |
| Device | `auto`, `cpu`, or CUDA target. |
| GPU IDs | Exact GPUs allowed for the model. |
| Sharding strategy | Whether/how to split model placement. |
| Torch dtype | `auto`, fp16, bf16, etc. |
| Quantization | `none`, `8bit`, or `4bit`. |
| Runtime engine | Transformers, vLLM, SGLang, llama.cpp, cloud, or auto depending on model support. |
| Tensor parallel size | Parallelism hint for engines that support it. |
| Max memory | Per-GPU memory reservation overrides. |

## VRAM estimates

Model dropdowns and cards include memory estimates when known.

Use quantization or multiple GPUs when a model exceeds single-GPU capacity. For example, a model that needs more than 24 GB in fp16/bf16 should be loaded in 8-bit/4-bit, sharded, placed on CPU/cloud, or moved to a larger GPU.

## Unloading models

Use unload when done with a model.

Unload attempts to:

- Remove loaded registry references.
- Move model objects to CPU when possible.
- Clear adapter references.
- Run garbage collection.
- Empty CUDA cache.
- Reset lifecycle load/inference state.

If VRAM does not drop immediately, wait a few seconds and re-check. Some drivers report memory lazily, and some libraries keep allocator caches.

## Custom models

Adding a custom model requires a category. Categories include:

- classifier
- tagger
- rating
- captioner
- LLM
- VLM
- detection
- segmentation
- embedding
- pose2d
- pose3d
- upscaler
- external image tool
- custom

Custom models are sorted near the top and use a distinct background style so they are easy to find.

## Model adapters

A catalog row is not enough for inference. A usable local model also needs an adapter that knows how to load and call it.

When an adapter is missing or incompatible, the job error should say so. Use the Jobs tab to inspect full error details.

## Re-download / Update

Use update/repair when a model folder has weights but lacks support files such as:

- `chat_template.jinja`
- `processing_*.py`
- `configuration_*.py`
- `modeling_*.py`
- processor/tokenizer configs

Older app builds may have downloaded only weights and skipped required lightweight support files.

## API/cloud models

API models should be configured through token profiles in Settings. They are sorted after local VLM/LLM/tag/caption models in relevant dropdowns.

See [Assistant, Orchestrator, and Chat](09-Assistant-Orchestrator-and-Chat.md) and [Code Assistant](14-Code-Assistant.md).

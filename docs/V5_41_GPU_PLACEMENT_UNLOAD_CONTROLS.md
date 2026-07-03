# v5.41 GPU Placement, Residency, and Unload Controls

This build adds explicit model memory-placement controls for multi-GPU systems and makes unload operations visible through the same circular model lifecycle status system used for downloads, loads, inference, and training.

## What changed

### Per-model GPU placement controls

Each model card in the Models tab now exposes a load-placement panel before **Load Into Memory**:

- runtime device, such as `auto`, `cpu`, `cuda`, or `cuda:0`
- exact CUDA GPU ids, such as `0`, `1`, or `0,1`
- sharding strategy: `none`, `auto`, `balanced`, `balanced_low_0`, `sequential`, or `custom`
- torch dtype: `auto`, `float16`, `bfloat16`, or `float32`
- quantization: `none`, `8bit`, or `4bit`
- runtime engine: `transformers`, `vllm`, `sglang`, `llama.cpp`, `cloud`, or `auto`
- tensor-parallel size
- optional per-GPU max-memory caps such as:

```text
0=23GiB
1=23GiB
```

The **Check VRAM / Placement** button asks the backend for a placement plan before the model is loaded.

### VRAM reservation and overcommit checks

The backend now estimates model VRAM use against detected CUDA devices and currently loaded/loading app-level reservations. It blocks load requests that would exceed the selected GPU budget before the adapter begins allocating memory.

The check is intentionally conservative. Runtime frameworks can still fail after this step if a model adapter, driver, CUDA build, quantization library, or sharding strategy is incompatible. Those failures are reported in the model load lifecycle stage.

### GPU residency panel

The top Models status card now shows:

- detected CUDA devices
- total and usable VRAM
- estimated app-reserved VRAM
- driver-reported free VRAM when available
- loaded models
- models currently loading with reserved placement

### Unload as a tracked job

The **Unload** buttons now queue a `model_unload` job instead of pretending unload completed instantly. The load lifecycle circle changes state while the app unloads model adapters, releases RAM/VRAM residency metadata, runs garbage collection, and clears CUDA cache where PyTorch is available.

### Already-loaded behavior

Loading a model that is already resident does not spawn a duplicate load job. The API returns the current residency/placement metadata instead.

## API additions

```text
GET  /api/models/resource-status
GET  /api/models/placement
POST /api/models/placement/plan
POST /api/models/unload
```

`POST /api/models/unload` now returns a queued job when a loaded model exists. If nothing is loaded, it returns a completed no-op response.

## Notes

- The app tracks its own model reservations, not every process on the machine.
- Driver-reported free memory is used when available, but exact VRAM behavior still depends on the runtime backend.
- To move a loaded model to a different GPU selection, unload it first and then load it again with the new placement controls.

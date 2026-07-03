# v5.71 VRAM Memory Policy and CPU Offload

This release adds explicit runtime memory management for long local LLM/VLM sessions.

## Why this exists

A model can fit in VRAM at load time but still run out of memory after several long prompts because generation creates temporary CUDA allocations and KV-cache/workspace memory. The application now treats that as a runtime memory-management problem instead of forcing the user to close the whole app.

## Added controls

Settings → **Model VRAM / Long Chat Memory Management** includes:

- cleanup CUDA cache after inference
- aggressive Python garbage collection
- reset peak CUDA statistics
- enable CPU offload policy
- CPU offload policy:
  - disabled
  - on pressure
  - after chat
  - after every inference
- VRAM pressure threshold
- disable generation KV cache under context pressure
- context pressure threshold
- debug cleanup snapshots
- manual **Clean CUDA Cache Now** button
- manual **Move Loaded Models to CPU RAM** button

## Runtime behavior

After model chat/prediction calls, the app now attempts to:

1. synchronize CUDA where available;
2. run Python garbage collection;
3. clear PyTorch CUDA cache and IPC cache;
4. reset peak CUDA statistics when enabled;
5. optionally move loaded model weights to CPU RAM when the selected policy triggers.

CPU offload is different from unload. It keeps the adapter object and CPU-side state alive but moves supported model tensors out of VRAM. The next request reactivates the model onto the selected CUDA device.

## KV-cache pressure mode

When the estimated prompt/context pressure is high, the app can pass `use_cache=false` to Transformers generation. This is slower, but it can reduce temporary KV-cache memory spikes during long chat sessions.

## Caveats

Some quantized, Accelerate-sharded, or custom remote-code models may not support `.to("cpu")` cleanly after loading. In those cases the app logs the offload error and still performs cache cleanup. Use full unload if a model family cannot support CPU offload.

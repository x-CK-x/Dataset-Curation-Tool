# v5.42 GPU Placement, Dropdown, and VLM Tag-Selection Fixes

This build adds another stabilization layer on top of the model lifecycle work.

## Dropdown stability

All normal polling renders now defer while the user is interacting with a dropdown. Native select menus can close when their parent DOM is re-rendered, so select interactions receive a longer render hold than text fields. Deferred renders are flushed after the control interaction finishes.

## GPU placement and unload control

The Models tab exposes explicit runtime placement controls:

- selected device mode
- selected CUDA GPU IDs
- sharding strategy
- dtype
- quantization
- runtime engine
- tensor parallel size
- per-GPU max memory map

The backend planner estimates VRAM reservations before loading and blocks GPU placements that would exceed the currently selected budget. It also reports a clear error when NVIDIA tools can see a GPU but PyTorch CUDA is not usable in the current app environment. This prevents silent-looking no-op loads such as a downloaded model appearing to do nothing when the runtime cannot actually allocate CUDA tensors.

Unload is treated as a lifecycle operation on the load stage. The load circle shows unload progress and the resource panel releases the RAM/VRAM reservation when the adapter is unloaded.

## LLM/VLM tag selection in the Tag Editor

The Tag Editor now supports manual tag highlighting directly in the ordered tag strip. You can:

- click chips to select/highlight or deselect them
- select all
- deselect all
- inverse all
- select by category
- deselect by category

Manual highlights are sent into the `LLM/VLM/Assistant Tag Selection for This Image` request as candidate tags. Preview results from an LLM/VLM also become highlighted candidates. If a VLM proposes tags for an image that currently has no tags, those proposed tags are displayed in a candidate panel instead of being pruned away because they are not yet in the draft.

The candidate panel supports adding one candidate tag or all highlighted candidate tags into the current draft without reloading the browser.

## Gemma / Hugging Face VLM path

The tag-selection backend now treats chat/VLM models as real inference models for tag selection. It loads the selected model when needed, runs VLM/LLM chat with the selected media context, parses `tags:` responses, stores a prediction audit row when possible, updates the inference lifecycle circle, and applies add/set/remove/keep-only operations without requiring a page reload.

Hugging Face VLM/text pipeline loading carries through runtime placement options, Hugging Face token, trust-remote-code, dtype, quantization, and max-memory options so load failures are surfaced in the lifecycle/job state rather than appearing as no-ops.

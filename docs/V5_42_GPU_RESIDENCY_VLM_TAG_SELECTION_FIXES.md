# v5.42 GPU Residency, Dropdown, and VLM Tag Selection Fixes

This release is additive on top of v5.40/v5.41. It focuses on making model residency explicit and controllable, preventing polling from interrupting dropdowns, and improving tag-selection workflows in the Tag Editor.

## Model residency and GPU placement

The Models tab now exposes practical per-model controls for local runtime placement:

- Select the exact GPU IDs that may load a model.
- Choose sharding strategy for models that need more than one GPU.
- Set dtype, quantization, runtime engine, tensor parallel size, and max-memory overrides.
- Check the VRAM/placement plan before loading.
- Load and unload models explicitly.
- See loaded placement/reservation status reflected in the model lifecycle/status UI.

The backend validates the requested placement against detected CUDA devices, app-tracked loaded model reservations, loading reservations, and the configured VRAM safety fraction. Placement errors are returned visibly instead of silently doing nothing.

A subtle `cuda:0` bug was fixed: numeric GPU id `0` is now preserved instead of being treated as empty. This is important for single-GPU 3090 setups where the intended target is `cuda:0`.

Built-in no-model helpers such as `dataset-assistant` no longer reserve GPU memory or fail when CUDA is not available.

## Load/unload feedback

Unload requests now go through the same model lifecycle/status layer used by load actions. This lets the circular status indicator show the model moving through an unloading state instead of leaving the user unsure whether VRAM/RAM was released.

## Gemma / Hugging Face VLM loading path

The Hugging Face chat/VLM adapters now pass through additional runtime kwargs needed by modern gated/custom-code models, including token, revision, and `trust_remote_code`. VLM/text outputs are parsed more defensively so nested `generated_text` results from `transformers` pipelines are converted into a normal text response.

The default dtype picker now infers `bfloat16`/`float16` from catalog precision metadata where possible, which avoids unnecessary full-precision loading attempts for models that are expected to fit on one 24 GB GPU.

If a model such as Gemma 4 E4B IT cannot load because PyTorch CUDA is missing, the selected GPU is not torch-ready, the GPU is not detected, or VRAM would be exceeded, the placement/load endpoint now reports the reason through the job/lifecycle path instead of appearing to do nothing.

## Dropdown stability

Automatic polling renders are now deferred while any dropdown/select menu is active. The hold applies globally to model selectors, category selectors, runtime selectors, placement controls, and other select menus, preventing menus from closing a second or two after opening.

## Tag Editor manual tag selection

The Tag Editor tag chip strip now supports manual selection/highlighting:

- Click a tag chip or its toggle to select/deselect it.
- Select all visible tags.
- Deselect all visible tags.
- Invert the current selection.
- Select by category.
- Deselect by category.

Manual selections are tracked per media item and are cleared/pruned when tags are applied, removed, or refreshed.

## LLM/VLM/Assistant tag selection integration

The Tag Editor's "LLM/VLM/Assistant Tag Selection for This Image" card now uses the same selected tag chips as candidate context. Preview/model selections highlight the same chips without needing a page reload. Apply operations refresh the active media row and clear stale drafts so the web component reflects backend-applied tag changes immediately.

Manual candidates are also sent to the backend per media item. A manual-only workflow can apply highlighted tags without forcing a model load, and a chat/VLM workflow receives existing tags plus highlighted/manual candidate tags in the prompt context.

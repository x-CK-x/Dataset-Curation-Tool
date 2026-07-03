# v5.42 GPU Residency, Dropdown Stability, and Manual Tag Selection Fixes

This build extends the v5.41 GPU placement work and fixes the remaining UI/control issues reported during model and Tag Editor testing.

## Dropdown stability

All frontend `select` controls now use a longer render hold while the native dropdown is open. Polling refreshes, tag-score refreshes, model lifecycle updates, and other scheduled renders are deferred instead of closing the dropdown after a few seconds. The hold is released after the dropdown changes or loses focus.

This applies globally to model selectors, category selectors, profile selectors, dataset selectors, kind filters, runtime selectors, and every other dropdown in the app.

## Model GPU residency controls

The Models tab now exposes explicit placement controls per model:

- runtime device (`auto`, `cpu`, `cuda:0`, etc.)
- exact CUDA GPU IDs
- sharding strategy
- dtype
- quantization
- runtime engine
- tensor-parallel size
- optional per-GPU max-memory caps

Before loading, the app can plan VRAM placement against detected GPUs and current app-level reservations. Loading a second model on an already-reserved GPU is blocked if the placement would exceed the configured usable VRAM budget. Unload actions are queued as tracked jobs and clear the app's model residency reservation metadata.

## Manual + model-assisted tag selection

The Tag Editor's ordered tag strip now supports manual highlighting in addition to model-generated preview selections:

- click a chip to highlight/deselect it for assistant tag-selection operations
- drag still reorders tags; small pointer movement starts drag, normal click toggles highlight
- Select All
- Deselect All
- Invert
- Select Category
- Deselect Category

The `LLM/VLM/Assistant Tag Selection for This Image` panel receives the highlighted tags as `candidate_tags`. Enabling **highlighted/manual only** uses those highlights as the exact candidate set for remove/keep/set/add operations.

## VLM/LLM tag-selection execution

Chat/VLM models such as Gemma 4 E4B IT are no longer treated as a no-op heuristic in the Tag Editor. When selected in the LLM/VLM/Assistant Tag Selection panel, the backend now:

1. loads the model if it is not already loaded,
2. builds an image-aware curation prompt with existing tags/categories/manual highlights,
3. runs VLM/LLM inference against the selected image context,
4. parses returned `tags:` suggestions,
5. updates the same lifecycle inference circle,
6. applies add/remove/keep/set operations without requiring a page reload.

This addresses the case where a downloaded Gemma 4 E4B IT model appeared to do nothing when used from the Tag Editor.

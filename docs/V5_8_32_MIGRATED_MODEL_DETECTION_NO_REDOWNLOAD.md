# v5.8.32 — Migrated Model Detection and No-Redownload Load Fix

This release fixes a migration-blocking model-management issue: migrated model folders could appear as downloaded in the Models tab, but clicking **Load Into Memory** could still fall back to a remote Hugging Face repo id and start another download.

## Fix summary

- Model loading now always prefers the concrete local directory returned by `complete_local_dir()` when the catalog already considers the model downloaded.
- Hugging Face cache snapshots migrated from older installs are resolved to the actual snapshot child directory before loading.
- Load and chat paths set `local_files_only=True` when a local migrated model folder is found.
- Local-only loads temporarily set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` while the adapter loads, then restore the prior environment values.
- The WD/PixAI ONNX tagger adapter now obeys local-only mode for `model.onnx` and `selected_tags.csv` resolution instead of calling Hugging Face Hub from the Load path.
- Missing local downloadable models are blocked from implicit load-time download. The user must use **Queue Download/Update** or explicitly allow remote loading.
- The Models tab now includes **Rescan / Reconcile Migrated Models**, which rescans current and external model roots and marks local model payloads as downloaded without fetching anything.

## Additional local-folder layouts now detected

The resolver now handles app-local folders, older alias folders, and Hugging Face cache-style folders including:

```text
models/hf/<repo-or-model-slug>
models/huggingface/<repo-or-model-slug>
models/hub/<repo-or-model-slug>
models/hf/hub/models--org--repo/snapshots/<revision>
models/huggingface/hub/models--org--repo/snapshots/<revision>
models/.cache/huggingface/hub/models--org--repo/snapshots/<revision>
external_model_root/hf/...
external_model_root/huggingface/...
external_model_root/hub/...
```

## Behavioral change

The **Load Into Memory** button is now local-only for downloadable local/catalog models. If no local payload is found, it surfaces a clear error instead of triggering Transformers/Hugging Face Hub to download a new snapshot. Models that are already marked downloaded are forced through their concrete local directory/snapshot path.

The explicit **Queue Download** / **Queue Update** button remains the network/download path.

## Catalog stability guard

The model catalog now de-duplicates candidate model paths with a cheap normalized path key instead of repeatedly resolving hundreds of non-existent aliases through `Path.resolve(strict=False)`. This keeps the Models tab responsive after migration and avoids platform-specific hangs or crashes while the catalog checks many possible migrated-folder layouts.

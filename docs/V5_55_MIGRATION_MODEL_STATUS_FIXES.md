# v5.55 Migration and Model Status Visibility Fixes

This patch focuses on reusable model assets from older installs and making model residency/download status visible anywhere the user chooses a model.

## Model migration repair

The install migration service now treats each model folder under provider roots such as `models/hf/`, `models/huggingface/`, `models/ultralytics/`, `models/checkpoints/`, and other common model-provider folders as its own atomic model asset. This prevents one questionable folder from causing unrelated model folders to be missed.

Migration now tolerates stale downloader files such as `.lock`, `.part`, `.tmp`, and `.download` when the model folder otherwise contains valid non-empty weights. Those transient files are ignored and are not moved/copied/symlinked.

Sharded Hugging Face model folders are validated through common `*.index.json` weight maps. If an index references a missing or zero-byte shard, the model group is skipped as corrupt/incomplete instead of being migrated into the new install.

The scan result now includes a `model_groups` section for model assets so the migration output shows valid and skipped model groups with reasons.

## Easier source-folder selection

If the user accidentally selects `models/hf/` or a specific `models/hf/<repo-safe>` folder as the previous install source, the migration service resolves it back to the install root when possible. This preserves paths such as:

```text
models/hf/fancyfeast--llama-joycaption-beta-one-hf-llava
models/hf/Qwen--Qwen2.5-VL-7B-Instruct
models/hf/Qwen--Qwen3-VL-2B-Instruct
```

## Model status visibility

The model list API now augments each model row with:

```text
download_state
load_state
inference_state
loaded_instance_count
loaded_instances
status_badges
status_summary
```

The Models tab and model dropdown labels now show whether a model is downloaded, not downloaded, needs repair/update, loaded, and how many loaded instances are currently tracked. Native dropdown options also include richer hover text with category, provider, memory estimate, integrity issues, and loaded-instance count.

## Visual changes

The Models tab now includes chips for:

```text
DOWNLOADED
NOT DOWNLOADED
NEEDS REPAIR/UPDATE
LOADED xN
```

The raw model table also shows downloaded/loaded/repair status instead of only a blank or `yes` value.

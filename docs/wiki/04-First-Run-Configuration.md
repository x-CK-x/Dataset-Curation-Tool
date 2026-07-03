# First Run Configuration

<!-- DCT_VISUAL_START -->
![First-run configuration visual guide](assets/images/first_run_configuration.png)
<!-- DCT_VISUAL_END -->


Use this page after installation and before serious curation work.

## Settings tab checklist

Open **Settings** and review these areas.

### General paths

Confirm output and runtime paths are writable. The default project layout uses:

```text
runtime/
models/
outputs/
```

Large model storage can be moved with symlinks. See [Install Migration and Symlinks](13-Install-Migration-and-Symlinks.md).

### Tag profile

Pick the tag profile that matches your dataset source. Typical profiles include booru-style profiles such as `e621` when using e621/e926 tag dictionaries.

The tag profile affects:

- Autocomplete suggestions.
- Category colors.
- Alias/implication behavior.
- Tag sorting.
- Assistant tag-selection context.

### Startup tag DB sync

The app can sync booru DB exports on startup so autocomplete and category coloring are available before import.

Recommended behavior when testing many builds:

1. Disable or stop startup sync when you plan to migrate from a previous install.
2. Use **Install Migration** to move/copy cached `runtime/tag_exports/` files.
3. Refresh the tag dictionary status.
4. Only re-download exports when the cache is missing or stale.

### Token profiles

Use named token profiles instead of pasting tokens repeatedly.

Supported profile groups include:

- Hugging Face.
- OpenRouter.
- OpenAI.
- Anthropic.
- xAI.
- RunPod.
- Vast.ai.
- Lambda Labs.

Use separate profiles for personal, testing, and production-like runs.

### Model download mode

For large models, use serial queue mode:

```text
Serial queue: one model file transfer at a time
```

Use parallel transfers only when the network and host can support multiple large transfers without corruption, throttling, or bandwidth contention.

### GPU and VRAM behavior

The tool reports:

- Physical GPU VRAM.
- Driver-reported free VRAM.
- App-reserved VRAM.
- Model placement estimates.
- Loaded instances.

Before loading a model, inspect the model card memory estimate and the selected GPU placement plan.

## Models tab first-run checklist

1. Press refresh/rescan.
2. Confirm downloaded models show `DOWNLOADED`.
3. Confirm incomplete models do not incorrectly show as complete.
4. Pick GPU IDs before loading.
5. Use quantization for models too large for a single GPU.
6. Use unload when finished.

## Tag Dictionaries first-run checklist

1. Pick the tag profile.
2. Check dictionary status.
3. Import default DB export or migrate cached exports.
4. Verify autocomplete works in Tag Editor.
5. Verify category colors show in tag chips.

## Jobs tab first-run checklist

Learn these controls early:

- Pause Downloads.
- Resume Downloads.
- Stop Checked Jobs.
- Retry from scratch.
- Copy error.
- Open full job details.

See [Jobs, Queues, and Troubleshooting](15-Jobs-Queues-and-Troubleshooting.md).

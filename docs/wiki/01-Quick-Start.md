# Quick Start

<!-- DCT_VISUAL_START -->
![Quick Start visual guide](assets/images/quick_start_overview.png)
<!-- DCT_VISUAL_END -->


This page gets a new user from a downloaded ZIP to the first usable curation session.

## 1. Extract the ZIP

Extract the release ZIP somewhere with a short path, for example:

```text
C:\Users\<you>\Desktop\DataCurationToolModern
```

Avoid extremely deep paths because Windows path-length issues can affect model folders and Hugging Face snapshots.

## 2. Install

On Windows:

```bat
install.bat
```

On Linux:

```bash
chmod +x install.sh run.sh update.sh
./install.sh
```

The scripts are intended to locate Conda, create or activate the `data-curation-tool` environment, and install the application dependencies.

## 3. Verify GPU support

Run:

Windows:

```bat
verify_gpu.bat
```

Linux:

```bash
./verify_gpu.sh
```

Expected result for CUDA mode:

- Python can import `torch`.
- `torch.cuda.is_available()` is true.
- NVIDIA GPUs are listed with their names and memory.

When CUDA is not detected, use the repair scripts from [Windows Installation](02-Installation-Windows.md) or [Linux Installation](03-Installation-Linux.md).

## 4. Run the app

Windows:

```bat
run.bat
```

Linux:

```bash
./run.sh
```

Open the browser to:

```text
http://127.0.0.1:7865
```

The run script normally opens a browser automatically.

## 5. Configure first-run basics

Open [Settings](04-First-Run-Configuration.md) and check:

- Tag profile, usually `e621` or the profile relevant to your dataset.
- Token profiles for Hugging Face/OpenRouter/cloud providers if needed.
- Startup tag DB sync behavior.
- Model download queue mode.
- GPU/device detection.

## 6. Import images

Go to **Import**.

Recommended first import:

1. Pick a small test folder.
2. Enable metadata extraction if you want tags/captions from existing files.
3. Start import.
4. Watch **Jobs** until it completes.

Then open **Gallery** and select images.

## 7. Edit tags

Go to **Tag Editor**.

Common first actions:

- Select an image.
- Inspect tags and category colors.
- Add or remove tags manually.
- Use autocomplete to normalize tags.
- Run a model or assistant preview before applying changes.
- Save the updated tags/caption.

## 8. Download or migrate models

Best first workflow when you already used older builds:

1. Open **Install Migration**.
2. Add one or more previous install folders.
3. Scan.
4. Move or copy models and tag export caches.
5. Open **Models** and press refresh/rescan.

For new downloads:

1. Open **Models**.
2. Choose serial queue mode for very large models.
3. Queue a model download.
4. Watch the model progress circles or the Jobs tab.
5. Load the model onto the selected GPU(s).
6. Use unload when done to free VRAM.

See [Models, Downloads, and GPU Placement](08-Models-Downloads-and-GPU-Placement.md).

## 9. Use the assistant

The assistant can be used in the **Assistant** tab, **Tag Editor**, **Compare**, **Batch Tags**, and other assistant-enabled surfaces.

Typical prompts:

```text
Look at the current image and validate which existing tags are visible.
```

```text
Suggest missing tags, but do not apply them yet.
```

```text
Prune tags that are not actually visible in the image.
```

```text
Write a concise caption for this image using the current tags as context.
```

The chat interface keeps history, supports message editing/deletion, and can condense old context into memory when needed. See [Assistant, Orchestrator, and Chat](09-Assistant-Orchestrator-and-Chat.md).

## 10. When something fails

Open **Jobs** and inspect the failed job.

Useful controls:

- Retry failed download from scratch.
- Stop checked jobs.
- Pause/resume downloads.
- Copy error details.
- Open full logs.

See [Jobs, Queues, and Troubleshooting](15-Jobs-Queues-and-Troubleshooting.md).

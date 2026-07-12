# Windows Installation

<!-- DCT_VISUAL_START -->
![Windows installation visual guide](assets/images/windows_installation.png)
<!-- DCT_VISUAL_END -->


This page documents the Windows setup path.

## Requirements

Recommended:

- Windows 10 or Windows 11.
- A recent NVIDIA driver for CUDA workflows.
- Miniconda or Anaconda installed for the current user.
- Enough disk space for models, tag DB exports, runtime cache, and imported datasets.

The scripts target the Conda environment:

```text
data-curation-tool
```

## Install

From the project root:

```bat
install.bat
```

The installer should:

1. Locate Conda from common user-level install paths.
2. Initialize Conda for the script session.
3. Create or update the `data-curation-tool` environment.
4. Install dependencies from the environment and requirements files.
5. Install the project in editable mode where applicable.

## Run

```bat
run.bat
```

The run script should activate the environment automatically and start the server. The app usually binds to:

```text
http://127.0.0.1:7865
```

## Update

```bat
update.bat
```

Use this after replacing the code with a newer build or when dependencies changed.

## GPU/CUDA checks

Run:

```bat
verify_gpu.bat
```

A healthy CUDA install should show:

- `torch` import success.
- CUDA available.
- GPU count.
- Device names.
- VRAM totals.

If CUDA is missing or CPU-only torch was installed, run one of these:

```bat
install_torch_cuda128.bat
```

or:

```bat
repair_cuda_torch.bat
```

For CPU-only usage:

```bat
install_torch_cpu.bat
```

## Optional installers

These scripts install optional feature groups:

| Script | Purpose |
| --- | --- |
| `install_annotation_models.bat` | General annotation model dependencies. |
| `install_sam_runtime.bat` | SAM/SAM-style segmentation runtime support. |
| `install_pose_models.bat` | Pose model support. |
| `install_image_tools.bat` | External image/upscale/tool integrations. |
| `install_geckodriver.bat` | Firefox geckodriver for Source Browser. |
| `install_jtp3_runtime.bat` | JTP-3 tag/rating model runtime support. |
| `install_hydra_runtime_deps.bat` | RedRocket Hydra 3.5 local inference runtime (`pyvips`/`libvips`) repair. |
| `install_flexavatar.bat` | Isolated FlexAvatar runtime. |

## Stop the server

Use:

```bat
stop.bat
```

Or press `CTRL+C` in the terminal that is running the server.

## Common Windows issues

### Browser opens but the GUI is blank

Open browser dev tools and check the Console. Blank pages are usually frontend JavaScript errors. Current builds include module-aware frontend validation, but old browser cache can still show stale assets. Hard refresh with `CTRL+F5`.

### Conda is not found

Confirm Conda exists under a user-level path such as:

```text
C:\Users\<you>\miniconda3
C:\Users\<you>\anaconda3
C:\Users\<you>\.conda
```

The scripts include helpers under `scripts/`, including Conda discovery and activation helpers.

### CUDA is visible in Task Manager but not in PyTorch

Task Manager and PyTorch use different detection paths. Run `verify_gpu.bat`; if PyTorch reports CUDA unavailable, repair the torch install with `repair_cuda_torch.bat` or `install_torch_cuda128.bat`.

### Long paths break model folders

Keep the project near the root of a drive, for example:

```text
D:\DCT\DataCurationToolModern
```

Use [symlinks](13-Install-Migration-and-Symlinks.md) if the models need to live on a large drive.

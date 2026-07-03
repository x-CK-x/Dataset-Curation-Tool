# Linux Installation

<!-- DCT_VISUAL_START -->
![Linux installation and first-run visual guide](assets/images/quick_start_overview.png)
<!-- DCT_VISUAL_END -->


This page documents Linux setup.

## Requirements

Recommended:

- A modern Ubuntu-based distribution or another Linux distribution with Conda support.
- Miniconda or Anaconda.
- NVIDIA driver and CUDA-capable PyTorch for GPU workflows.
- Sufficient disk space for model snapshots and runtime files.

## Install

From the project root:

```bash
chmod +x install.sh run.sh update.sh stop.sh
./install.sh
```

The installer should create or update the Conda environment:

```text
data-curation-tool
```

## Run

```bash
./run.sh
```

Open:

```text
http://127.0.0.1:7865
```

## Update

```bash
./update.sh
```

## Verify GPU support

```bash
./verify_gpu.sh
```

A healthy GPU setup should report CUDA available from PyTorch and list the detected NVIDIA GPUs.

## Optional installers

| Script | Purpose |
| --- | --- |
| `install_annotation_models.sh` | General annotation model dependencies. |
| `install_sam_runtime.sh` | SAM/SAM-style segmentation runtime support. |
| `install_pose_models.sh` | Pose model support. |
| `install_image_tools.sh` | External image/upscale/tool integrations. |
| `install_geckodriver.sh` | Firefox geckodriver for Source Browser. |
| `install_jtp3_runtime.sh` | JTP-3 tag/rating model runtime support. |
| `install_flexavatar.sh` | Isolated FlexAvatar runtime. |

## Stop the server

```bash
./stop.sh
```

Or press `CTRL+C` in the terminal that is running the server.

## Permissions

Do not place the project inside a folder that requires root for normal writes. The app writes to:

- `runtime/`
- `models/`
- selected output folders
- imported dataset/database paths

## Linux symlinks

To place models on another drive:

```bash
mkdir -p /mnt/bigdrive/DCT-models
mv models/hf /mnt/bigdrive/DCT-models/hf
ln -s /mnt/bigdrive/DCT-models/hf models/hf
```

More detail is in [Install Migration and Symlinks](13-Install-Migration-and-Symlinks.md).

# Migration Notes

This version moves the application to a Conda-first FastAPI architecture with a local browser HUD.

## Important changes

- The old UI runtime is no longer required.
- The environment name is `data-curation-tool`.
- The installer no longer uses `venv`; it creates or updates the Conda environment from `environment.yml`.
- PyTorch is installed separately by the install scripts so the correct CUDA/CPU wheel can be chosen.
- Dataset folders can be selected through the HUD with native folder picker buttons.
- Tag category information is no longer displayed by grouping tags into separate blocks. Tags stay in one ordered strip and are color-coded by category.
- Downloader source support is now plugin-style and requires an explicit authorization confirmation before running.
- Local LLM/VLM chat is exposed through the Assistant tab and `/api/models/chat`.

## Torch modes

```text
DCT_INSTALL_TORCH=auto   # default; CUDA 12.8 if NVIDIA is detected, otherwise skip
DCT_INSTALL_TORCH=cu128  # force CUDA 12.8 PyTorch wheels
DCT_INSTALL_TORCH=cpu    # force CPU PyTorch wheels
DCT_INSTALL_TORCH=skip   # skip PyTorch
```

## Validate GPU setup

```bat
verify_gpu.bat
```

```bash
./verify_gpu.sh
```

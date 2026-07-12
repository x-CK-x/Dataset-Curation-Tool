# Hydra Runtime Dependency Fix

![Model lifecycle and GPU dashboard](assets/images/model_lifecycle_and_gpu_dashboard.png)

Hydra 3.5 local inference depends on both the Python `pyvips` package and the native `libvips` shared libraries.  v5.8.4 adds those dependencies to the Conda environment and adds repair scripts for existing installs.

## Symptoms fixed

The fixed error looked like this:

```text
ModuleNotFoundError: No module named 'pyvips'
```

or, on some systems, a DLL/shared-library error while importing `pyvips`.

## Fresh install

Run the normal installer again:

```bat
install.bat
```

```bash
./install.sh
```

The Conda environment now includes:

```text
pyvips
libvips
```

## Existing install repair

Use the targeted repair script:

```bat
install_hydra_runtime_deps.bat
```

```bash
./install_hydra_runtime_deps.sh
```

Manual equivalent:

```bash
conda install -n data-curation-tool -c conda-forge pyvips libvips
```

## What the app does now

Before launching Hydra's native `inference.py`, the adapter checks for:

| Dependency | Purpose |
|---|---|
| `torch` / `torchvision` | model execution |
| `timm` | SigLIP/vision-model support |
| `einops` | tensor operations |
| `safetensors` | Hydra model weights |
| `pyvips` + `libvips` | image loading/preprocessing |

If a dependency is missing, the app now reports the missing package before the subprocess runs.

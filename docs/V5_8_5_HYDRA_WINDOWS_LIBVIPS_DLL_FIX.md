# v5.8.5 — Hydra Windows libvips DLL / Auto-Repair Fix

This release fixes the Hydra 3.5 load-time failure where `pyvips` exists but Windows cannot locate or load `libvips-42.dll`.

## Failure fixed

```text
Hydra 3.5 runtime dependencies are missing ...
pyvips + libvips (cannot load library 'libvips-42.dll': error 0x7e)
```

## What changed

- Hydra load now runs a runtime dependency check before marking the model loaded.
- If `pyvips`/`libvips` is missing, the Hydra adapter now attempts an in-environment repair by installing:
  - `pyvips[binary]>=3.0.0`
  - `pyvips-binary>=8.16.0`
  - `cffi>=1.17.1`
- If the pip binary repair is not enough and Conda is visible, the adapter also attempts:

```bash
conda install -n data-curation-tool -c conda-forge pyvips libvips cffi
```

- Windows DLL search handling now keeps `os.add_dll_directory()` handles alive for the process lifetime.
- The libvips search path now includes:
  - active Conda `Library/bin`
  - common user Conda environment paths
  - existing `PATH` entries containing libvips
  - manual `VIPS_HOME`, `VIPSHOME`, `LIBVIPS_HOME`, `LIBVIPS_DIR`
  - `pyvips-binary` site-package locations
- `install.bat`, `update.bat`, `install.sh`, and `update.sh` now run the Hydra repair helper after core dependency checks.
- `install_hydra_runtime_deps.bat/.sh` now route through the same repair helper.
- Added `scripts/repair_hydra_runtime_dependencies.py` for targeted repair.

## Existing install repair

For an existing Windows install, run:

```bat
install_hydra_runtime_deps.bat
```

or:

```bat
update.bat
```

Then restart the app before loading Hydra again.

## Disable auto-repair during model load

Set this environment variable before starting the app:

```bat
set DCT_HYDRA_AUTO_REPAIR=0
```

This keeps the load operation diagnostic-only for locked-down/offline environments.

## Manual fallback

```bat
conda activate data-curation-tool
python -m pip install "pyvips[binary]>=3.0.0" pyvips-binary>=8.16.0 cffi>=1.17.1
python scripts\check_hydra_runtime_dependencies.py
```

Hydra itself is unchanged. This fix only changes how the application prepares and repairs the Python/native image-runtime dependency chain needed by Hydra.

# v5.8.4 — Hydra Runtime Dependency Fix

This release fixes local RedRocket Hydra 3.5 inference failures caused by missing `pyvips`/`libvips` runtime dependencies.

## What changed

- Added `pyvips` and `libvips` to `environment.yml`.
- Added `install_hydra_runtime_deps.bat` and `install_hydra_runtime_deps.sh` for repairing existing installs.
- Added `scripts/check_hydra_runtime_dependencies.py` for dependency verification.
- Added a preflight dependency check inside the Hydra adapter so missing image-runtime dependencies fail with an actionable message before `inference.py` is launched.
- Added Windows DLL/search-path preparation for Conda `Library/bin`, manual `VIPS_HOME`/`VIPSHOME`, and `LIBVIPS_*` installs.

## Existing environment repair

On Windows:

```bat
install_hydra_runtime_deps.bat
```

On Linux/macOS:

```bash
./install_hydra_runtime_deps.sh
```

Manual Conda repair:

```bash
conda install -n data-curation-tool -c conda-forge pyvips libvips
```

Then rerun Hydra inference from the Models, Tag Editor, Batch, Compare, or Annotation surfaces.

## Why this is needed

Hydra's native repository imports `pyvips` for image loading/preprocessing.  The Python package alone is not always enough on Windows because the underlying libvips DLLs/shared libraries must also be available to the Python process.  Installing through Conda is the preferred path for this tool because Conda can install the Python binding and native shared-library dependency together.

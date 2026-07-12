# Hydra Windows libvips DLL Fix

Hydra 3.5 uses `pyvips` for image loading/preprocessing. On some Windows installs, `pyvips` is present but Python cannot locate or load `libvips-42.dll`.

## Recommended repair

Run:

```bat
install_hydra_runtime_deps.bat
```

or:

```bat
update.bat
```

Then restart the app.

## What the repair does

The repair helper first installs the pip binary fallback:

```bat
python -m pip install "pyvips[binary]>=3.0.0" pyvips-binary>=8.16.0 cffi>=1.17.1
```

If Conda is visible and the binary fallback is still not loadable, it also tries:

```bat
conda install -n data-curation-tool -c conda-forge pyvips libvips cffi
```

## Runtime behavior

When Hydra is loaded locally, the app now:

1. prepares Conda/manual/libvips DLL search paths,
2. checks `pyvips`/`libvips`,
3. attempts an automatic in-environment repair when allowed,
4. re-checks the runtime,
5. loads Hydra only after the dependency chain is valid.

To disable model-load auto-repair, start the app with:

```bat
set DCT_HYDRA_AUTO_REPAIR=0
```

Remote Hydra service mode does not require local `pyvips` or local Hydra weights on the controller machine.

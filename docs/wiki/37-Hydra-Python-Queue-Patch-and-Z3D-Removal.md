# Hydra Python Queue Patch and Z3D Removal

v5.8.6 fixes a local RedRocket Hydra 3.5 inference failure and removes an unavailable legacy tagger.

## Hydra queue-annotation failure

If Hydra fails with the following error:

```text
TypeError: type 'Queue' is not subscriptable
```

then Python is evaluating a runtime annotation in the downloaded Hydra source before inference can start. The Data Curation Tool now automatically patches the downloaded Hydra source file during load/inference.

Patched source:

```text
models/hf/RedRocket--Hydra/utils/loader.py
```

The app rewrites queue annotations only:

| Before | After |
|---|---|
| `MpQueue[str]` | `MpQueue` |
| `Queue[int]` | `Queue` |
| `mp.Queue[str]` | `mp.Queue` |
| `multiprocessing.Queue[str]` | `multiprocessing.Queue` |

The original source is preserved as:

```text
loader.py.dctbak
```

The marker file is:

```text
.dct_hydra_py311_queue_patch.json
```

## What this does not change

- It does not edit Hydra model weights.
- It does not edit Hydra tag metadata.
- It does not edit user datasets.
- It does not affect remote Hydra service mode unless the remote machine is also running this app code and loading a local Hydra repo.

## Removed unavailable legacy tagger

The Z3D/Zack3D legacy model entry is no longer shown in the Models catalog because the asset is unavailable. Existing local files are not deleted automatically, but the app no longer advertises or downloads the row.

Remaining legacy taggers:

| Model | Source family |
|---|---|
| Thouph EVA02-CLIP ViT-Large 7704 | e621 tagger |
| Thouph EVA02 ViT-Large 448 8046 | e621 tagger/rating labels |
| Thouph Experimental EfficientNetV2-M 8035 | e621 tagger |

## Recommended action

Update to v5.8.6 and run Hydra again. No Hydra model re-download should be required. If the Hydra runtime dependency repair has not been run yet, run `update.bat` or `install_hydra_runtime_deps.bat` first.

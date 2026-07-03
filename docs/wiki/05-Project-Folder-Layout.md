# Project Folder Layout

<!-- DCT_VISUAL_START -->
![Project folder layout and migration visual guide](assets/images/project_folder_layout_migration.png)
<!-- DCT_VISUAL_END -->


This page explains where the app stores code, models, runtime state, and generated files.

## Top-level files

| Path | Purpose |
| --- | --- |
| `README.md` | Release notes and quick project summary. |
| `environment.yml` | Conda dependency definition. |
| `requirements.txt` | Pip dependency fallback/supplement. |
| `install.bat` / `install.sh` | Install the app environment. |
| `run.bat` / `run.sh` | Launch the app. |
| `update.bat` / `update.sh` | Update dependencies and editable install. |
| `stop.bat` / `stop.sh` | Stop the app server. |
| `verify_gpu.bat` / `verify_gpu.sh` | Check PyTorch/CUDA/GPU status. |

## Important directories

| Path | Purpose |
| --- | --- |
| `data_curation_tool/` | Main Python application package. |
| `data_curation_tool/static/` | Frontend JavaScript and CSS. |
| `docs/` | Release notes and developer documentation. |
| `docs/wiki/` | GitHub-wiki-ready user and developer docs. |
| `integrations/` | Optional integration assets. |
| `models/` | Local model files and downloaded snapshots. |
| `runtime/` | App database, settings, tag exports, cache, and state. |
| `scripts/` | Helper scripts. |
| `tests/` | Regression tests. |

## Models folder

Common model locations:

| Path | Purpose |
| --- | --- |
| `models/hf/` | Hugging Face snapshots. |
| `models/ultralytics/` | YOLO/Ultralytics-style model files. |
| `models/checkpoints/` | Generic checkpoint files. |
| `models/custom/` | User-added custom models. |
| `models/annotation/` | Annotation model checkpoints. |

Hugging Face local folder names are usually normalized from repo IDs, for example:

```text
models/hf/Qwen--Qwen2.5-VL-7B-Instruct
models/hf/microsoft--Florence-2-large
models/hf/fancyfeast--llama-joycaption-beta-one-hf-llava
```

## Runtime folder

Common runtime files:

| Path | Purpose |
| --- | --- |
| `runtime/app.db` | Main SQLite database. |
| `runtime/settings.json` | User settings and token profile references. |
| `runtime/custom_models.json` | Custom model catalog. |
| `runtime/custom_tags.json` | User-defined custom tags. |
| `runtime/tag_exports/` | Cached booru DB export files. |
| `runtime/download_cache/` | Download-related cache. |

## Outputs

Output folders depend on the feature used. Examples include:

- Import results.
- Downloaded media datasets.
- Annotation exports.
- Media extraction outputs.
- Code Assistant backups under `.dct_code_backups/` inside a target project.

## Backup priority

When backing up or migrating an install, prioritize:

1. `models/`
2. `runtime/tag_exports/`
3. `runtime/app.db`
4. `runtime/settings.json`
5. `runtime/custom_models.json`
6. `runtime/custom_tags.json`
7. project-specific outputs or datasets you created

Use [Install Migration and Symlinks](13-Install-Migration-and-Symlinks.md) for moving assets between builds.

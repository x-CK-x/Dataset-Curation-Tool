# v5.48 Custom Model Catalog + CV Registry + Migration Validation

This build adds a stricter custom-model catalog workflow and expands the built-in computer-vision model registry.

## Custom model catalog changes

- User-added custom models must include a model category before they can be saved.
- Supported categories include `classifier`, `tagger`, `rating`, `captioner`, `llm`, `vlm`, `detection`, `segmentation`, `embedding`, `pose2d`, `pose3d`, `upscaler`, `external_image_tool`, and `custom`.
- Custom models are marked with `user_custom=true` and `custom=true` in `/api/models`.
- Custom models expose both `custom_category` and `custom_model_category` for frontend compatibility.
- Custom models are sorted above built-in catalog rows in model lists and dropdowns.
- Custom model cards and menu options use a distinct custom-model visual style.
- Custom model rows are mirrored into both:
  - `runtime/settings.json` under `custom_models`
  - `runtime/custom_models.json`

## Modern CV registry expansion

Added additional catalog rows for modern classification, detection, and segmentation families, including:

- EfficientNet / EfficientNetV2 timm classifier rows.
- ConvNeXt V2 and Swin V2 classifier rows.
- DINOv3 visual backbone/embedding row.
- YOLO26 detection and segmentation contract rows.
- RT-DETR / RT-DETRv2 detection row.
- Grounding DINO open-vocabulary detection row.
- RF-DETR / D-FINE detection contract rows.
- Florence-2 multitask vision-language row.
- Mask2Former, OneFormer, SegFormer, and SAM3/SAM2-style segmentation contract rows.

Some rows are direct downloadable Hugging Face/Ultralytics entries; others are explicit runtime-contract rows so they are visible in the UI before their specialized adapter is fully implemented.

## Migration fixes

Model migration now treats each model folder/file as an atomic asset group. For example:

- `models/hf/<repo-safe-name>/...`
- `models/ultralytics/<weights>.pt`
- `models/checkpoints/<name>/...`
- `models/custom/<name>/...`

A group is moved/copied only when it looks complete. Corrupt or incomplete groups are skipped when they contain partial/temp files or zero-byte weights, or when no recognizable checkpoint/weight file exists.

Downloader metadata folders such as `.cache` are ignored for model validity so completed Hugging Face local-dir downloads are not falsely marked corrupt just because old cache metadata exists.

## API/UI additions

- `POST /api/models/custom` saves/updates a custom model row.
- `DELETE /api/models/custom/{model_name}` removes a user custom row.
- The Models tab now includes an "Add Custom Model to Catalog" card.
- User custom rows get a custom chip and custom model-card styling.

## Validation

Targeted validation included:

```bash
python -m py_compile data_curation_tool/models/registry.py \
                     data_curation_tool/services/model_service.py \
                     data_curation_tool/routers/models.py \
                     data_curation_tool/services/install_migration_service.py \
                     data_curation_tool/routers/migration.py \
                     data_curation_tool/app.py \
                     data_curation_tool/config.py \
                     data_curation_tool/schemas.py

node --check data_curation_tool/static/app.js

pytest -q tests/test_api_smoke.py \
          tests/test_v524_model_browser_audit.py \
          tests/test_v519_annotation_download_regressions.py \
          tests/test_v535_metadata_model_chat_audit.py \
          tests/test_v536_downloader_all_posts_dedupe.py \
          tests/test_v537_model_lifecycle_status.py \
          tests/test_v538_stability_regressions.py \
          tests/test_v539_model_tag_refresh_focus.py \
          tests/test_v540_migration_dropdown.py \
          tests/test_v541_gpu_placement_controls.py \
          tests/test_v542_dropdown_manual_vlm_selection.py \
          tests/test_v544_stop_downloads_conda_scripts.py \
          tests/test_v545_configurable_assistant_orchestrator.py \
          tests/test_v546_job_cancel_retry_controls.py \
          tests/test_v547_refresh_vlm_logs_sort.py \
          tests/test_v548_custom_models_cv_registry_migration.py
```

# 73 — Thumbnails, Multiselect, Booru Reset, Integrity Classifiers

v5.8.43 improves visible UI responsiveness and adds an integrity-check workflow.

## Gallery thumbnails

Gallery tiles now render immediately with a lightweight placeholder while thumbnails are generated in the background. When a thumbnail becomes available, the frontend replaces the placeholder in place. The backend also has an optional OpenCV/CUDA resize path for systems that expose CUDA-enabled OpenCV.

## Quick Tag model selection

The multi-model selector now supports:

- Ctrl/Cmd-click to toggle selected models.
- Shift-click to select a range.
- Ctrl/Cmd+A to select all models in the menu.

Queue buttons now use all highlighted rows.

## Booru tag reset

Single-image and batch booru tag reset actions now queue a visible job. The job refreshes local `.download.json` metadata, replaces tags with fresh source-site tags, and writes failures to `runtime/booru_tag_resets/`.

## Nightshade / Glaze integrity checks

The Models tab contains a new card for registering local EfficientNet/EfficientNetV2 integrity classifier profiles with labels. The Tag Editor and Batch Tags tabs can queue those profiles against current media. Results are stored as prediction metadata and optional safety tags.

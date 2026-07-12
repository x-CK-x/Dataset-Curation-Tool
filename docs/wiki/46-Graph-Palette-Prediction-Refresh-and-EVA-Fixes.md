# Graph Palette, Prediction Refresh, and EVA Fixes

v5.8.16 improves the Agentic Graph Editor and model-result review behavior.

## Palette-driven graph node customization

The graph node palette is now treated as a real contract instead of only a flat reference table. Each node type can define:

- category
- input/output port metadata
- input/output modality metadata
- default config
- workflow-step mapping
- standalone graph-editor equivalent
- customization sections and fields

The node inspector includes a **Palette-driven customization** section so graph-specific node options are editable without manually editing raw JSON. The raw JSON remains available for advanced edits and model-assisted graph refinement.

## Node families covered

The palette includes standalone-style nodes for text, image, audio, video, bundle/context packing, model calls, supervisor/controller planning, external tool calls, event publishing, webhooks, live streams, conditions, fan-out, joins, browser search/open MCP actions, and output artifacts.

## Faster prediction visibility after inference

When a quick model inference job completes, the frontend now polls that specific job, invalidates tag-score caches, refreshes affected media rows when tags/captions were applied, reloads prediction-score rows, and re-renders the current surface.

This specifically helps the Tag Editor hover cards show new model predictions shortly after the job completes.

## Model score colors

Per-model prediction rows now use stable dynamic color variables. The hover panel avoids local color collisions for multiple models on the same tag and keeps the average row visually distinct.

## Legacy EVA/TIMM compatibility

Legacy EVA taggers now get additional neutral compatibility defaults for newer `timm` forward paths, including `no_embed_class`, `num_prefix_tokens`, and rope-related nullable fields.

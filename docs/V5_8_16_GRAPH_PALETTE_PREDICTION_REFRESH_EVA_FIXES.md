# v5.8.16 Graph Palette, Prediction Refresh, and EVA Compatibility Fixes

This release tightens three areas that were reported during live use.

## Agentic Graph Editor node palette

The node palette now exposes backend-owned customization schemas for the standalone-style node families. The GUI, saved graph JSON, and assistant/orchestrator model prompts all reference the same node contracts.

Added/confirmed palette-driven customization coverage for:

- text/image/audio/video input nodes
- live stream placeholders
- bundle/context packers
- model call nodes
- supervisor/controller nodes
- external HTTP/tool gateway nodes
- event and webhook nodes
- condition, fan-out, and join nodes
- browser search/open MCP nodes
- output artifact nodes

The Agentic Graph Editor now shows grouped palette cards with category, port, workflow-step, standalone-equivalent, and custom-field metadata. Nodes added from the palette carry their default config, port metadata, modality metadata, approval defaults, and workflow mapping.

## Tag prediction refresh after inference

Model inference completion now refreshes prediction scores even when a run does not mutate tags/captions. The UI polls the queued model job directly after the user starts a quick inference run, then invalidates the tag-score cache, refreshes affected media rows when needed, reloads tag scores, and re-renders the current review surface.

This is intended to avoid the previous state where the model job reached 100%, but the Tag Editor chip hover cards took too long to show new prediction rows.

## Unique per-model prediction colors

Prediction score rows now use per-model CSS variables generated from stable model-name hashes with local collision avoidance. Multi-model hover cards should no longer reuse the same color for different models in the same hover panel. The average row remains visually distinct.

## Legacy EVA compatibility

Legacy EVA/TIMM pickle compatibility now includes additional neutral defaults such as `no_embed_class`, `num_prefix_tokens`, and rope-related nullable attributes. This is intended to prevent one-missing-attribute-at-a-time inference failures on older pickled EVA taggers under newer `timm` versions.

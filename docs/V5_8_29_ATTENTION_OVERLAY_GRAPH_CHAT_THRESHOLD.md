# v5.8.29 — Inline Attention Overlays, Graph Editor Interaction Fixes, Graph Chat, and 0.70 Tagger Thresholds

## Summary

This patch preserves the v5.8.28 Thouph preprocessing, scroll/dropdown, prediction-sort, multimodal-builder, and LingBot world-model additions, then adds a focused v5.8.29 update for review workflows and the Agentic Graph Editor.

## Tag Editor and Compare attention overlays

The standalone Attention Visualizer remains the correct place for visualizations that need their own spatial or abstract review surface, such as embedding maps, t-SNE/projection outputs, clustering, and non-image scatter views.

The heatmap-style methods that naturally align with image pixels are now available inside the review tabs:

- Tag Editor
- Image Compare

The inline overlay controls support:

- method selection for heatmap-capable methods only
- optional compatible model selection
- tag/token/prompt field
- opacity slider
- blend-mode selector
- show/hide toggle
- create/refresh heatmap button
- clear heatmap button

The backend now writes both:

- a composite overlay PNG for the standalone Attention Visualizer
- a transparent heatmap PNG intended for semi-transparent frontend overlay

The frontend uses the transparent heatmap layer over the original image preview, so the user can toggle it off without losing the original image view.

## Default tagger threshold

The default classifier/tagger threshold is now **0.70** across the app-level settings, frontend controls, model run request schemas, orchestration step schema, and legacy Thouph tagger configs.

Detection/segmentation thresholds that are spatial-annotation-specific remain separate where they intentionally use lower defaults.

## Agentic Graph Editor fixes

The Graph Editor canvas now avoids full page-scroll jumps by preserving UI state during canvas-local renders. This targets the reported bug where right-clicking the graph or clicking a node reset the page scrollbar to the top.

The node/context-menu behavior was updated:

- clicking empty canvas while a menu is open closes it
- right-clicking a node opens node actions instead of the generic canvas palette
- double-left-clicking a node opens the expanded node properties panel
- double-left-clicking empty canvas opens the node palette
- context menus are attached to graph world coordinates, so they pan and zoom with the canvas

The Graph Editor top controls now expose explicit buttons for:

- Save Graph
- Edit Graph
- Remove Graph
- Open Linked Graph Chat

The node inspector now supports:

- Minimize
- Normal
- Maximize
- Close Panel

## Agentic Graph Chat

A new **Agentic Graph Chat** tab is linked directly to the graph canvas. It sends the current graph JSON, selected node, selected media IDs, dataset/runtime settings, and graph event-log tail as context.

It supports:

- graph-linked conversation history
- model/runtime controls
- visible plan/action trace controls
- approved local tool/COA parsing
- saved graph-chat state
- conversation memory clearing/editing/branching through the existing chat panel

The implementation exposes user-visible planning, assumptions, tool/action traces, and verification notes. It does not expose private hidden chain-of-thought.

## Validation

Validated with:

```text
python -m compileall -q data_curation_tool integrations scripts tests
node --check data_curation_tool/static/app.js
bash -n install.sh update.sh
pytest -q tests/test_v621_thouph_preprocess_scroll_graph_sort_world_models.py tests/test_v622_attention_overlay_graph_chat_threshold.py
```

# v5.8.31 Graph Selection, Node Menu, WD/PixAI Loader Fixes

v5.8.31 improves large-graph editing and fixes several model-loader/UI regressions.

## Graph editor

- Ctrl+drag draws a selection box around nodes and edges.
- Selected node chunks can be moved together.
- Ctrl+C, Ctrl+X, and Ctrl+V copy, cut, and paste graph fragments.
- The node palette has search, colored category filters, and the last three used nodes.
- Scrolling inside the palette scrolls the palette, not the canvas.
- Right-click opens the node menu at the cursor in canvas coordinates.
- Nodes with many inputs/outputs now render multiple ports and preserve port-level edges.

## New graph template

The graph catalog includes `closed_loop_model_training_improvement_graph`, a generic model-training improvement loop for collection, tagging/captioning, branch QA, export, trainer handoff, generated-output evaluation, assistant-proposed branch/hyperparameter changes, and human approval.

The attached sample workflow is included as:

```text
docs/examples/agentic_closed_loop_training_curation_graph_sample.json
```

## Attention Visualizer

The Attention Visualizer now has the same tag suggestion/autocomplete control style used by the Tag Editor.

## Augment tab

The missing `exportCard()` render helper is restored, so the Augment tab no longer fails to render.

## WD/PixAI taggers

The rows that previously failed with `Model adapter is not available` now use a new isolated ONNX adapter:

- PixAI Tagger v0.9
- WD ConvNeXt Tagger v3
- WD EVA02 Large Tagger v3
- WD SwinV2 Tagger v3
- WD ViT Tagger v3

This is separate from the existing working tagger adapters.

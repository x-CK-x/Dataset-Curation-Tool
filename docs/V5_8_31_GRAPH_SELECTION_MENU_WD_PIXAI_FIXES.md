# v5.8.31 — Graph Selection, Searchable Node Menu, WD/PixAI Loader Fixes

## Scope

v5.8.31 is a targeted regression and workflow-usability update on top of v5.8.30.

It focuses on four areas:

1. Agentic Graph Editor canvas interactions for large graphs.
2. Attention Visualizer and Augment tab render fixes.
3. A closed-loop model-training improvement graph template based on the attached sample workflow.
4. Isolated adapter support for the PixAI and WD v3 tagger rows that previously failed with `Model adapter is not available`.

## Agentic Graph Editor changes

- Ctrl+drag on the canvas now draws a selection rectangle for nodes and edge midpoints.
- Dragging a selected node moves the full selected node group as a chunk.
- Ctrl+click toggles node selection.
- Ctrl+C copies selected nodes and internal edges.
- Ctrl+X cuts selected nodes and internal edges.
- Ctrl+V pastes the copied graph fragment near the last canvas cursor/world position.
- Delete/Backspace removes selected nodes and selected edges.
- The canvas right-click menu is no longer clamped to a small fixed coordinate range; it opens at the user cursor in graph-world coordinates.
- The node menu now has a search box, quick colored category filters, and the last three used node kinds at the top.
- Mouse-wheel scrolling inside the node menu scrolls the menu instead of zooming the canvas.
- Context menus remain graph-world overlays, so they move/scale with pan and zoom instead of resetting to the page top.
- Multi-port nodes now render distinct input/output ports.

## Multi-port node support

The frontend now reads node/registry `ports` metadata instead of assuming one input and one output. The important multi-port families include:

- `supervisor_controller`: one input, many outputs.
- `parallel_fanout`: one input, many outputs.
- `condition_gate`: one input, true/false outputs.
- `join_merge`: many inputs, one output.
- `bundle_context`: many inputs, one output.
- `output_artifact`: one input, zero outputs.
- `start`, `webhook_event`, `live_stream_input`: zero inputs, one output.

Saved edges preserve `source_port` and `target_port` so graph intent survives reloads.

## Closed-loop training improvement template

The graph catalog now includes `closed_loop_model_training_improvement_graph`.

The template represents:

- user goal → supervisor/orchestrator
- data collection or existing dataset reuse
- branch creation
- tag/caption rules
- parallel image/video/audio labeling
- assistant refinement and rule application
- branch readiness evaluation
- augmentation/upscaling branch improvement
- export and external trainer handoff
- generated-sample/result evaluation
- assistant-proposed dataset and hyperparameter edits
- human review before a replacement workflow/branch update
- feedback loop back into the supervisor

The attached sample workflow JSON is also bundled at:

```text
docs/examples/agentic_closed_loop_training_curation_graph_sample.json
```

## Attention Visualizer

The Attention Visualizer now uses the same tag autocomplete/suggestion control family as the Tag Editor. This keeps tag selection consistent when requesting Grad-CAM, rollout, cross-attention, and overlay artifacts.

## Augment tab

The Augment tab render failure caused by the missing `exportCard()` helper is fixed. The tab now includes a small dataset export/handoff shortcut card instead of failing to render.

## WD and PixAI tagger loader fixes

Added a new isolated `WDOnnxTaggerAdapter` for only the failing WD/PixAI rows:

- `wd-vit-tagger`
- `wd-swinv2-tagger`
- `wd-convnext-tagger-v3`
- `wd-eva02-large-tagger-v3`
- `pixai-tagger-v09`

This adapter does not alter the existing working Thouph/legacy/Hydra/HF taggers.

The adapter loads `model.onnx` and `selected_tags.csv`, follows the WD ONNX preprocessing path, and supports CPU/CUDA ONNXRuntime provider selection. For PixAI v0.9, the registry row uses the public DeepGHS ONNX export while preserving the PixAI base model provenance because the original PixAI repository may require access acceptance.

## Validation notes

The package was validated with Python compilation, frontend JavaScript syntax checking, shell syntax checking, targeted regression tests, and ZIP integrity checking.

Live browser interaction, GPU ONNX inference, model download authentication, and large-model runtime behavior still need user-side testing on the target workstation.

# v5.8.18 EVA `norm_pre` and Agentic Graph Editor Event Handler Fixes

v5.8.18 addresses two reported failures:

1. The legacy `eva02-vit-large-448-8046` PyTorch classifier could still fail under newer `timm` with missing optional EVA attributes such as `norm_pre`.
2. The Agentic Graph Editor looked correct but key standalone-editor interactions were not consistently functional because the integrated vanilla frontend was missing node update/change handler functions and graph-canvas actions could be deferred by scroll protection.

## Legacy EVA compatibility

The legacy EVA adapter now patches additional neutral attributes on older pickled EVA model objects before and during inference:

- `norm_pre` → identity module
- `norm_post` → identity module
- `fc_norm` → identity module
- `attn_mask` → `None`
- `global_pool` → `token`
- `final_norm` → `True`
- `use_rot_pos_emb` → `False`

The retry loop for missing optional EVA attributes was widened so newer `timm` compatibility fields can be patched in one run instead of failing one attribute at a time.

## Graph editor interaction repair

The Agentic Graph Editor frontend now defines the handlers that the canvas and inspector already expected:

- `graphEditorUpdateNode`
- `graphEditorUpdateNodeConfig`
- `graphEditorChangeNodeKind`
- `graphEditorRenderCanvasNow`

The canvas now registers direct and capture-phase handlers for:

- right-click context menus
- wheel zoom
- pointer-drag panning

Graph-editor-specific renders now bypass scroll-deferral protection so right-click menus, node creation, port connection, and node movement appear immediately instead of waiting for the general page-scroll debounce.

## Expected behavior

The graph canvas should support:

- drag empty canvas background to pan
- mouse wheel to zoom around the cursor
- right-click canvas background to open grouped node-type palette
- create the selected node type at the clicked world position
- drag nodes around the canvas
- drag output ports to input ports to create edges
- click output port, then input port, to create an edge
- delete edges through the edge delete handle
- inspect nodes without losing the underlying graph state

## Validation

Selected regression coverage includes:

```text
pytest -q tests/test_v611_eva_norm_pre_graph_editor_handlers.py tests/test_v610_graph_editor_parity_migration_finalize.py tests/test_v607_legacy_tagger_preprocess_scroll_fix.py tests/test_v609_graph_palette_prediction_refresh_eva_fix.py
```

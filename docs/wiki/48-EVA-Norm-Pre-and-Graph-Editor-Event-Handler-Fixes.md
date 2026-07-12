# EVA Norm-Pre and Graph Editor Event Handler Fixes

v5.8.18 fixes a remaining legacy EVA inference compatibility issue and repairs missing frontend handlers used by the integrated Agentic Graph Editor.

## EVA legacy model fix

The `legacy-eva02-vit-large-448-8046` model can be an older pickled `timm` EVA object. Newer `timm` code may look for optional attributes that were not serialized into that older object. v5.8.18 adds neutral compatibility defaults for the remaining missing fields, including `norm_pre` as an identity module.

This is intended to stop the pattern where inference fails one field at a time, for example:

```text
'Eva' object has no attribute 'norm_pre'
```

## Agentic Graph Editor fix

The integrated graph editor now defines the frontend update functions expected by the canvas and inspector, including node update, node-kind change, and config JSON update handlers.

Canvas-specific render calls now bypass the app-wide scroll-debounce path. This matters because the app’s scroll-protection logic can otherwise defer a graph canvas update exactly when the user is trying to right-click, drag, connect, or create a node.

## Expected graph canvas controls

- Right-click empty canvas to open the node palette.
- Choose the exact node type from the grouped palette.
- Drag empty canvas to pan.
- Use the mouse wheel to zoom.
- Drag nodes to move them.
- Drag an output port to an input port to connect nodes.
- Click output port, then input port, to connect nodes without dragging.
- Use edge delete handles to remove edges.

## Notes

This does not replace the current DCT graph editor with the standalone React implementation. It ports the missing interaction contracts into the existing local-first vanilla frontend so the editor remains integrated with DCT workflows, models, MCP tools, and the existing backend graph runtime.

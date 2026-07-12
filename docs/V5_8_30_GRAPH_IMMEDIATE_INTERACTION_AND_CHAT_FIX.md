# v5.8.30 — Immediate Agentic Graph Canvas Interaction and Graph Chat Render Fix

This patch preserves the v5.8.29 attention-overlay, graph-chat, graph-editor, and default-threshold work, then focuses on the interaction regression reported while testing the Agentic Graph Editor.

## Fixed: graph/canvas input delayed by refresh protection

The frontend scroll-jump protection had become too broad. It treated pointer clicks and right-clicks like active scrolling, which protected scroll position but also caused canvas operations to wait behind the polling/render deferral queue.

v5.8.30 separates real scroll input from ordinary graph interaction:

- pointerdown, mousedown, touchstart, node clicks, node drags, right-click menus, port-connection gestures, and graph context-menu actions cancel stale scroll-restore timers without opening the active-scroll render-delay window;
- wheel, touchmove, actual scroll events, and scroll-key navigation remain treated as real scrolling;
- graph-local interactions repaint the canvas and node inspector immediately through graph-local region refresh;
- graph-local actions can fall back to a hard render through `render(true, 'hard')` when targeted region replacement is unavailable;
- passive polling defers while graph canvas interaction is active so background refreshes do not steal the canvas mid-drag, mid-menu, or mid-port-connection;
- the current tab scroll position is still snapshotted/restored around graph-local repaints.

## Fixed: Agentic Graph Chat render failure

The graph-linked chat tab no longer depends on a model-catalog fallback variable from another UI scope. The inline selected-model runtime controls now create a safe fallback model row when the selected assistant/chat model is not present in the catalog snapshot.

This addresses the reported render failure at:

```text
inlineSelectedModelRuntimeControls
agenticGraphChatView
render
setTab
```

## Validation markers

The frontend now contains explicit logic for:

- `cancelPendingScrollRestoreOnly`
- `markActiveUserScrollWindow`
- pointer/click input as non-scroll restore cancellation
- `graphEditorHasActiveCanvasInteraction`
- `graphEditorRefreshInteractiveRegions`
- hard graph-local render fallback through `render(true, 'hard')`
- graph-chat fallback runtime controls without the stale `capsInput` dependency

## Additional v5.8.30 refinement: partial graph region patching

Graph-local updates now replace only the live canvas region and the node-inspector region when possible:

```text
dct-graph-canvas-region
dct-graph-inspector-region
```

This avoids replacing the full application shell for ordinary canvas operations. Node clicks, right-click menus, edge/port state, drag commits, and inspector open/close actions therefore update immediately without waiting for the generic render-defer queue and without forcing the tab scroll container back to the top.

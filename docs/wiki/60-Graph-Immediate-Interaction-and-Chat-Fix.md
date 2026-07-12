# v5.8.30 Graph Immediate Interaction and Chat Fix

v5.8.30 fixes the Agentic Graph Editor interaction delay caused by the refresh/scroll-jump guard.

## What changed

The frontend now treats graph clicks, right-clicks, node drags, port connections, context-menu actions, and graph-wheel zoom as graph interactions rather than page scrolling. These interactions cancel stale scroll-restore passes but do not arm the active-scroll render-delay window.

The graph canvas and node inspector can update directly through targeted region replacement, with a hard-render fallback, instead of waiting for the full app-shell render/defer queue. Background polling still avoids stealing the canvas while a graph interaction is active.

## Scroll behavior

The current tab scroll position is still snapshotted and restored around graph-local updates. The intended behavior is immediate graph response without returning the page or nested tab scroll to the top.

## Graph chat

The Agentic Graph Chat tab now uses a safe selected-model fallback for inline runtime controls. This removes the render failure caused by a stale cross-scope model capability fallback.

## Partial live-region refresh

The Agentic Graph Editor now has dedicated live regions for the canvas and node inspector. Canvas-local actions patch those regions directly instead of routing every click through a full application render. This is specifically intended to keep node selection, right-click menus, drag commits, zoom/pan state, and port connections responsive while preserving the current tab scroll position.

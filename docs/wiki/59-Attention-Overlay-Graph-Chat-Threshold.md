# v5.8.29 Attention Overlay, Graph Chat, and Threshold Update

v5.8.29 moves heatmap-style attention review into the places where the user is already editing and comparing images.

## Inline heatmap overlays

The Tag Editor and Compare tabs now include heatmap overlay controls. These controls create an attention visualization artifact and layer the transparent heatmap over the original preview with configurable opacity and blend mode.

The dedicated Attention Visualizer remains available for clustering, t-SNE/projection, and other visualizations that require their own standalone space.

## Threshold default

The default classifier/tagger threshold is now **0.70** for model runs, orchestration steps, app settings, frontend controls, and legacy Thouph tagger configs.

## Graph Editor interaction fixes

Canvas and node interaction was patched so node clicks and context-menu actions preserve scroll position. Right-clicking a node opens a node-specific action menu. Double-clicking a node opens an expanded inspector. Double-clicking the canvas opens the node palette. Menus now live in graph-world coordinates so they pan and zoom with the canvas.

## Graph Chat

The new Agentic Graph Chat tab is bound to the active graph and selected node. It can discuss, validate, refine, and run workflow actions using the existing chat-history system and approved local tool/COA mechanism.

Only visible plan/action traces are surfaced. Private hidden chain-of-thought is not exposed.

# v5.8.45 — Attention Heatmap, Dropdown, and Queue Refresh Fixes

This release focuses on the attention overlay workflow after the Quick Tag queue stabilized.

## Attention heatmap improvements

- Inline heatmap cards now expose CAM depth and heat-strength controls.
- The fallback overlay is no longer a generic single-color blob. It now produces a signed CAM-style heatmap where green indicates positive evidence and red indicates negative evidence.
- When RedRocket Hydra 3.5 is locally available, the attention service attempts a Hydra-demo-style native CAM path using local Hydra tensors. If this fails, the service returns to the signed fallback and records the reason in the artifact manifest.
- Overlay artifacts still write both a composited overlay image and a transparent heatmap layer.

## Dropdown/refresh stability

Attention overlay and Attention Visualizer dropdowns are now render-sensitive controls. Background polling and deferred renders should not close them while the user is scrolling or choosing values.

## Quick Tag queue cleanup

The Quick Tag model queue now clears recent completed/failed rows more quickly while keeping active rows live. This prevents completed rows from lingering until the user changes tabs.

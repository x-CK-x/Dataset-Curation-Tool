# Attention Heatmap, Dropdown, and Queue Refresh

v5.8.45 improves the attention heatmap overlay used from Tag Editor, Compare, and the standalone Attention Visualizer.

## Heatmap behavior

The inline overlay now uses signed CAM-style colors:

- green: positive evidence for the selected tag/token
- red: negative evidence for the selected tag/token

Hydra-compatible local models can attempt native CAM extraction. If native tensors are unavailable, the fallback still produces a deterministic signed overlay so the UI remains functional.

## Controls

Inline overlay cards expose method, model, tag/token, CAM depth, heat strength, opacity, and blend mode. Clustering and projection methods remain in the Attention Visualizer tab.

## Refresh protection

Attention dropdowns are protected from background refresh, matching the scroll/dropdown stability rules used elsewhere in the app.

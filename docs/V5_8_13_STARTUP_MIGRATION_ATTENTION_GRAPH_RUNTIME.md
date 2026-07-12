# v5.8.13 — Startup Migration Progress, Attention Heatmaps, and Functional Graph Runtime

This update focuses on three areas that affect day-to-day usability: visible first-run maintenance during manual migration, restored attention/heatmap visualization workflows, and a more functional Agentic Graph Editor runtime.

## Dashboard startup maintenance during migration

Manual migration can now attach itself to the Dashboard **Startup Maintenance Progress** card. This covers the case where first-run tag downloads were cancelled or skipped and the user instead starts moving an existing install/runtime into the current project. The Dashboard card now receives job id/type, phase, message, percent, elapsed time, and ETA updates from the migration job and post-migration reconciliation steps.

The routine startup path remains intentionally fast on later runs: expensive first-run tag-export sync and migration work only run when they are required by settings/cache state, while ordinary runs reuse cached startup status and active-profile dictionary state.

## Attention and heatmap visualization

The **Attention Visualizer** tab now supports immediate artifact creation for:

- classifier Grad-CAM / CAM-style heatmaps;
- ViT/SigLIP attention rollout contracts;
- Hydra CAM attention / PCA handoff;
- diffusion U-Net / transformer cross-attention contracts;
- t-SNE / embedding projection planning;
- tag-region overlay review artifacts.

When a model-specific adapter exposes true tensors, that adapter can replace the generic overlay path. Until then, the backend writes deterministic review overlays and manifests so the UI, workflow integration, and artifact format are already stable.

## Agentic Graph Editor runtime

The integrated editor keeps the existing dark/neon canvas, grid, smooth nodes, and port-based layout, while adding more behavior from the standalone graph editor:

- local graph presets stored in browser local storage;
- snapshot JSON export;
- edge labels, conditions, and edge-type metadata;
- full graph runtime session execution;
- selected-node execution;
- runtime result inspection per node;
- bundle aggregation with limit policies;
- supervisor/controller fanout previews;
- model-call prompt packets;
- browser/MCP/tool-call approval previews.

The runtime path is conservative by design. Browser actions, shell commands, MCP calls, webhooks, and external tool calls remain approval-gated unless explicitly approved for a run.

## Validation

Selected regression coverage includes startup progress attachment, attention artifact creation, graph runtime execution, graph compatibility normalization, and frontend hook checks.

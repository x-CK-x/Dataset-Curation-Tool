# Startup Migration Progress, Attention Heatmaps, and Graph Runtime

This page documents the v5.8.13 updates.

## Startup maintenance progress during manual migration

When a user cancels or skips first-run tag downloads and then uses **Install Migration**, the migration job is now treated as startup maintenance. The Dashboard progress circle updates live with migration progress, reconciliation status, elapsed time, ETA, and the backing job id/type.

## Attention Visualizer

The Attention Visualizer supports Grad-CAM/CAM, ViT/SigLIP attention rollout, Hydra CAM/PCA handoff, diffusion U-Net cross-attention, t-SNE/embedding projection planning, and tag-region overlays. Immediate rendering writes overlay and manifest artifacts under the application outputs folder.

## Agentic Graph Editor runtime

The editor now supports local presets, export snapshots, edge metadata editing, graph-runtime session execution, selected-node execution, per-node runtime output inspection, bundle-limit policies, supervisor fanout previews, and approval-gated browser/MCP/tool call previews.

## Safety model

Workflow graph execution does not automatically run high-impact external actions. Shell commands, browser actions, MCP calls, webhooks, and external tool calls are previewed or blocked unless the user explicitly approves unsafe steps for that run.

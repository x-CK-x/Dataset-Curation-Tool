# v5.8.39 — Live Model Cards, VRAM Visibility, and Gallery Resilience

## Scope

This patch targets three reliability issues observed during multi-model testing:

1. Models that finish loading did not immediately move/highlight in the Models tab until the user switched tabs.
2. VRAM and system RAM displays did not make actual memory changes visible enough while models were loaded and unloaded.
3. Failed model jobs could interfere with media refreshes, making the Gallery appear empty or broken after unrelated model errors.

## Frontend live model-card refresh

The live runtime poller now synchronizes `state.models` from `/api/models/status`, patches lifecycle rings, updates loaded/downloaded/repair state in model cards, and reorders active/loaded rows in the Models tab without forcing a full shell rebuild.

The in-place patch path preserves the Models tab scroll position and skips destructive reorder when the user is actively interacting with a control inside the model list.

## VRAM and RAM visibility

The resource panel now shows:

- actual used VRAM;
- actual free VRAM;
- memory source (`nvidia-smi`, `torch`, or app reservation fallback);
- torch allocated memory;
- torch reserved memory;
- app reservation budget;
- system RAM used/available.

Backend resource status merges detected CUDA device rows with a PyTorch memory snapshot where available, so the GUI and orchestrator have the same live resource picture.

## Gallery/media resilience

`loadMedia()` now preserves the last good Gallery state if a media refresh fails. The Gallery displays a non-blocking warning instead of rendering as an empty or failed page.

The background job/model/media poller is wrapped in a top-level failure guard. A failed model job or a failed status response should no longer break subsequent Gallery or Models-tab updates.

## Orchestrator runtime planning context

Added:

```text
GET /api/models/runtime-planning-context
```

The endpoint returns compact model metadata, loaded model details, live GPU/RAM resource state, and strict placement policy guidance. This gives assistant/orchestrator/LLM/VLM/GLM supervisor flows an explicit source of live memory data for choosing:

- target GPU IDs;
- sharding strategy;
- tensor-parallel size;
- runtime backend;
- queueable model inference jobs.

## Key files

```text
data_curation_tool/services/model_service.py
data_curation_tool/routers/models.py
data_curation_tool/static/app.js
data_curation_tool/static/styles.css
```

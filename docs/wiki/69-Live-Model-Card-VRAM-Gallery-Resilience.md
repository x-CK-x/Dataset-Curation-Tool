# v5.8.39 — Live Model Card, VRAM, and Gallery Resilience Fix

This patch fixes the last visible gap in the live model-runtime UI: a model could finish loading, but the Models tab would not immediately move it to the active/loaded section or apply the active highlight until the user switched tabs.

## Models tab behavior

The Models tab now patches model cards in place from live lifecycle status:

- loaded-card background/highlight updates immediately;
- lifecycle rings update immediately;
- loaded/downloaded/repair chips update immediately;
- loaded models can move to the top without requiring a tab switch;
- the model-list scroll position is preserved.

## Runtime memory panel

The GPU resource panel now distinguishes app planning reservations from actual runtime memory usage.

Each CUDA card shows:

- actual used VRAM;
- actual free VRAM;
- source of the memory reading;
- torch allocated/reserved memory;
- app reservation budget;
- planning availability.

The system RAM line remains live as well.

## Gallery resilience

A failed model job or transient backend refresh error should not destroy the Gallery state. The Gallery now preserves the last good page and shows a non-blocking warning if media refresh fails.

## Assistant/orchestrator placement context

The new runtime planning endpoint is:

```text
/api/models/runtime-planning-context
```

It exposes compact model metadata plus live GPU/RAM state and strict placement policy so assistant/orchestrator models can reason about which GPU IDs, sharding strategy, tensor parallelism, and model jobs to queue.

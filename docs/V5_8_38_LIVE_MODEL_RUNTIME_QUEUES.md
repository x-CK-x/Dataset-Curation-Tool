# v5.8.38 — Live Model Runtime Status and Inference Queues

This release focuses on model-runtime responsiveness while keeping the earlier scroll-stability rules intact.

## Changes

- Added live model-runtime polling that patches model lifecycle circles, model dropdown option styles, GPU VRAM/resource panels, and regular system RAM status without requiring the user to leave and re-enter a tab.
- Added a system-RAM snapshot to `/api/models/resource-status` so the UI can show CPU RAM pressure alongside app-level GPU reservations and driver-reported GPU memory.
- Added a generic backend endpoint, `POST /api/models/queue-runs`, for queueing multiple model inference jobs through the existing model-inference job lane.
- Added Quick Tag multi-model queueing in the Tag Editor with per-job progress rows, per-job ETAs, and an overall circular queue progress indicator.
- Added an Agent Tools model queue panel that shows all model jobs, including user-queued, quick-tag, graph, and assistant/orchestrator model handoffs.
- Updated assistant/orchestrator queueing so approved recommendations patch live model queue state instead of forcing the user to switch to Jobs.

## Non-goals

This release does not change model adapter behavior, WD/PixAI preprocessing, Thouph/JTP/Hydra inference paths, tag dictionary normalization, or graph runtime semantics. It only adds queueing/status/UI synchronization and one generic queue endpoint.

## Manual verification checklist

1. Load a model and keep the Tag Editor open.
2. Confirm the lifecycle circles, model dropdown highlights, GPU VRAM, and system RAM update without switching tabs.
3. Select several loaded/downloaded tagger models in the Quick Tag queue panel.
4. Queue them in parallel and confirm the active queue list shows per-job progress and ETA.
5. Confirm completed quick-tag jobs disappear from the active queue list but remain visible in Jobs.
6. Open Agent Tools and confirm the global model queue shows model jobs from Quick Tag and approved assistant/orchestrator plans.

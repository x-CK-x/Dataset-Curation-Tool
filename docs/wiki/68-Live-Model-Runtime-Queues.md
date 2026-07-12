# v5.8.38 Live Model Runtime Queues

v5.8.38 adds live model-runtime synchronization across the model-heavy surfaces of the application.

## Runtime resource updates

The frontend now polls lightweight model-runtime endpoints while model jobs are active or while the user is on model-related tabs. It patches existing DOM regions instead of forcing a full tab render, so scroll position should remain stable.

The resource panel now includes:

- CUDA device totals;
- app-level VRAM reservations;
- driver-reported free memory;
- loaded model residency;
- loading reservations;
- regular system RAM total/used/available.

## Quick Tag queue

The Tag Editor Quick Tag section now supports queueing more than one tag/rating/classifier model against the current image or selected media set. The queue panel shows:

- per-model job status;
- progress bars;
- elapsed time;
- ETA;
- an overall circular queue-progress indicator.

Completed jobs are removed from the active queue list but remain available in the Jobs tab.

## Agent Tools model queue

Agent Tools now includes a global model-job queue panel. It is broader than the Quick Tag queue and includes all model jobs, including jobs started by user actions, approved assistant/orchestrator plans, graph workflows, and direct Agent Tools model queue actions.

## Backend endpoint

`POST /api/models/queue-runs` accepts a list of `ModelRunRequest` payloads and queues them through the existing `model_inference` job lane. This gives the UI, graph editor, assistant panels, and future supervisor/orchestrator models a shared queueing primitive for model inference jobs.

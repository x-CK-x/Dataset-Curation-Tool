# v5.37 Model Lifecycle Status Circles

This patch adds a shared lifecycle/status layer for model operations without replacing the existing Jobs system. Jobs remain the durable execution log; lifecycle status is the live polling surface used by the HUD to render circular indicators.

## Tracked stages

Every registered model now has four status rows:

1. **Download** — model repository/checkpoint download, including dry-run checks.
2. **Load** — adapter/model initialization into memory before use.
3. **Inference** — single-image and batch model execution.
4. **Training** — currently wired to training scaffold creation and reserved for future full training jobs.

Each row includes `state`, `active`, `progress`, `percent`, `message`, `job_id`, timestamps, and optional `error` / `result` payloads.

## API additions

- `GET /api/models/status` returns all model lifecycle rows plus aggregate status per stage.
- `GET /api/models/status?model_name=<name>` returns a single model lifecycle payload.
- `GET /api/models/status/<name>` is the path-style equivalent.
- `POST /api/models/load` queues an explicit model-load job using the same runtime placement fields as `/api/models/run`.

`/api/models` now includes each row's `loaded` flag and `lifecycle` stage snapshot.

## UI additions

The HUD now renders circular status/progress indicators in:

- the top of the Models tab as a global aggregate status row;
- every model catalog card;
- the main Run Model on Selection card;
- quick tag/rating model cards used in editor, batch, compare, and annotation workflows;
- model tag-selection cards;
- annotation model download/load panels.

Buttons that would use a model are disabled while that model's download or load stage is active. Backend guards enforce the same rule, so direct API calls cannot start inference/chat/tag-selection against a model that is still downloading or loading.

## Backend integration notes

- `ModelLifecycleTracker` is an in-memory, thread-safe service attached to `ModelService`.
- `JobManager.submit_with_job_id(...)` lets lifecycle rows reference the durable job id from inside queued tasks.
- `ModelRegistry.load_model(...)` centralizes explicit and lazy loading and uses per-model load locks.
- Existing lazy `predict(...)` / `chat(...)` behavior is preserved; it now goes through the explicit load path when needed.
- Annotation model downloads and load/validation paths update the same lifecycle rows.
- Training scaffold creation marks the training stage completed so the fourth circle is already part of the model contract before a future trainer is added.

## Regression coverage

`tests/test_v537_model_lifecycle_status.py` verifies:

- the lifecycle status endpoint exposes all four stages;
- explicit load jobs complete and attach their job id without regressing to queued status in inline mode;
- model list rows expose `loaded=True` after loading;
- no-media inference completes the inference stage cleanly;
- training scaffold creation updates the training stage circle.

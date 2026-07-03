# v5.45 Configurable Assistant / Orchestrator Model

This build makes the app assistant an actively configurable model instead of a hardwired built-in helper.

## Assistant tab

The Assistant tab now has an **Assistant / Orchestrator Model Control** card. It lets you:

- choose the current chat model,
- set the default assistant model,
- set the default orchestrator model,
- load the selected assistant model into RAM/VRAM,
- unload the selected assistant model,
- use the same GPU placement, dtype, quantization, runtime, tensor-parallel, and max-memory controls used by the Models tab.

The built-in `dataset-assistant` remains available as a no-model fallback. If you select a downloaded VLM/LLM such as Gemma, that model can become the default Assistant and/or Orchestrator model.

## Backend API

New endpoints:

```text
GET /api/models/assistant-config
PUT /api/models/assistant-config
```

Stored settings:

```text
assistant_model_name
orchestrator_model_name
assistant_model_auto_load
assistant_allow_orchestration
```

The app validates that selected defaults are assistant/chat/VLM-capable rows from the model registry.

## Orchestrator default

Orchestration templates now read the configured orchestrator model. Old or placeholder orchestrator requests using `dataset-assistant` resolve to the configured orchestrator default, while explicit Assistant chat can still choose `dataset-assistant` to use the local no-model fallback.

## User-directed orchestration

This patch does not make the assistant autonomously launch arbitrary work. It provides the model-selection and persistence layer needed for the assistant to act as the user-directed orchestrator when future tool-calling/task-dispatch flows are added.

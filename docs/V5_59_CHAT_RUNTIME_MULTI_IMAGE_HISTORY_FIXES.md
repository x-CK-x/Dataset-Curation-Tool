# v5.59 Chat Runtime, Multi-Image Navigation, and History Control Fixes

## Runtime payload defaults

The Tag Editor and Code Assistant chat composers now sanitize model runtime controls before calling backend APIs. Empty UI values for dtype, quantization, runtime engine, sharding, and device are converted to safe defaults before the request is sent:

- `torch_dtype`: `auto`
- `quantization`: `none`
- `runtime_engine`: `transformers`
- `sharding_strategy`: `none`
- `device`: `auto`

The backend schemas also coerce blank runtime values so direct API calls cannot fail with Pydantic literal validation errors when a frontend select has an empty value.

## Inline model controls outside the Models tab

Assistant-enabled surfaces now expose compact selected-model controls without forcing the full Models tab UI into the workflow. In the Tag Editor assistant card and Code Assistant tab, open the selected model controls section to access:

- model status badges
- GPU IDs
- sharding strategy
- dtype
- quantization
- runtime engine
- tensor parallel size
- max-memory overrides
- queue download/update
- load into memory
- unload
- VRAM placement check

These actions stay on the current page instead of jumping to the Jobs tab.

## Models tab no longer auto-jumps to Jobs

Queueing a model download, model update, or model run from the Models tab now stays on the Models tab. Use the existing Open Last Job button when full job logs are needed.

## Selected-media queue persistence

The frontend now caches selected media records as they are selected. Tag Editor and Compare use that cache to cycle through selected images, even after UI refreshes or when the active item is not the first selected media object on the current rendered page.

## Chat history controls

Tag Editor Assistant Chat and Code Assistant Chat now include:

- Clear memory: clears only the cached condensed context summary.
- Clear chat: clears visible messages and memory while keeping saved image/project state.
- Delete: selectively deletes one message.
- Delete from here: deletes a message and all later turns so the conversation can continue from the prior point.
- Existing edit-message behavior remains available for user messages.

Switching the selected model mid-conversation keeps the same conversation ID/history and sends that persisted context to the newly selected model.

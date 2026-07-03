# v5.49 Orchestrator Controls, Tag-Selection UX, and Active Model Highlighting

## Assistant / orchestrator control

- Added user-approved assistant/orchestrator planning endpoints and UI support.
- Assistant-capable model selectors can promote the selected LLM/VLM to the orchestrator role from assistant-enabled surfaces.
- The orchestrator planner can recommend multiple model runs for selected tasks and media.
- Recommendations include GPU placement feedback, selected GPU IDs, sharding strategy, warnings, and errors.
- Nothing is queued by the planner endpoint. Queueing requires explicit user approval.
- Added queue support for approved orchestrator model-run plans through `/api/models/orchestrator/queue-runs`.

## Tag Editor LLM/VLM/Assistant Tag Selection

- The model dropdown is category-aware and color-coded.
- Sorting order for tag-selection models is:
  1. local VLMs
  2. local LLMs / assistants
  3. tagger, caption, rating, classifier models
  4. API/cloud models last
- Dropdown options expose category/provider details through hover titles.
- Selecting a model now immediately primes visible lifecycle circles instead of waiting on the next slow status poll.
- During tag-selection inference, the UI starts optimistic lifecycle state immediately and keeps polling in the background.
- Fixed a first-run preview/highlight issue by forcing the editor tag-strip DOM to sync after the first result and by falling back to global `selected_tags` when per-media keys are missing.

## Models tab active model highlighting

- Active/loaded/running models are pinned to the top of the Models tab model list and raw registry table.
- Active non-custom models are highlighted with the color for their model class/category.
- User custom models keep their custom shaded background only and do not receive the active category highlight.
- Inactive built-in/catalog rows remain unhighlighted.

## Validation added

Added `tests/test_v549_orchestrator_tag_selection_active_models.py` covering:

- orchestrator plan endpoint returns feedback and placement requests without queueing work
- queueing orchestrator runs requires explicit approval
- frontend category dropdown, fast lifecycle, first-run highlight, planner, and active-model affordances are present

# v5.63 Assistant Visible Planning and Think-Longer Controls

This build adds a controlled planning/deliberation layer for assistant-capable models across the application.

## Important boundary

The feature exposes a **user-visible planning summary** and action notes. It does **not** attempt to reveal provider/private hidden chain-of-thought. Local/API models are asked to produce a separate concise plan that the UI can show before the final answer.

## New settings

Settings now includes **Assistant Thinking / Visible Planning Defaults**:

- `assistant_thinking_mode`: `off`, `fast`, `balanced`, or `deep`
- `assistant_reasoning_effort`: `none`, `low`, `medium`, `high`, or `max`
- `assistant_show_visible_plan`
- `assistant_planning_passes`
- `assistant_plan_max_tokens`
- `assistant_min_chat_tokens`
- `assistant_deep_chat_tokens`
- `assistant_max_auto_reflection_rounds`

## Runtime behavior

When enabled, assistant chat can run a separate planning pass before the final answer. The plan is returned as:

- `visible_plan`
- `action_notes`
- `reasoning`

The final answer receives the visible plan as structure/context, but the plan is rendered separately in the UI.

## Affected surfaces

The controls and display are now available in:

- Assistant tab
- Tag Editor assistant chat and tag-selection panel
- Compare / Batch shared assistant panels through the same tag-selection component
- Code Assistant tab
- Agent tool planning/relay calls through default reasoning options

## Critical tag tasks

Tag-selection tasks can include visible media-specific plans through `visible_plans_by_media`. Existing completion guards still use `[TASK_COMPLETE]` and automatic continuation to reduce partial tag operations.

## Cloud/model compatibility

For cloud adapters that accept reasoning-effort style hints, the app passes `reasoning` / `reasoning_effort` values through runtime kwargs. For local models that do not support native reasoning controls, the app uses plan-before-answer prompting plus larger token/continuation budgets.

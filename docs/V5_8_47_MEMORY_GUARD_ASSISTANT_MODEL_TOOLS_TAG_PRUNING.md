# v5.8.47 — Memory Guard, Assistant Model Tools, and Tag Pruning

This release focuses on long-running VLM/LLM sessions and Tag Editor assistant behavior.

## System RAM guard

Long model-chat sessions can grow system RAM through large context payloads, chat response metadata, and optional CPU offload of model state. v5.8.47 changes the default policy so automatic VRAM-to-CPU offload is disabled unless the user explicitly enables it. A system-RAM guard now runs after model calls and avoids CPU offload when RAM pressure is high.

Chat context and response JSON stored in SQLite are compacted so visible chat text remains available without repeatedly storing massive structured payloads. Old conversation payloads are compacted one row at a time to avoid loading every large JSON blob into RAM at once.

## Condensed memory display

The condensed conversation memory panel is now expanded by default, scrollable, copyable, downloadable, and uses a full pre-wrapped view instead of the compact log style that could visually truncate long summaries.

## Tag Editor assistant tag pruning

The Tag Editor assistant now sends the active Dataset Pipeline / LoRA-rule context to the assistant request. When enabled, the assistant can return JSON fields such as `keep_tags`, `remove_tags`, `add_tags`, and `final_tags`; the backend applies those directives to the selected media tag list.

The prompt contract performs two passes conceptually:

1. Remove tags that are not visible or media-evidenced.
2. Apply the active LoRA/dataset rules before writing final tags.

## Assistant-controlled model queue tools

Approved agent/tool calls can now queue model operations directly:

- `queue_model_load`
- `queue_model_inference`
- `queue_model_unload`
- `wait_for_jobs`

The tools use the shared JobManager, so model operations launched by an assistant/orchestrator appear in the normal live job queues. The assistant still requires visible user approval/COA execution controls for tool execution.

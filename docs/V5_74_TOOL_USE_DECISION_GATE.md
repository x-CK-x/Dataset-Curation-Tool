# v5.74 Tool-Use Decision Gate

This release changes the assistant/tool contract so tool visibility does **not** force every prompt into a COA/tool workflow.

## What changed

- Added a tool-use decision layer for assistant-capable models.
- The model is instructed to choose one response mode before acting:
  - `DIRECT_ANSWER`: answer normally; no tool calls.
  - `APP_GUI_ACTION`: route the task through the Data Curation Tool GUI/app workflow.
  - `TOOL_COA`: propose approved filesystem/terminal/browser/Python/model-delegation tools.
  - `MIXED`: answer what can be answered directly, then propose only the remaining tool calls.
- Added `app_gui_action` as a structured tool-call type for app/internal GUI workflows so the model does not misuse PowerShell/Python for tasks that belong inside the app.
- Added visible tool-decision badges so users can see when the model decided no tool was needed versus when it proposed a local tool COA.
- Added Settings controls for:
  - model decides if tools are needed
  - allow no-tool/direct chat
  - app/GUI action routing
  - show tool-decision badges

## Why this matters

The assistant should have access to tools, but tool access is not equivalent to tool requirement. Many prompts should be answered directly from current context, while other prompts need GUI/app actions, and only some prompts need OS-level commands or generated scripts.

## Human-in-the-loop behavior

External/local actions still follow the existing approval path. The difference is that the assistant now has an explicit contract to avoid fabricating COAs when no tool is needed.

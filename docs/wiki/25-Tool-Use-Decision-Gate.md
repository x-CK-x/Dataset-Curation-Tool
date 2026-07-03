# Tool-Use Decision Gate

<!-- DCT_VISUAL_START -->
![Tool-use decision gate visual guide](assets/images/agent_tools_decision_gate.png)
<!-- DCT_VISUAL_END -->


The assistant can see the Agent Tools runtime, but it should not use tools for every message. The v5.74 decision gate teaches assistant/orchestrator models to choose among four modes before responding.

## Response modes

| Mode | Meaning | User result |
|---|---|---|
| `DIRECT_ANSWER` | No tool needed. | Normal chat response; no COA button is required. |
| `APP_GUI_ACTION` | Best handled inside the Data Curation Tool GUI/app workflow. | The assistant describes or emits an `app_gui_action` for review. |
| `TOOL_COA` | Needs local filesystem, terminal, Python, browser, URL fetch, or model-delegation work. | The assistant proposes executable COAs/tool calls for approval. |
| `MIXED` | Some parts can be answered directly; some need tools. | The assistant answers what it can and proposes only the needed tools. |

## Why it exists

Earlier versions made tools visible but could make small local models overuse them or assume every request needed a plan. This gate makes tool use a decision rather than a default.

## Settings

Open **Settings → Agent Tools Safety / Function-Calling Runtime** and use:

- **model decides if tools are needed**
- **allow no-tool/direct chat**
- **enable app/GUI action routing**
- **show tool-decision badges**

## `app_gui_action`

Use this mode for tasks that belong inside the application, such as opening a tab, refreshing the gallery, inspecting jobs, using model controls, or applying app-side tag/caption workflows. It avoids unnecessary PowerShell/Python commands for things the GUI already knows how to do.

# COA Reattempts and Live Action Notes

<!-- DCT_VISUAL_START -->
![COA reattempts and live action notes visual guide](assets/images/agent_tools_decision_gate.png)
<!-- DCT_VISUAL_END -->


This page explains the v5.70 Agent Tools behavior.

## Live action-notes overlay

Assistant chat panels can show a temporary overlay while a model response, queued chat message, or approved COA/tool run is active. The overlay is checked by default and can be disabled in the thinking/planning controls or Settings.

The overlay is not hidden/private chain-of-thought. It is a generated status panel that tells the user what the application is doing: collecting context, estimating token budget, parsing COAs, running jobs, and relaying results.

## Running approved COAs

When a model proposes tool calls, the application parses them into reviewable COA/action cards. After approval, the app executes them through the Agent Tools runtime and imports the stdout/stderr/result JSON back into the conversation before asking the assistant to continue.

## PowerShell best practice

When `shell` is `powershell`, the command should be the PowerShell script itself, not another nested `powershell.exe -Command ...` wrapper.

Preferred:

```json
{"tool":"run_shell_command","arguments":{"shell":"powershell","command":"Get-Content -Path \"C:\\Users\\Me\\Downloads\\file.json\" -Raw"}}
```

The app now normalizes redundant PowerShell wrappers when a local model emits them anyway.

## Reattempt policies

Settings exposes several modes:

- Always confirm every COA/action.
- Only confirm high-risk/new-section COAs.
- Full computer access with high-risk confirmation.
- Full auto, including high-risk COAs.

The default remains human-in-the-loop. Automatic retry counts are capped unless the user enables the experimental infinite option.

## Orchestrator model spawning

The orchestrator can inspect GPU/model resources and propose running another model as a subtask. These actions still flow through the same approval and logging system.

# v5.70 — Agent COA Execution, Live Action Notes, PowerShell Normalization, and Reattempt Controls

This build tightens the agentic/tool execution path used by the Assistant, Tag Editor assistant, Compare assistant, Batch assistant, Code Assistant, and Agent Tools tab.

## Visible live action notes

The chat panels now include a checked-by-default **live action-notes overlay** while a response, queued message, or COA/tool run is active. This is a user-facing status/planning layer. It is not provider/private hidden chain-of-thought.

The app still records `hidden_chain_of_thought_exposed: false` because hidden/private chain-of-thought is not exposed. The visible overlay is intended to give the user the practical information they need: what context is being prepared, whether a tool plan is being parsed, whether output is being relayed, and whether queued messages remain.

## PowerShell command normalization

Model-generated tool calls often accidentally include a full PowerShell executable wrapper even though the tool call already selected `shell="powershell"`. Example:

```json
{
  "tool": "run_shell_command",
  "arguments": {
    "shell": "powershell",
    "command": "\"%SystemRoot%\\system32\\WindowsPowerShell\\v1.0\\powershell.exe\" -Command \"python -c 'print(123)'\""
  }
}
```

The app now strips that redundant wrapper before execution, so the actual executed PowerShell script becomes:

```powershell
python -c 'print(123)'
```

This avoids nested PowerShell parser failures around `-Command`.

## Agent Tools defaults

Clean installs now default to:

- Agent Tools enabled
- approval required per action
- shell/CMD/bash enabled
- Python scripts enabled
- file writes enabled
- browser actions enabled
- existing Firefox profile allowed
- high-risk commands allowed only with confirmation text
- any path allowed
- approved COA execution enabled
- auto relay after plan jobs enabled
- sandbox mode: `local`
- default allowed roots: user Downloads, Desktop, Documents

Existing settings files are preserved unless changed through Settings.

## COA confirmation modes

Settings now exposes a COA confirmation mode:

1. **Always get confirmation on every COA/action** — safest default human-in-the-loop mode.
2. **Only confirm high-risk/new-section COAs** — low/medium risk retries can run after an approved plan.
3. **Full computer access, confirm high-risk COAs** — broader access, but high-risk still requires confirmation.
4. **Full auto, including high-risk COAs** — experimental mode for users who intentionally permit full autonomous command execution.

## Reattempt controls

Failed COAs can now ask the selected assistant/orchestrator for a corrected retry plan. The number of reattempts is configurable, with a deliberately separate experimental infinite option.

In the safest `always` confirmation mode, retry COAs are proposed and logged but not automatically executed until the user approves them.

## Orchestrator model spawning

Agent Tools now includes app-native tools for:

- inspecting model/GPU/VRAM resources
- running another model as a subtask through the same model registry and placement controls

This lets a designated orchestrator ask for resource status, select a specialized local/API model, and run that model as part of an approved COA workflow.

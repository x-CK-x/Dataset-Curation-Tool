# v5.74 — Model-Decided Tool Use and GUI Action Routing

This patch changes the assistant/tooling contract so visible tools do not force every prompt into a terminal/script workflow.

## What changed

- Assistant prompts now explicitly require a tool-use decision for each request.
- The model can choose among:
  - `answer_directly`
  - `app_gui_action`
  - `local_tools`
  - `model_delegation`
  - `mixed`
  - `ask_clarifying_question`
- Direct answers are valid when no tool is needed.
- In-app GUI/workflow actions are separated from OS-level tools through `app_gui_action`.
- Local commands/scripts/browser/file/model-delegation COAs are only expected when the task truly needs external action or information.
- Agent plan results and assistant responses now include tool-decision metadata so the UI can show whether no tool, GUI action, or local tool COA was selected.

## Why this matters

The assistant should know that PowerShell, CMD, Bash, Python, browser actions, file access, model spawning, and GUI actions are available, but it should not use them automatically for every message. Some prompts only need a normal answer; some need an app workflow; some need local tool execution after user approval.

## UI behavior

Assistant chat messages and Agent Tools plan results can show a tool-decision badge such as:

- **No tool needed**
- **In-app GUI action**
- **Local tool COA**
- **Model subtask**
- **Mixed COA**
- **Clarification needed**

A new Settings control lets the user hide/show these badges.

## Safety behavior

The existing approval and COA execution rules remain in place. This patch only improves the decision layer before tools are proposed or executed.

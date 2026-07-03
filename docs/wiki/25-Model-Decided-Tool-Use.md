# Model-Decided Tool Use

<!-- DCT_VISUAL_START -->
![Model-decided tool use visual guide](assets/images/agent_tools_decision_gate.png)
<!-- DCT_VISUAL_END -->


The assistant can see available tools, but tool access is not the same as tool requirement.

For each assistant request, the model should decide whether to:

1. answer directly,
2. route through an in-app GUI/workflow action,
3. propose approved local tools such as PowerShell, Bash, Python, file access, browser automation, or URL fetch,
4. delegate a subtask to another model,
5. use a mixed plan, or
6. ask a clarifying question.

## Direct answer mode

Use this when the user is asking for explanation, discussion, reasoning over already-visible data, or a normal chat response.

## In-app GUI action mode

Use this when the right action is inside Data Curation Tool itself, such as switching tabs, refreshing state, applying tags through the app UI/API, opening Jobs, or asking the user to inspect a panel.

## Local tool COA mode

Use this when the assistant needs information or side effects outside the current app context, such as reading a file, listing a folder, running PowerShell, generating and running Python, opening a browser, or fetching a URL.

## Model delegation mode

Use this when an orchestrator should inspect model resources and route a subtask to another model that is better suited for the job.

## Human approval

Tool execution still follows the configured approval policy. The decision badge only explains what path the assistant chose.

## `app_gui_action`

`app_gui_action` is a structured way for the model to say the next step belongs inside Data Curation Tool rather than in PowerShell, Bash, Python, or a browser. Use it for tab changes, app refreshes, Jobs/Models/Tag Editor workflows, tag/caption operations, or user-review steps.

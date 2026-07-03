# Approved COA Execution

<!-- DCT_VISUAL_START -->
![Approved COA execution visual guide](assets/images/agent_tools_decision_gate.png)
<!-- DCT_VISUAL_END -->


The assistant/orchestrator can generate a course-of-action plan and convert it into executable tool calls. These calls can run PowerShell, CMD/batch, bash/sh, generated Python scripts, file operations, URL fetches, and Firefox/geckodriver browser actions through the Agent Tools runtime.

## Basic workflow

1. Select an assistant-capable local/API model.
2. Enable **approved local tools/COA** in the assistant panel or Agent Tools tab.
3. Ask the model for a task or plan.
4. Review the generated COA/tool calls.
5. Tick **approve next local action** and **enable approved COA execution**.
6. Click **Execute Approved COA Plan**.
7. Inspect logs/results in the Jobs tab.
8. Relay the result back to the assistant when another step is needed.

## Supported tool-call formats

The parser accepts strict JSON tool calls:

```json
{
  "tool_calls": [
    {
      "tool": "run_shell_command",
      "arguments": {
        "shell": "powershell",
        "command": "Get-ChildItem -Force",
        "cwd": "C:\\path\\to\\project"
      },
      "risk": "low",
      "note": "List files in the target folder.",
      "requires_approval": true
    }
  ]
}
```

It also accepts practical COA snippets from smaller local models:

```powershell
Get-ChildItem -Force
```

```python
print("hello")
```

## Safety controls

The app still uses human approval and job logging. High-risk actions require the high-risk checkbox plus the confirmation phrase:

```text
RUN HIGH RISK ACTION
```

The Settings tab controls allowed roots, sandbox mode, browser profile access, shell/script/file/browser permissions, timeouts, and output limits.

# v5.64 Approved COA Execution

This release closes the gap between visible assistant plans and actual local action execution.

## What changed

- Added an explicit **Enable approved COA execution** checkbox to Agent Tools approval controls.
- Added a backend sequential plan runner:
  - `POST /api/agent-tools/run-plan`
- Added **Execute Approved COA Plan** buttons for generated tool plans.
- Normal assistant chat can now be told that approved local tools are available, so local models should stop answering that they cannot run commands merely because they are sandboxed.
- Tag Editor, Assistant, and Code Assistant chat surfaces can opt into this tool contract.
- Model responses are parsed for executable tool calls in multiple formats:
  - JSON `tool_calls`, `actions`, or `steps`
  - fenced `powershell`, `cmd`, `bash`, `sh`, or `python` blocks
  - labeled `PowerShell:`, `CMD:`, `Bash:`, and `Python:` COA notes
- Approved plan execution runs as a visible job and preserves stdout/stderr/results.

## Execution model

The model does not directly execute commands inside text. It produces a concrete tool-call plan. The application then:

1. Shows the plan/tool calls to the user.
2. Requires the user to approve local action execution.
3. Runs the plan as visible jobs.
4. Stores logs/results in the Jobs tab.
5. Allows relaying the result back to the assistant for the next COA step.

## Important controls

The plan runner requires one of these to be enabled:

- Settings → Agent Tools Safety / Function-Calling Runtime → **enable approved COA execution**
- the per-panel checkbox **enable approved COA execution** before running a plan

For high-risk commands, the existing high-risk checkbox and confirmation phrase are still required:

```text
RUN HIGH RISK ACTION
```

## Why this was needed

Some local models, especially smaller LLM/VLM models, will answer that they cannot run terminal commands even when the host application has a tool runtime. v5.64 injects a clear local tool contract into assistant chat when the user enables local tools, telling the model to produce executable JSON/tool calls instead of refusing.

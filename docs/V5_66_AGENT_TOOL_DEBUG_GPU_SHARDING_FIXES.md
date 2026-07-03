# v5.66 Agent Tool Debug, Python Runtime, GPU Identity, and Sharding Fixes

This release focuses on making assistant/agent tool execution observable and reliable from the inline assistant surfaces.

## Inline Agent Tools media-context fix

The inline **Generate Tool Plan From This Context** action now passes selected media IDs and image paths into `/api/agent-tools/plan`. This fixes VLM planner failures such as:

```text
VLM chat requires selected media or external image paths.
```

If the selected VLM still cannot plan because of model-specific prompt/input constraints, the planner logs the failure and retries with the configured orchestrator/default assistant model.

## Approved COA execution debug logging

Agent tool planning and execution now create JSONL debug logs under:

```text
runtime/agent_tools/logs/
```

Debug logs include:

- planner request payload
- selected model and runtime settings
- model planner errors and fallback attempts
- parsed tool-call payloads
- per-step COA execution start/end/failure events
- command/script subprocess args
- stdout/stderr/return code
- timeout/cancellation events
- Python venv creation and pip install logs

The **Agent Tools** tab and inline assistant panels expose recent debug logs and allow opening the log contents from the UI.

## Approve + Run buttons

Buttons labeled **Approve + Run** now count as the explicit user approval for that reviewed COA. High-risk actions still require the high-risk checkbox and the exact confirmation text:

```text
RUN HIGH RISK ACTION
```

## Python scripts with requirements

Generated Python tool calls can now include:

```json
{
  "tool": "run_python_script",
  "arguments": {
    "script": "import requests\nprint(requests.get('https://example.com').status_code)",
    "requirements": ["requests"],
    "create_venv": true
  }
}
```

The parser also detects requirements from script comments and fenced requirements blocks, such as:

```python
# requirements: pillow requests
```

When requirements are present, the app creates or reuses an isolated venv under:

```text
runtime/agent_tools/venvs/
```

It installs the requirements with pip before running the script, then records all pip output in the debug log.

## Startup tool smoke test

On startup, Agent Tools can run small smoke tests for detected local tools:

- Python
- PowerShell / pwsh on Windows
- CMD on Windows
- Bash/sh on Linux/macOS
- Docker, if installed
- Firefox path detection

Results are saved to:

```text
runtime/agent_tools/tool_smoke_test.json
```

They are shown in the Agent Tools status panel.

## GPU identity / Task Manager note

GPU cards now expose more identity information:

- CUDA id, such as `cuda:0`
- nvidia-smi index
- PCI bus id
- GPU UUID
- physical VRAM total
- driver-reported free VRAM
- app planning budget

Windows Task Manager GPU numbering may not match CUDA/nvidia-smi numbering. Use PCI bus id or UUID to confirm which physical GPU is being targeted.

The run/install/update scripts set:

```text
CUDA_DEVICE_ORDER=PCI_BUS_ID
```

This makes CUDA ordering more stable and easier to compare against `nvidia-smi`.

## Multi-GPU sharding validation

The placement planner still auto-switches `none` to `balanced` when multiple GPU IDs are selected. HF/Transformers-like LLM/VLM/chat models can now attempt Accelerate/Transformers device-map sharding even when the registry row was not explicitly marked `supports_sharding`, with a placement warning rather than a hard block.

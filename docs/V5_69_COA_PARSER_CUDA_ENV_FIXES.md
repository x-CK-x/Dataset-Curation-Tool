# v5.69 — COA Parser, Tool-Result Relay, Chat Queue, and CUDA Environment Fixes

This release focuses on two failure clusters reported during Tag Editor assistant testing:

1. Approved COA/tool plans that were visibly present in the assistant response but were not detected or executed.
2. CUDA/GPU visibility and VRAM reporting issues after selecting multiple GPUs for model loading/sharding.

## COA/tool-call parsing fixes

The Agent Tools parser now uses balanced JSON extraction instead of depending only on simple regular expressions. This lets it detect executable tool plans embedded inside normal assistant prose, including responses with trailing model tokens such as `<turn|>`.

Supported forms include:

```json
{
  "tool_calls": [
    {
      "tool": "run_shell_command",
      "arguments": {
        "shell": "powershell",
        "command": "Get-Content -Path \"C:\\Users\\<USERNAME>\\Downloads\\<YOUR_IMG>.download.json\" -Raw"
      },
      "risk": "high",
      "requires_approval": true
    }
  ]
}
```

The parser is also more tolerant of model-generated JSON that contains Windows paths or command strings with imperfect escaping. It attempts a safe recovery pass for common command-line quoting mistakes before falling back to fenced-code/labeled-line parsing.

## Tool output is now imported into the conversation

Approved COA execution now writes the tool result back into the application conversation before any relay-back model call happens. This matters because the tool may execute correctly even if the selected VLM fails during the follow-up relay.

The conversation now receives a `tool` message containing:

- selected COA index
- command/script step summary
- return codes
- stdout/stderr excerpts
- debug log paths
- execution result JSON

That means command output is preserved inside the chat transcript and can be sent back to the model on the next step.

## COA job watcher and UI recovery

After pressing **Approve + Run**, the frontend now watches the queued COA job. When the job completes, fails, or is cancelled, the UI refreshes the conversation and Agent Tools debug logs so the tool-result message becomes visible without manual page refresh.

If a chat queue or assistant panel gets stuck in a local sending state, the chat UI now exposes an **Unlock / Clear Pending** control. This clears the frontend pending-message lock without deleting backend jobs or logs.

## CUDA/GPU clean-install fixes

The Windows and Linux run/install/update/verify scripts now clear accidental `CUDA_VISIBLE_DEVICES` masking by default. This helps avoid the case where NVIDIA tools see two physical GPUs but PyTorch only sees one CUDA device.

Advanced override behavior:

- Set `DCT_CUDA_VISIBLE_DEVICES=0,1` to intentionally choose visible CUDA devices.
- Set `DCT_ALLOW_TORCH_GPU_SUBSET=1` to allow PyTorch to see fewer GPUs than `nvidia-smi` reports.
- Set `DCT_CLEAR_CUDA_VISIBLE_DEVICES=0` to preserve an existing external CUDA mask.

The app also clears CUDA masking before runtime GPU detection unless explicitly told not to.

## CUDA-enabled PyTorch verification is stricter

`scripts/check_torch_cuda.py` now compares:

- `torch.cuda.is_available()`
- `torch.cuda.device_count()`
- physical GPU count from `nvidia-smi`
- `CUDA_VISIBLE_DEVICES`
- `DCT_CUDA_VISIBLE_DEVICES`

If NVIDIA tools report two GPUs but PyTorch only exposes one, the verification script exits as failed so install/update scripts can repair the environment instead of leaving the app half-CUDA-ready.

## VRAM display/planning behavior

The model placement UI now separates:

- physical total VRAM
- driver-reported free VRAM
- app-reserved VRAM
- planning budget

By default, the planning budget uses full physical VRAM capacity unless strict driver-free checks or explicit max-memory overrides are enabled. This is intended to stop a 24 GB card from appearing as only roughly 22 GB because of a safety fraction being displayed as the physical amount.

## Files changed

Key files changed in this release include:

```text
data_curation_tool/services/agent_tools_service.py
data_curation_tool/static/app.js
data_curation_tool/static/styles.css
data_curation_tool/services/model_service.py
data_curation_tool/app.py
scripts/check_torch_cuda.py
run.bat
install.bat
update.bat
install_torch_cuda128.bat
verify_gpu.bat
run.sh
install.sh
update.sh
verify_gpu.sh
tests/test_v569_coa_parser_cuda_env.py
```

## Testing notes

The targeted regression set for this patch verifies:

- tool-call JSON embedded in prose is detected
- malformed Windows command JSON is recovered when possible
- tool results are imported into conversation storage
- startup scripts clear accidental CUDA masking
- CUDA verification compares PyTorch-visible GPUs against NVIDIA-visible GPUs

# v5.65 Approved COA Execution, Context Budget, GPU, and Download Fixes

This build hardens the assistant/orchestrator workflow so approved plans can be executed by the app without requiring the user to manually copy/paste commands.

## Approved COA execution from chat messages

Assistant messages can now be parsed for one or more executable COA options. The parser accepts strict JSON tool calls, JSON `steps`/`actions`/`options`, fenced code blocks, and labeled lines such as `PowerShell:`, `CMD:`, `Bash:`, or `Python:`.

After a user approves one COA option, the app executes the parsed steps in sequence through the existing visible Jobs system, captures stdout/stderr/results, and can relay those results back into the same assistant conversation. This means the correct flow is now:

1. Model proposes one or more COAs.
2. User clicks the COA parse/find control.
3. User enables approved COA execution and approves the next action.
4. User clicks the selected `Approve + Run ...` COA button.
5. The app runs the steps as jobs and feeds the result back to the assistant.

The model is no longer expected to decide, after the fact, whether it is allowed to run tools. The app owns execution after explicit approval.

## Tool/binary detection

Agent Tools status now reports detected local tool binaries, including Python, PowerShell, CMD, Bash/sh, Docker, and Firefox where available. This information is included in planning prompts so local models see the concrete execution environment and should stop claiming that local tool use is impossible merely because they are a model.

## Multiple COA options

The UI can now show multiple parsed COA options from a single assistant response. Each option gets its own approval/run button, so the user can choose which course of action to run.

## Context/token pressure indicator

Assistant chat panels now show an estimated context budget ring. It displays estimated tokens used out of the model context limit. When context pressure approaches the limit, the backend automatically condenses older chat history into a compact memory summary before the next model call.

The summary is hard-capped so it cannot become too large to fit back into context and create an infinite condensation loop.

## Download queue size visibility

The Models tab now shows an active/queued model-download size summary. Model download jobs also carry estimated total and remaining GB when catalog metadata or local files can provide it. This helps the user understand disk-space pressure before large downloads consume the drive.

## Model filter refresh behavior

The Models tab refresh button now preserves the active model category filter and refreshes the filtered list instead of losing the selected category.

## GPU and VRAM reporting

GPU discovery now merges Torch-visible GPUs with `nvidia-smi`-visible GPUs. If Torch only sees `cuda:0` but `nvidia-smi` sees `cuda:1`, the second GPU is still shown with a warning that it is not currently Torch-visible.

The UI now distinguishes physical total VRAM from driver-free VRAM and app planning budget. By default, placement planning uses the full physical VRAM capacity unless the user applies explicit strict driver-free checks or max-memory limits.

# v5.8.34 — Graph Edges, Model Lifecycle, ONNX Runtime, and Workflow Certification

## Scope

This release is a reliability correction for four regressions reported after v5.8.33:

1. Agentic Graph Editor nodes rendered, but graph edges were invisible.
2. Model load/unload jobs and lifecycle circles did not appear promptly.
3. Selected GPU placement could be ambiguous when `device` and `device_ids` disagreed.
4. PixAI/WD model loading failed because of a damaged ONNX Runtime namespace or migrated WD folders containing only the official safetensors payload.

It also reviews and expands the baseline Agentic Graph workflows so users can validate the graph runtime before introducing external dependencies.

## Agentic Graph edge rendering

The graph world is 10,000×10,000 pixels and the SVG uses this view box:

```text
-5000 -5000 10000 10000
```

The prior SVG element started at canvas position `0,0`, which made world-coordinate paths render approximately 5,000 pixels away from nodes. v5.8.34 offsets the physical SVG to `left:-5000px; top:-5000px`, so SVG world `0,0` and node world `0,0` align. Edge selection and delete handles retain their existing pointer behavior.

## Immediate model load/unload lifecycle

The frontend no longer performs a synchronous `/api/models/placement/plan` request before creating a load job. Placement validation and VRAM reservation already occur inside the queued load worker, so the blocking preflight was redundant and could leave the interface without a job/status for one or two minutes.

New behavior:

- A queued lifecycle state appears immediately after click.
- `/api/models/load` or `/api/models/unload` is called immediately.
- The returned job ID is inserted into the local Jobs state immediately.
- A dedicated lifecycle watcher polls that job and patches the circle/status in place.
- Full Models-tab rendering is deferred until terminal completion/failure/cancellation, preserving user interaction and scroll position.
- Load/unload failure text is retained on the lifecycle stage.

The separate **Check VRAM / Placement** action remains available for users who want an explicit preflight.

## GPU assignment validation

Frontend placement requests are normalized:

```text
device_ids=[1] + device=auto  -> device=cuda:1, device_ids=[1]
device=cuda:0 + device_ids=[] -> device=cuda:0, device_ids=[0]
```

Conflicting requests such as `device=cuda:0` with `device_ids=[1]` now fail immediately with an actionable error. The backend repeats this validation so API clients cannot bypass it. Single-GPU adapters receive the selected `cuda:N`; sharded adapters retain all selected IDs.

## ONNX Runtime namespace repair

Added:

```text
scripts/repair_onnxruntime_runtime.py
```

The script validates the actual imported API rather than trusting wheel metadata. It checks:

- concrete `onnxruntime.__file__`;
- callable `onnxruntime.InferenceSession`;
- callable `onnxruntime.get_available_providers`;
- installed `onnxruntime` and `onnxruntime-gpu` distributions;
- conflicting CPU/GPU wheels sharing one Python namespace.

When repair is required, it removes both wheels, force-reinstalls a clean ONNX Runtime GPU wheel; v5.8.35 supersedes this with `onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23`, and validates from a fresh Python interpreter. Install/update scripts run the repair before and after requirements installation.

For existing Windows installs, run:

```bat
update.bat
```

The repair script can also be run directly:

```bat
python scripts\repair_onnxruntime_runtime.py --ensure-gpu
```

## Isolated PixAI/WD loader repair

The new behavior remains isolated to these five rows:

```text
pixai-tagger-v09
wd-convnext-tagger-v3
wd-eva02-large-tagger-v3
wd-swinv2-tagger
wd-vit-tagger
```

The adapter now:

- validates the ONNX Runtime API before creating a session;
- requires `CUDAExecutionProvider` when a CUDA device is explicitly assigned;
- passes the selected CUDA device ID to the provider;
- verifies the created session actually activated CUDA;
- uses the official WD ONNX preprocessing contract for ONNX files;
- loads official WD `model.safetensors` + `config.json` through timm when ONNX is absent or unusable;
- verifies PyTorch parameters landed on the requested `cuda:N` device;
- uses the model config’s input size, mean, and standard deviation for the safetensors path;
- reports the actual runtime (`onnxruntime` or `timm_safetensors`) in prediction metadata.

PixAI’s public DeepGHS row remains ONNX-based unless a compatible safetensors payload is present. WD catalog downloads now include both ONNX and safetensors candidates, and integrity rules accept either runnable WD weight format plus `selected_tags.csv`.

No preprocessing or loading code for the confirmed-working Thouph/legacy taggers was changed by this adapter.

## Certified Agentic Graph workflows

The reviewed catalog now contains six certified local dry-run templates:

```text
guaranteed_graph_runtime_smoke_test
guaranteed_empty_branch_readiness_workflow
guaranteed_multimodal_manifest_preview
certified_tag_normalization_preview
certified_dataset_qa_export_plan
certified_closed_loop_training_improvement_preview
```

The closed-loop preview is derived from the larger supplied training-improvement graph, but is intentionally acyclic for baseline certification. It exercises evaluation, parallel data/hyperparameter planning, join/merge, review planning, and trainer-handoff preview. Its output records the intended feedback target; a real feedback edge should only be added after the baseline passes and after iteration limits/approval/rollback policies are configured.

New endpoint:

```text
POST /api/graph-editor/templates/self-test
```

The self-test:

- constructs each template through the same backend builder used by the GUI;
- validates node/edge/workflow conversion;
- runs the same graph runtime used by the canvas;
- disables live model calls, network access, unsafe approvals, browser/shell/MCP actions, media mutation, and trainer execution;
- verifies every enabled node completed;
- returns per-template pass/fail details.

The **Agentic Workflow READMEs** tab now includes **Self-Test Selected** and **Self-Test All Certified Workflows** actions.

## New workflow documentation

```text
docs/agentic_workflows/certified_tag_normalization_preview.md
docs/agentic_workflows/certified_dataset_qa_export_plan.md
docs/agentic_workflows/certified_closed_loop_training_improvement_preview.md
```

## Validation boundary

The certified templates are validated for their local dry-run contract. A graph that is later edited to call a real model, trainer, downloader, browser, shell command, MCP server, or media-processing dependency must be validated with that dependency configured. The package tests do not substitute for live browser interaction, real CUDA allocation, actual ONNX inference, or full external trainer execution on the user’s workstation.

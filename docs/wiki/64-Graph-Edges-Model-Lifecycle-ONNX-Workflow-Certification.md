# v5.8.34: Graph Edges, Model Lifecycle, ONNX Runtime, and Workflow Certification

## What this release fixes

- Agentic Graph Editor edges now share the same world-coordinate origin as nodes and render on the canvas.
- Model load/unload creates visible jobs and lifecycle-circle updates immediately instead of waiting for a blocking placement preflight.
- Selected GPU IDs are normalized into an explicit `cuda:N` request and conflicting device settings are rejected.
- A new ONNX Runtime repair utility fixes the broken shared namespace that can import without `InferenceSession`.
- PixAI/WD loading remains isolated from working legacy taggers and supports official WD safetensors folders when a migrated folder has no ONNX file.
- Six local dry-run Agentic Graph templates can be self-tested from the GUI.

## Repair an existing ONNX Runtime installation

From the project root, run:

```bat
update.bat
```

Or run the focused repair directly:

```bat
python scripts\repair_onnxruntime_runtime.py --ensure-gpu
```

The script removes conflicting CPU/GPU ONNX Runtime wheels, installs a clean GPU wheel, and validates `InferenceSession` and provider discovery in a fresh Python process.

## Verify the workflows

1. Start the application.
2. Open **Agentic Workflow READMEs**.
3. Click **Self-Test All Certified Workflows**.
4. Confirm the result reports all six templates passed.
5. Select a workflow and click **Create + Run Certified Dry-Run**.
6. Open the created graph in **Agentic Graph Editor** and inspect node/edge rendering and node results.

These certified runs do not use a model, GPU, network request, trainer, browser, shell command, MCP tool, or source-media mutation.

## Verify model lifecycle and placement

1. Open **Models**.
2. Select the intended GPU ID.
3. Click **Load Into Memory**.
4. Confirm a queued job and load circle appear immediately.
5. Open the job details and verify the request and placement both identify the intended `cuda:N` device.
6. After load, verify the model row reports the actual placement.
7. Click **Unload** and confirm the unload state/job appears immediately.

The separate **Check VRAM / Placement** button remains available when a preflight is desired.

## WD/PixAI local payloads

A complete WD model folder may use either:

```text
model.onnx + selected_tags.csv
```

or:

```text
model.safetensors + config.json + selected_tags.csv
```

PixAI’s public DeepGHS export uses:

```text
model.onnx + selected_tags.csv
```

Use **Models → Rescan / Reconcile Migrated Models** after copying model folders from an older install.

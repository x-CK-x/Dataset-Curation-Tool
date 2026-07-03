# Jobs, Queues, and Troubleshooting

<!-- DCT_VISUAL_START -->
![Jobs, queues, and troubleshooting visual guide](assets/images/jobs_queues_troubleshooting.png)
<!-- DCT_VISUAL_END -->


The **Jobs** tab is the operational log and control center for long-running tasks.

## Job types

Common job types include:

- Import.
- Downloads.
- Model downloads.
- Annotation model downloads.
- Model loading.
- Model unloading.
- Inference.
- Tag dictionary sync/import.
- Migration.
- Code Assistant patch operations.

## Queue lanes

Long-running tasks use queue lanes so one type of work does not lock the whole app.

Typical lanes:

| Lane | Purpose |
| --- | --- |
| model_download | Large model downloads. |
| download | Generic downloads and tag exports. |
| model_load | Loading/unloading models. |
| model_inference | Inference/chat/tag-selection work. |
| general | Other background jobs. |

## Controls

| Control | Use |
| --- | --- |
| Stop Checked Jobs | Cancel selected queued/running jobs cooperatively. |
| Stop Queued/Running Downloads | Stop download-like jobs. |
| Pause Checked | Pause selected pausable jobs. |
| Resume Checked | Resume selected paused jobs. |
| Pause Downloads | Pause all download-like jobs. |
| Resume Downloads | Resume download-like jobs. |
| Retry from scratch | Repair a failed/cancelled download job. |
| Copy Error | Copy detailed failure payload. |
| Open Details | Inspect full job metadata/logs. |

## Cooperative cancellation

A queued job can stop immediately. A running job stops when the worker reaches a cancellation checkpoint.

Large file transfers may not stop at the exact instant you press the button.

## Common errors

### 422 validation error for blank runtime values

This means a frontend/runtime control sent an empty string where the API expected a literal value. Current builds normalize blanks to defaults such as `auto`, `none`, and `transformers`.

### Model adapter is not available

The model exists in the catalog, but no concrete adapter is registered for loading/inference. Use a model with a supported adapter or add one.

### Missing `chat_template.jinja` or processor files

Older downloads may have fetched weights but skipped support files. Use **Re-download / Update** to repair lightweight files.

### VRAM estimate exceeds available capacity

Options:

- Select more GPUs.
- Use 8-bit or 4-bit quantization.
- Use CPU/cloud.
- Unload another model.
- Reduce max-memory reservation.
- Pick a smaller model.

### Unload did not visibly reduce VRAM

Try:

1. Wait a few seconds.
2. Refresh model/device status.
3. Check whether another loaded model is still resident.
4. Inspect job details for unload errors.
5. If a library allocator is caching memory, run another unload or restart as a last resort.

### Browser opens but app is blank

Hard-refresh with `CTRL+F5`. If still blank, check browser Console. Modern builds include module-aware validation and visible startup error panels.

## What to send when reporting an issue

Copy:

- Job JSON/details.
- Error panel raw payload.
- Model name.
- Selected GPU IDs.
- Quantization/dtype/runtime settings.
- Whether the model was migrated, downloaded fresh, or symlinked.
- Whether it loaded but failed at inference, or failed at load.

## Recovery workflow

1. Open Jobs.
2. Copy error details.
3. Retry failed downloads from scratch when appropriate.
4. Repair/update partial model folders.
5. Rescan Models.
6. Verify GPU.
7. Try a smaller known-good model to isolate app vs model-family issues.

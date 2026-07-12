# v5.8.33 — Download Progress and Guaranteed Agentic Graphs

## Summary

This update fixes model-download lifecycle progress visibility and adds known-good Agentic Graph templates with rendered READMEs inside the application.

## Model-download progress fixes

- Hugging Face `snapshot_download` now uses a DCT-aware tqdm wrapper that forwards byte/item progress into the job and model lifecycle progress callback.
- The Models tab now starts a dedicated watcher for model download jobs, updates the download circle while the job is running, and forces a Models panel refresh when the job completes, fails, or is cancelled.
- Model-service lifecycle reconciliation now checks whether a local payload is complete before leaving a download stage stuck in `queued` or `running`.
- `Load Into Memory` now reconciles the local payload before rejecting a load because a stale download stage is active.
- After a download finishes, the model catalog is reconciled and invalidated so newly downloaded ONNX/tagger repos become visible as downloaded immediately.

## Guaranteed graph templates

The following templates are added to the Graph Editor catalog and to the new **Agentic Workflow READMEs** tab:

1. `guaranteed_graph_runtime_smoke_test`
2. `guaranteed_empty_branch_readiness_workflow`
3. `guaranteed_multimodal_manifest_preview`

These are deliberately local-only and dry-run-safe. Their first-run purpose is to confirm graph runtime reliability before adding live models, media probing, source downloads, MCP calls, shell commands, browser automation, trainer handoffs, or mutating dataset steps.

## New UI tab

A new **Agentic Workflow READMEs** tab renders the workflow documentation and includes buttons to:

- create a known-good graph template,
- create and immediately run a runtime smoke test,
- run the last created template in dry-run runtime mode,
- open the created graph in the Agentic Graph Editor.

## Operational note

The templates are designed to work in graph runtime dry-run mode. They are not a claim that every external provider, trainer, GPU runtime, or edited downstream node will work after the user expands the graph. They are known-good baselines for isolating graph/runtime issues from external integration issues.

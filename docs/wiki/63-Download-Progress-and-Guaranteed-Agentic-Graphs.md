# v5.8.33 — Download Progress and Guaranteed Agentic Graphs

v5.8.33 focuses on two reliability issues: model-download progress circles and safe first-run Agentic Graph templates.

## Model-download progress

Hugging Face snapshot downloads now forward progress into the app job/lifecycle system, and the Models tab watches download jobs directly. This keeps the circular download progress indicator moving during the download and marks the model complete when the local payload is ready.

The loader also reconciles completed local payloads before blocking a load on an apparently active download. This prevents a model such as a small ONNX tagger from staying stuck behind a stale running download stage after its files already exist.

## Known-good graph templates

The Graph Editor catalog now includes:

- `guaranteed_graph_runtime_smoke_test`
- `guaranteed_empty_branch_readiness_workflow`
- `guaranteed_multimodal_manifest_preview`

These templates are intentionally conservative. They should be run first in runtime dry-run mode so the user can confirm the graph runtime is healthy before adding live model calls, media files, source downloads, browser actions, MCP calls, shell commands, or trainer integration.

## Agentic Workflow READMEs tab

The new **Agentic Workflow READMEs** tab renders instructions for each baseline workflow and provides create/run buttons. Each README explains what the workflow does, what to expect, and what manual steps are required before expanding it.

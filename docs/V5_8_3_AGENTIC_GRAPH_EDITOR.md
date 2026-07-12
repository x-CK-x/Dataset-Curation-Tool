# v5.8.3 Agentic Graph Editor

Version `5.8.3` adds a visual graph-authoring layer on top of the Automation Workflows engine.

The goal is to make advanced orchestration more approachable while still preserving the safe execution rules already used by workflow automation. Users can build graphs manually, ask the selected assistant/orchestrator model to draft a graph from a goal, refine the graph cooperatively, convert the graph into an Automation Workflow, dry-run it, and queue it through the Jobs system.

## What was added

- New **Agentic Graph Editor** tab.
- Persistent graph storage under `runtime/agentic_graphs/`.
- Graph JSON contract with `nodes`, `edges`, layout coordinates, node config, Mermaid preview text, metadata, and validation results.
- Node palette for dataset curation orchestration tasks.
- Visual graph canvas with clickable nodes and explicit edge creation/removal controls.
- Node inspector for editing node kind, workflow mapping, approval flags, enabled state, and node config JSON.
- Model-planning endpoint that lets the selected assistant/orchestrator model draft graph JSON from a user goal.
- Model-refinement endpoint that lets the selected model revise an existing graph from user instructions.
- Import existing Automation Workflow as a graph.
- Convert graph to Automation Workflow preview.
- Save graph as Automation Workflow.
- Dry-run graph through the workflow backend.
- Queue graph run through the Jobs tab.
- Recent graph run manifests.

## API routes

```text
GET    /api/graph-editor/catalog
GET    /api/graph-editor
POST   /api/graph-editor
GET    /api/graph-editor/runs
POST   /api/graph-editor/plan
GET    /api/graph-editor/{graph_id}
PUT    /api/graph-editor/{graph_id}
DELETE /api/graph-editor/{graph_id}
POST   /api/graph-editor/{graph_id}/refine
POST   /api/graph-editor/{graph_id}/validate
POST   /api/graph-editor/{graph_id}/to-workflow
POST   /api/graph-editor/{graph_id}/save-as-workflow
POST   /api/graph-editor/{graph_id}/dry-run
POST   /api/graph-editor/{graph_id}/run
POST   /api/graph-editor/import-workflow/{workflow_id}
```

Compatibility aliases for older local graph-editor tooling are also exposed under `/api/graphs/*`, including `/api/graphs/catalog`, `/api/graphs/plan`, `/api/graphs/{graph_id}/compile`, `/api/graphs/{graph_id}/dry-run`, and `/api/graphs/{graph_id}/run`.

## Graph execution model

The graph editor does not create a second execution engine. It compiles visual graph nodes into the existing Automation Workflow format, then runs through the same workflow service and Jobs queue.

This matters because:

- unsafe/expensive steps keep approval gates;
- global dataset originals remain read-only;
- branch sidecars and branch-local variants remain the normal write target;
- dry-runs and run manifests behave consistently with Automation Workflows;
- future orchestrator models can edit one shared graph/workflow contract instead of separate incompatible formats.

## Node categories

The initial graph palette includes nodes for:

| Category | Examples |
|---|---|
| Control | start/user goal, manual review gate |
| Model/orchestration | assistant plan, assistant label refinement |
| Global dataset | create/update branch, ingest/link dataset |
| Downloader | sync tag dictionary, download/query source data |
| Selection | character-reference rank/prune |
| Labeling | build label rules, dry-run label rules, apply label rules |
| Augmentation | plan augmentations, create branch-local variants |
| Regularization | plan regularization/prior images |
| Quality/export | evaluate branch, export branch |
| Tool handoff | trainer handoff, remote dispatch, MCP/tool command nodes |

## User, model, and cooperative editing

The graph JSON is intended to be shared between the user and the selected orchestrator model. The user can edit nodes visually, edit raw JSON directly, or ask the model to generate/refine the graph. The model-generated output is validated before conversion or execution.

Recommended workflow:

1. Select a template and fill in branch/model/dataset goal fields.
2. Write the desired dataset outcome in plain language.
3. Generate a graph plan.
4. Inspect every node and approval flag.
5. Dry-run the graph.
6. Convert/save it as an Automation Workflow if it is reusable.
7. Queue the graph or workflow only after validation and dry-run output look correct.

## Safety notes

Graph nodes that can download data, mutate branch sidecars, generate augmented variants, run shell commands, dispatch remote workers, or trigger external tools should remain approval-gated by default. The graph editor is a planning and orchestration surface, not an unconditional command runner.

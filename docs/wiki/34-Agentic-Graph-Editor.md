# Agentic Graph Editor

The **Agentic Graph Editor** is a visual workflow builder for dataset-curation automation. It lets the user, the selected assistant/orchestrator model, or both together create custom orchestration graphs for downloading, pruning, labeling, augmentation, export, and tool handoff.

The editor builds on the Automation Workflows layer. A graph is converted into an Automation Workflow before it is dry-run or queued, so the same approval gates, branch-safe behavior, and run manifests are used.

## When to use it

Use the graph editor when a task is too complex for a single button but should still be repeatable:

- prepare a character LoRA branch from a large global dataset;
- download matching source data, dedupe it, then link it into a branch;
- run character-reference pruning before label cleanup;
- generate branch-local augmentation variants;
- evaluate branch readiness before export;
- hand off an export to a trainer, slicer, MCP tool, or remote worker;
- let an orchestrator model draft a curation plan and then edit it manually.

## Main areas

| Area | Purpose |
|---|---|
| Graph design controls | Select template, branch, target model, adapter type, dataset goal, and assistant model. |
| Model planning | Generate a graph from the user goal and instructions. |
| Graph canvas | View nodes and dependencies as a visual graph. |
| Node inspector | Edit the selected node kind, workflow mapping, approval flag, enabled flag, and config JSON. |
| Graph JSON | Directly edit the graph contract shared by the user and model. |
| Conversion/run controls | Validate, convert to workflow, save as workflow, dry-run, or queue a graph run. |
| Node palette | Review available node types and what workflow step each node compiles into. |
| Recent runs | Inspect graph run manifests. |

## Graph JSON contract

Graphs are saved as JSON under:

```text
runtime/agentic_graphs/
```

A graph contains:

```json
{
  "id": "graph_example",
  "name": "Character LoRA prep graph",
  "goal": "Prepare a branch for character LoRA training",
  "nodes": [
    {"id": "branch", "kind": "create_branch", "x": 40, "y": 40, "config": {"branch_name": "character_lora"}}
  ],
  "edges": [
    {"id": "edge_1", "from": "branch", "to": "rules", "label": "next"}
  ]
}
```

The `nodes` array defines work. The `edges` array defines ordering. The graph service validates node IDs, unknown node kinds, dangling edges, and cycles before conversion.

## Node palette

Common node types include:

| Node kind | Typical use |
|---|---|
| `start` | Store the user goal and starting context. |
| `assistant_plan` | Ask the selected assistant/orchestrator model to plan or revise the graph. |
| `manual_review_gate` | Require user approval before continuing. |
| `create_branch` | Create an editable branch over the global dataset. |
| `ingest_existing_dataset` | Register/link an existing dataset. |
| `sync_tag_dictionary` | Sync source-specific tag dictionaries before download/labeling. |
| `download` | Run source downloads or logic-query downloads. |
| `character_reference_rank` | Rank/prune by character reference without training a new model. |
| `build_label_rules` | Generate LoRA/IC-LoRA/ControlNet/embedding tag/caption rules. |
| `assistant_refine_labels` | Let a local/cloud model refine labels or captions. |
| `dry_run_label_rules` | Preview deterministic sidecar changes. |
| `apply_label_rules` | Write branch-sidecar changes. |
| `plan_augmentations` | Plan LoRA-specific branch variants. |
| `create_augmentation_variants` | Create approved branch-local variants. |
| `regularization_plan` | Plan prior/class/regularization images. |
| `evaluate_branch` | Compute readiness metrics. |
| `export_branch` | Export a training-ready dataset. |
| `trainer_handoff` | Build a trainer/tool handoff manifest. |
| `remote_dispatch_plan` | Split work across configured remote workers. |
| `shell_command` | Approved local/remote shell command placeholder. |
| `mcp_tool` | Approved MCP/tool action placeholder. |

## Model-created workflows

The selected assistant/orchestrator model can draft or refine graph JSON. The model is prompted to return structured graph JSON or workflow JSON. The graph editor then validates the result before it can be saved, converted, or run.

A practical pattern is:

1. The user describes the dataset goal.
2. The model drafts a graph.
3. The user edits nodes and approval gates.
4. The model refines only the parts the user asks it to change.
5. The user dry-runs the graph.
6. The user queues the graph through Jobs.

## Automation Workflow compatibility

Graph runs compile into Automation Workflow steps. This keeps one execution contract for both the workflow tab and graph tab.

Graph-only fields such as `x`, `y`, and visual labels are preserved in the graph file. Execution-relevant fields are copied into workflow step IDs, step types, approval flags, and params.

## Safety model

The graph editor should not bypass review for risky actions. Steps that can write files, download large amounts of data, generate many variants, call external tools, dispatch remote workers, or run shell commands should be approval-gated.

Global dataset originals remain untouched. Edits should happen through branch configs, branch sidecars, and branch-local variants.


## Compatibility API aliases

The primary API namespace is `/api/graph-editor/*`. Compatibility aliases are also exposed under `/api/graphs/*` for older local graph-editor style tools and scripts. These aliases use the same backend service and compile into the same Automation Workflow execution contract.

## v5.8.10 standalone-editor feature port

The integrated graph editor now includes the standalone editor's main workflow primitives without replacing the Data Curation Tool canvas style. Added behavior includes right-click node creation, canvas pan/zoom, port-based node connections, edge delete handles, flow animation, graph event-console messages, multimodal input nodes, bundle/context policy nodes, model call nodes, supervisor nodes, external HTTP/tool nodes, and browser search/open MCP nodes.

See [Agentic Graph Editor Standalone Port and Browser MCPs](40-Agentic-Graph-Editor-Standalone-Port-and-Browser-MCPs.md).

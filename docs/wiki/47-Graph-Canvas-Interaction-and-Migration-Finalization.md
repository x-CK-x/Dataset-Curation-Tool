# Graph Canvas Interaction and Migration Finalization

v5.8.17 repairs the graph editor interaction layer and reduces the apparent stall after migration/startup progress reaches 100%.

## Graph editor behavior

The Agentic Graph Editor now supports the direct-manipulation behavior expected from the standalone graph editor:

| Action | Behavior |
|---|---|
| Drag empty canvas | Pan around the graph world |
| Mouse wheel over canvas | Zoom around the cursor |
| Right-click empty canvas | Open the categorized node palette |
| Open Node Palette button | Opens the same palette without relying on browser context-menu behavior |
| Drag node card | Move the node |
| Drag output port to input port | Create an edge |
| Click output, then click input | Create an edge without dragging |
| Right-click node | Node-specific actions |
| Edge delete handle | Remove a connection |

The palette is driven by the same node contracts used by the backend graph/workflow compiler. If the backend catalog has not finished loading, the frontend falls back to standalone-style node contracts for text, image, audio, video, bundle/context, model call, supervisor, external tool, MCP tool, condition, parallel fanout, join, browser search/open, and output nodes.

## Migration finalization behavior

Large migrations can appear to stall after 100% when the app is serializing a large job result or when `/api/jobs` repeatedly decodes large historical `result_json` payloads.

v5.8.17 changes that behavior:

| Area | Change |
|---|---|
| Migration file details | Stored as a bounded sample instead of every file op |
| Job counters | Preserve `files_total`, `files_omitted`, `files_truncated`, and `files_result_limit` |
| Job list polling | Avoids full result JSON decoding |
| Job detail view | Still exposes the detailed result when opened explicitly |
| Tag cache reconciliation | Records active-profile reconciliation result |
| Dashboard progress | Shows final compact-result/reconciliation phase |

## Practical workflow

Use **Scan** before a large migration if you need the full detailed plan. Use **Run Migration** for the actual move/copy/symlink operation; the job result is now summarized so the Dashboard and Jobs page remain responsive.

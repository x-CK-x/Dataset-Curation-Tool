# Agentic Graph Editor Standalone Port and Browser MCPs

v5.8.10 expands the integrated Agentic Graph Editor with the standalone graph-editor concepts while keeping the existing Data Curation Tool visual style.

## What changed

The graph editor now has more node primitives, a richer canvas, a graph event console, and browser MCP nodes/tools. The goal is to let the user and the selected orchestrator model co-design curation workflows using nodes that match the real data-curation pipeline.

## Canvas controls

| Control | Behavior |
|---|---|
| Right-click canvas | Add the currently selected node kind at the pointer location |
| Drag node | Move node |
| Mouse wheel | Zoom canvas |
| Drag empty canvas | Pan canvas |
| Output port → input port | Connect nodes |
| Edge `×` handle | Delete edge |
| Animate Flow | Show moving edge-flow effect |
| Reset View | Reset pan/zoom |

## New graph node families

| Family | Examples |
|---|---|
| Inputs | text, image, audio, video, live stream |
| Context | bundle/context packer, join/merge |
| Models | model call, supervisor controller |
| Tools | external HTTP/tool call, browser search/open |
| Events | event bus publish, webhook/event trigger |
| Control | manual review, condition gate, parallel fan-out |
| Outputs | output artifact |

## Browser MCPs

The MCP Tools tab now lists local browser integrations:

- default system browser
- Microsoft Edge
- Google Chrome
- Firefox
- Chromium
- Tor Browser

Browser MCP actions are intended for visible, user-approved browsing and search handoff. They are not a webscraper implementation. Graph workflows can include browser nodes when the selected assistant/orchestrator needs the user’s enabled browser to look up information.

## Node inspector

Selecting a node shows type-specific settings. For example:

| Node | Inspector settings |
|---|---|
| Bundle | array/object mode, max items, max characters, limit policy, text-only filtering |
| Model call | model id, preset/card id, provider, prompt, input/output modalities |
| Supervisor | controller model, preset, plan mode, event channels, max spawns |
| External tool | base URL, path, method, headers JSON, body template, local-only guard |
| Browser | browser MCP target, URL/search query, search-engine template, private/incognito option |

## Automation workflow conversion

Graph nodes that map cleanly to existing automation workflow steps compile into those steps. Context-only nodes remain in the graph and Mermaid preview but do not create destructive workflow steps. Unsafe or external actions compile into approval-gated steps unless a deterministic safe workflow step exists.

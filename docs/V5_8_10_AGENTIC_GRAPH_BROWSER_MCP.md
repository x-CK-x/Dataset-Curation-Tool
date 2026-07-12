# v5.8.10 — Agentic Graph Editor Feature Port and Browser MCPs

This build expands the integrated **Agentic Graph Editor** using the standalone `agentic_graph_editor_complete` prototype as a feature reference while preserving the current Data Curation Tool dark/neon graph background, node shape, and visual theme.

## Integrated graph-editor features

The graph editor now supports additional standalone-style node primitives:

| Node kind | Purpose | Workflow conversion behavior |
|---|---|---|
| `text_input` | Manual/event/tool/graph-fed text source | context-only node |
| `image_input` | Image source or graph-fed image artifact | context-only node |
| `audio_input` | Audio source or graph-fed audio artifact | context-only node |
| `video_input` | Video/live-stream source | context-only node |
| `bundle_context` | Aggregates upstream artifacts with item/character limits | approval-gated workflow context step |
| `model_call` | LLM/VLM/tagger/model node using the app model catalog | maps to assistant/model refinement step |
| `supervisor_controller` | Coordinator node that can read event channels and limit downstream actions | maps to model-prompt planning step |
| `external_tool_call` | HTTP/local tool gateway node with local-only guard | approval-gated manual/tool step |
| `event_bus_publish` | Graph event-console publish node | approval-gated event step |
| `webhook_event` | Event/webhook trigger placeholder | context-only node |
| `live_stream_input` | Future stream/sensor input placeholder | context-only node |
| `condition_gate` | Conditional routing/checkpoint node | approval-gated workflow gate |
| `parallel_fanout` | Fork downstream branches or remote work | remote-dispatch planning step |
| `join_merge` | Merge branch outputs/context | approval-gated merge/checkpoint |
| `browser_search` | User-approved browser MCP lookup | approval-gated browser/tool step |
| `browser_open` | User-approved browser URL handoff | approval-gated browser/tool step |
| `output_artifact` | Terminal output/display node | context/output-only node |

## Canvas behavior

The integrated canvas adds the standalone editor interaction model:

- right-click canvas to add the selected node type;
- drag nodes to move them;
- mouse wheel zoom;
- drag empty canvas to pan;
- click output and input ports to connect nodes;
- delete edges with visible edge handles;
- optional flow animation toggle;
- node inspector sections for input streams, bundle limits, model calls, supervisor planning, external tool calls, events, and browser MCP actions.

## Graph event console

The Agentic Graph Editor tab now includes a session event console for prompts, alerts, tool messages, model messages, sensor events, and supervisor context channels. The event console is local/session-oriented in this build; graph JSON preserves channel names and supervisor-node configuration so automation workflows can later use the same contracts.

## Browser MCP tools

The MCP Tools registry now includes browser handoff entries for:

- `browser_default`
- `browser_edge`
- `browser_chrome`
- `browser_firefox`
- `browser_chromium`
- `browser_tor`

These are conservative browser handoff MCPs. They open a visible browser URL or search after user approval. They do not implement hidden scraping or bypass website controls. For deeper browser automation, the user should manually configure a separate browser profile and debugging endpoint, then keep approval gates enabled.

## MCP bridge additions

The bundled MCP bridge now exposes browser tools when launched with one of the browser MCP tool keys:

- `build_browser_command`
- `open_url`
- `search_web`
- `browser_control_note`

## Safety/approval model

Browser/search actions, external tool calls, shell-like tool steps, downloads, augmentation writes, exports, and trainer/tool handoffs remain approval-gated by default. This preserves the existing workflow safety model while allowing the orchestrator model and the user to co-design graph workflows.


## v5.8.10 user-interruption fixes

- Tab switching now uses a fixed viewport with `.main` as the scroll container and persists sidebar/main/window scroll state through `sessionStorage`.
- Manual asset migration mirrors progress into the Dashboard startup-maintenance indicator so a canceled first-run tag-sync/startup path can resume visibly when the user migrates assets later.
- Startup tag dictionary sync defaults to empty-only behavior so later launches avoid the heavy first-run tag download unless the user explicitly disables empty-only sync or the dictionary is missing.

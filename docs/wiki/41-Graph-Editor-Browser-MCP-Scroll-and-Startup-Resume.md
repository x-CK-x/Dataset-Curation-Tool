# Graph Editor, Browser MCPs, Scroll Persistence, and Startup Resume

This page documents the v5.8.10/v5.8.11 graph-editor and startup-maintenance updates.

## Graph editor port

The integrated Agentic Graph Editor keeps the Data Curation Tool visual style but adds the standalone editor's workflow concepts:

| Area | Added support |
|---|---|
| Inputs | text, image, audio, video, live-stream placeholders |
| Model nodes | model call, assistant planning, supervisor/controller |
| Context | bundle aggregation, item limits, character limits |
| Control flow | condition gates, parallel fanout, join/merge |
| Tools | external HTTP/local tool-call placeholders, MCP placeholders |
| Browser | browser search/open nodes with approval gates |
| Output | artifact/output terminal nodes |
| Runtime preview | local event-console/session events |

The graph can still be converted into an Automation Workflow for validation, dry-run, queued execution, and approval-gated execution.

## Browser MCP behavior

Browser MCP entries are provided for default browser, Edge, Chrome, Firefox, Chromium, and Tor Browser. The bridge opens visible URLs/searches after approval. Configure executable paths in MCP Tools when auto-detection does not find the desired browser.

## Tab scroll behavior

Tab switching now preserves the main scroll container and nested scroll regions. This is intended to stop the previous behavior where returning to a large Gallery, Models list, or Graph Editor view could snap back to the top.

## Startup maintenance after migration

If first-run tag sync was cancelled, the Dashboard maintenance card can become active again when you run Install Migration. After migration, the tool reconciles migrated models and tag-export caches, refreshes dictionary status, and only downloads/syncs tags if the active profile is still missing or stale.

Future launches should normally be much faster because first-run tag downloads are cache-aware and agent-tool smoke tests use their cached result by default.

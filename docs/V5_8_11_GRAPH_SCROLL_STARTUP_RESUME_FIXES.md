# v5.8.11 — Graph Editor Port Completion, Browser MCPs, Scroll Persistence, and Startup Maintenance Resume

This build preserves the existing dark/neon Agentic Graph Editor look while expanding it with the standalone graph-editor concepts from the provided prototype. It also fixes the persistent tab-scroll jump and makes Dashboard startup-maintenance progress resume when the user later runs Install Migration.

## Agentic Graph Editor improvements

The integrated graph editor now supports the standalone-style workflow primitives without embedding a separate Next/React app:

- multimodal input nodes for text, image, audio, video, and live-stream placeholders;
- model-call and supervisor/controller nodes;
- bundle/context aggregation nodes with item and character limits;
- condition, fanout, and join/merge control nodes;
- output artifact nodes;
- local/session event-console nodes;
- external tool-call placeholders;
- browser search/open nodes that compile to approval-gated tool steps.

The current Data Curation Tool canvas background, node styling, neon grid, node inspector style, and workflow-conversion layer are retained.

## Browser MCP targets

The MCP Tools registry now includes conservative browser handoff entries for:

- system default browser;
- Microsoft Edge;
- Chrome;
- Firefox;
- Chromium;
- Tor Browser.

These MCPs are visible/user-approved browser handoffs. They open URLs or searches in an installed browser when enabled and approved. Hidden scraping, bypassing site controls, and unapproved navigation are intentionally not implemented.

## Scroll persistence fix

The app shell now uses a dedicated scroll container for the active tab. Tab switching stores and restores:

- document scroll;
- sidebar scroll;
- main tab scroll;
- nested scroll areas such as tables, galleries, logs, graph canvas, and model lists.

The restore operation is delayed across multiple animation frames/timeouts so slow Gallery, Graph Editor, Models, and workflow panes do not jump back to the top after their DOM finishes rebuilding.

## Startup maintenance resume after migration

If the user cancels or interrupts first-run startup tag sync, the Dashboard progress card can resume when Install Migration is run later. Migration now mirrors its progress into the Dashboard startup-maintenance card and then performs post-migration reconciliation:

- migrated custom model catalog reload;
- migrated model-asset reconciliation;
- tag-export cache reconciliation;
- active tag dictionary status refresh;
- optional post-migration tag dictionary sync if the cache is still missing/stale and startup tag sync remains enabled.

## Faster future startup behavior

Agent tool smoke tests now use the cached smoke-test result by default instead of forcing a fresh shell/Python/PowerShell/Bash/Docker check every launch. First-run checks still create the cache, but future runs should skip that repeated cost unless the cache is removed or the user explicitly reruns checks.

# v5.8.46 Multi-Unload, Live Token Context, and Assistant Condensing

This update repairs the remaining Quick Tag multi-model unload path and restores live assistant feedback inside the Tag Editor.

## Quick Tag unload queue

- **Queue Unload Selected** now submits every highlighted model, not only the last clicked row.
- The frontend creates visible queued rows for all selected unload jobs immediately.
- The backend exposes `/api/models/unload-many` so batch unloads are handled as explicit jobs with per-model lifecycle updates.

## Tag Editor Assistant live token budget

- Assistant conversations now show a live circular context/token budget meter while the request is running.
- The meter updates from a client-side estimate until the backend returns the final context-budget payload.
- Visible planning/action notes remain on by default. The UI shows user-facing trace/status, not hidden/provider-private chain-of-thought.

## Automatic context condensing

- Chat requests default to automatic context condensation.
- If estimated context pressure approaches the configured threshold, the backend writes a compact memory summary, trims the live history window, and continues using the condensed state.
- The final response includes context-budget metadata indicating whether pre-condensing was used.

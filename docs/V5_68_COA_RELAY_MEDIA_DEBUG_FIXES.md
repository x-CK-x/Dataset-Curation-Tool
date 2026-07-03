# v5.68 COA Relay Media / Debug Fixes

This release fixes a failure where an approved COA/tool plan could run but the job failed during the relay-back step when the selected model was a VLM.

## Fixes

- COA execution and relay-back are now separate stages.
- A relay-back failure no longer marks the whole COA tool job as failed when the local tool steps completed.
- The relay step now extracts selected media IDs and image paths from assistant surface context and passes them explicitly to VLM chat.
- If relay to the selected model fails, the app tries configured orchestrator/assistant fallbacks and records the failure in the debug log.
- COA job results now include `relay_error`, `relay_targets`, and `debug_log_path` so failures can be inspected.
- Progress scaling now keeps tool execution below 100% until the relay stage finishes or reports a relay-only failure.

## Why this matters

A VLM adapter cannot infer image targets from a JSON context string alone. It needs explicit `media_ids` or `external_paths`. v5.68 provides those targets during COA relay and prevents relay-only errors from hiding the command stdout/stderr result.

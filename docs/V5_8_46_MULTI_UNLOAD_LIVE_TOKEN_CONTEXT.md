# Data Curation Tool Modern v5.8.46 — Multi-Unload, Live Token Context, Assistant Condensing

## Summary

v5.8.46 fixes the last Quick Tag unload multi-select path and restores live assistant token/context feedback in the Tag Editor.

## Changes

- Added `/api/models/unload-many` for explicit batch unload queueing.
- Added frontend `queueModelUnloadMany(...)` so all selected Quick Tag models receive visible unload placeholders and live job watchers.
- Hardened Quick Tag model-selection capture to include native selected options, queued-selection mirror flags, and persisted state.
- Added live token/context-budget estimation while Tag Editor Assistant chat requests are running.
- Opened visible reasoning/action-trace controls by default and kept the wording explicit that provider/private hidden chain-of-thought is not displayed.
- Enabled automatic context-condensing options by default on assistant chat requests and surfaced pre-condense metadata in responses.

## Validation

Validated with Python compile checks, frontend JavaScript syntax checks, shell syntax checks, targeted regression tests, and ZIP integrity verification.

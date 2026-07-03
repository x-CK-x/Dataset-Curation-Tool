# v5.57 Chat, Download Queue, and Migration UX Fixes

## Chat interface changes

The Tag Editor assistant and Code Assistant conversation history now render as a scrollable chat thread instead of a generic history list. User messages appear on the user side, assistant messages appear on the assistant side, and user messages expose an inline **Edit message** action. Editing a prior user message saves the replacement text and removes later turns so the conversation can continue normally from that exact point.

Both surfaces now include **Save current state**. For the Tag Editor, the saved state captures the current media IDs, active image path, tag profile, active tags, caption, prompt/criteria, and selected model. For the Code Assistant, the saved state captures the project root, selected files, filter, scan summary, selected model, and token profile.

Long conversations are automatically condensed into a persistent cached memory summary stored with the conversation. Future prompts include the cached memory plus a compact recent message window, instead of recursively embedding full prior message payloads.

## Model download queue controls

The Models tab now has an explicit model-download mode selector:

- **Serial queue: one model file transfer at a time**
- **Parallel transfers: split bandwidth across files**
- **Use Settings default**

Model download buttons are labeled as queue actions so it is clearer when a model will be downloaded through the job queue instead of starting unconstrained parallel transfers.

## Migration/status changes

Model support-file warnings are no longer treated as hard download-integrity failures. A folder with valid non-empty weights is shown as downloaded even if an older build omitted lightweight files such as chat templates or remote-code helpers. Those are now warnings that can be repaired by update/load logic, not `NEEDS REPAIR/UPDATE` badges.

Migration now keeps repairable Hugging Face model folders with unusual or stale sharded-index layouts instead of dropping the entire model folder. It still skips empty/temporary/zero-payload assets, but it prefers moving reusable model files into the new install so the newer runtime can repair or validate them in place.

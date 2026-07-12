# v5.8.47 Memory Guard, Assistant Model Tools, and Tag Pruning

v5.8.47 addresses long-running assistant sessions and closes the gap between the Tag Editor assistant and the actual tag-list state.

## What changed

- Automatic CPU offload is disabled by default to reduce the risk of exhausting system RAM during overnight model runs.
- Chat context/response payloads are compacted before storage.
- Conversation history loading uses bounded SQL substrings for JSON payloads.
- Condensed memory is expanded, copyable, downloadable, and no longer shown in a cramped compact log block.
- The Tag Editor assistant receives active Dataset Pipeline / LoRA rule context.
- Assistant tag-edit JSON can directly prune/update the active media tags.
- Approved assistant/orchestrator tool plans can queue model load, inference, unload, and wait-for-job operations through the shared queue.

## Assistant tag-edit JSON

The assistant should return fields like:

```json
{
  "keep_tags": ["1girl", "white_hair"],
  "remove_tags": ["wings", "weapon"],
  "add_tags": [],
  "final_tags": ["1girl", "white_hair"],
  "reason": "Removed tags that are not visible in the selected image."
}
```

When the Tag Editor checkbox for assistant tag edits/pruning is enabled, the backend applies the result to the selected media.

## Model queue tools

The assistant can propose tool calls that queue model operations. These remain user-visible and approval-gated. Queued jobs appear in the same model/job queue panels used by manual Quick Tag operations.

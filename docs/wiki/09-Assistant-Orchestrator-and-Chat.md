# Assistant, Orchestrator, and Chat

<!-- DCT_VISUAL_START -->
![Assistant, orchestrator, and chat visual guide](assets/images/assistant_orchestrator_chat.png)
<!-- DCT_VISUAL_END -->


The assistant can be a built-in fallback, a local LLM/VLM, or an API model. The orchestrator is the assistant-like model that can plan user-approved tool/model runs.

## Assistant vs orchestrator

| Role | Meaning |
| --- | --- |
| Assistant | The model you chat with for reasoning, explanations, tag help, captions, and dataset guidance. |
| Orchestrator | The model selected to propose or plan multi-step actions involving other models/tools. |

The same model can be both.

## Selecting the assistant/orchestrator model

Use the **Assistant** tab or assistant-enabled panels to:

- Select a downloaded/local/API LLM or VLM.
- Save it as the assistant default.
- Save it as the orchestrator default.
- Load or unload it.
- Select GPU placement.

Assistant-enabled surfaces include Tag Editor, Batch Tags, Compare, Assistant, Orchestrate, and Code Assistant.

## User-approved orchestration

The orchestrator can recommend:

- Which models to run.
- Which GPUs to use.
- Whether a model should be sharded.
- Which dtype/quantization to choose.
- Warnings about VRAM or missing downloads.

Model runs should require explicit user approval before queueing. This prevents the assistant from unexpectedly launching expensive or destructive jobs.

## Chat history

Chat history is stored by conversation.

Supported operations:

- Continue normal conversation.
- Edit a previous user message and continue from that point.
- Delete a message.
- Delete from a message onward.
- Clear visible chat.
- Clear condensed memory.
- Switch models mid-conversation while preserving context.

## Memory and context condensation

Long conversations are condensed into persistent memory so the model does not lose important state when the raw message history grows too large.

The model receives:

- Condensed memory summary.
- Recent full turns.
- Current image/project state.
- Current tags/captions/metadata when relevant.
- Selected files/context for code workflows.

## Finish Last Output

Use **Finish Last Output** when a model stops mid-sentence, mid-list, or mid-code block.

The follow-up request instructs the model to continue from the previous answer without repeating already shown text.

## Tag selection and action completion

For critical tag operations, the assistant is asked to include:

```text
[TASK_COMPLETE]
```

If missing, the backend attempts continuation. Destructive apply operations are blocked when the result still appears incomplete.

## Common assistant tasks

### Validate existing tags

```text
Look at the image and validate existing tags by selecting the ones that match and/or are present in the image.
```

### Find missing tags

```text
List missing visible tags. Separate high-confidence tags from uncertain tags.
```

### Prune tags

```text
Remove tags that are not visible or not supported by the current image. Explain uncertain removals.
```

### Caption image

```text
Write a concise caption using the visible image content and the current tag list as context.
```

### Discuss dataset quality

```text
Analyze the current image and tags. Tell me what is inconsistent, redundant, missing, or risky.
```

## Best practices

- Preview before applying tag changes.
- Use clear criteria for prune/keep-only operations.
- Use Finish Last Output when a response appears incomplete.
- Use smaller local models for quick drafts and larger/cloud models for verification.
- Keep token profiles separated by provider and usage type.

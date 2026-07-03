# Code Assistant

<!-- DCT_VISUAL_START -->
![Code Assistant workflow visual guide](assets/images/code_assistant_workflow.png)
<!-- DCT_VISUAL_END -->


The **Code Assistant** tab is a project-aware coding workspace for using local/API LLMs against an existing codebase.

## Goals

The Code Assistant is designed to help with:

- Reading and summarizing a codebase.
- Debugging errors.
- Planning changes.
- Creating patches.
- Applying approved unified diffs.
- Keeping persistent project conversation history.
- Switching models mid-conversation.

## Basic workflow

1. Open **Code Assistant**.
2. Pick a project root.
3. Scan files.
4. Select files to include as context.
5. Select a coding model and token profile if needed.
6. Ask a question or request a patch.
7. Review the response.
8. Apply patch only after explicit approval.

## Chat interface

The Code Assistant chat supports:

- Scrollable history.
- User/assistant message layout.
- Editing earlier user messages.
- Deleting messages.
- Deleting from a message onward.
- Clearing chat.
- Clearing memory.
- Saving project state.
- Finish Last Output.

## Memory and context

The assistant should not blindly send the entire project every time. It uses:

- Selected files.
- Scan summaries.
- Conversation history.
- Condensed memory.
- Recent turns.
- Current model and token profile.

## Applying patches

Patch application uses unified diff behavior and creates backups under:

```text
.dct_code_backups/
```

Recommended patch workflow:

1. Ask for a plan first.
2. Ask for a patch second.
3. Review patch content.
4. Apply patch.
5. Run tests.
6. Ask the assistant to inspect failures.

## Good prompts

```text
Scan this project and explain the main architecture. Focus on where the API routes, services, frontend, and tests live.
```

```text
Here is the error log. Identify likely root cause and propose a minimal patch.
```

```text
Create a patch for this feature, but do not remove existing functionality.
```

```text
Review the selected files for places that could break the frontend module loader.
```

```text
Continue the previous answer from where it stopped without repeating already shown text.
```

## Best practices

- Keep selected context focused.
- Prefer small patches over massive rewrites.
- Run tests after every patch.
- Keep backups.
- Use a stronger model for architecture-level changes and a smaller local model for quick local Q&A.
- Do not apply generated patches blindly.

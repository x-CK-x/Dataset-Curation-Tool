# v5.58 Chat Composer and Completion Guards

This patch improves the Tag Editor and Code Assistant chat workflow for long local-model responses and actionable tag operations.

## Chat UI

- The Tag Editor assistant conversation now has a bottom composer for normal chat about the current image, tags, captions, metadata, and model outputs.
- The Code Assistant conversation uses the same bottom-composer pattern for project chat.
- Both composers include a **Finish Last Output** button. This asks the selected model to continue the previous assistant answer without repeating text already shown.
- Conversation requests send persisted compact memory, recent conversation turns, and the current saved state so the model keeps continuity without recursively bloating context.

## Completion mitigation

Local models can stop mid-sentence or mid-list when they hit the output budget. v5.58 adds:

- higher minimum output budgets for chat/code/tag tasks;
- automatic continuation attempts when an answer appears incomplete;
- de-duplication when a continuation repeats part of the previous answer;
- explicit continuation metadata in API results.

## Actionable tag-task guard

LLM/VLM tag selection, pruning, keep-only, set, and add operations now request a `[TASK_COMPLETE]` sentinel from the model. If the sentinel is missing, the backend performs continuation/verification rounds before returning. For non-preview operations, the backend blocks file/tag modifications when the response still appears incomplete after continuation attempts.

This prevents half-completed model responses from being silently applied to tags.

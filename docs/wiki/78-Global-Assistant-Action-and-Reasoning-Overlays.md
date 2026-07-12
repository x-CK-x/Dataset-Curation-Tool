# v5.8.48 Global Assistant Action and Reasoning Overlays

v5.8.48 adds two active-only overlays that remain visible from any tab while an assistant-capable model is running.

## Live action notes

Shows current execution status such as context collection, token-budget checks, tool/model-queue decisions, job waiting, parsing, and application of approved actions.

## Live chain-of-thought / reasoning trace

Shows a separate user-visible reasoning trace stream by default. This is the app/model-visible reasoning contract and runtime trace. Provider/private hidden reasoning is not extracted or claimed to be available.

## Defaults

The following settings default to enabled:

```text
assistant_show_live_action_notes = true
assistant_show_live_chain_of_thought = true
assistant_show_live_reasoning_trace = true
assistant_show_visible_plan = true
auto_condense_context = true
```

The overlays hide automatically when no assistant run is active.

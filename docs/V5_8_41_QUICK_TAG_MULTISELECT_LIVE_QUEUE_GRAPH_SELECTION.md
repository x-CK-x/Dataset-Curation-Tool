# v5.8.41 — Quick Tag Multiselect, Live Queue Status, and Graph Selection

This patch focuses on interaction reliability in the Tag Editor Quick Tag queue and the Agentic Graph Editor canvas.

## Quick Tag model menu

The multi-model Quick Tag selector now explicitly supports:

- Ctrl/Cmd-click to toggle one model.
- Shift-click to select a contiguous range.
- Ctrl/Cmd+A to select all models in the menu.
- Mouse-wheel scrolling inside the menu without propagating to the page or graph canvas.
- Preservation of selected options during live model-status refreshes.

The option rows are patched in place. A status change for one model no longer waits for the entire queue to finish before the dropdown reflects that model's new state.

## Quick Tag model queue

The Quick Tag queue panel now includes active model jobs for selected quick-tag-capable models across these lifecycle actions:

- model downloads;
- model loads;
- model unloads;
- model inference runs.

The queue panel keeps its own model filter list and also merges the live `state.quickModelSelection` and `state.quickModelQueueSelection` values during each refresh. That keeps the queue relevant even when the menu is already open and the user changes selected models without a full render.

## Live model option status

Inference job watchers now patch the selected model's inference lifecycle stage on every job poll. Download and load/unload watchers already patched their respective lifecycle stages; this release makes the inference stage behave the same way.

## Agentic Graph Editor node selection

Canvas nodes now support:

- Ctrl/Cmd-click toggle selection.
- Shift-click range selection by current node order.
- Existing Ctrl/Cmd-drag selection box.
- Existing copy/cut/paste/delete/group-drag behavior.

This is additive and does not remove the existing box-selection workflow.

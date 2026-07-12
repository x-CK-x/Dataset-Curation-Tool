# v5.8.41 — Quick Tag Multiselect, Live Queue Status, and Graph Selection

v5.8.41 improves the model-queue interaction loop in the Tag Editor and the node-selection behavior in the Agentic Graph Editor.

## Quick Tag improvements

The Quick Tag multi-model selector supports Ctrl/Cmd-click, Shift-click, and Ctrl/Cmd+A. Selected rows are preserved while the app patches model statuses in place.

The Quick Tag queue now shows active download, load, unload, and inference jobs for selected quick-tag-capable models. Each model option updates as that specific model changes state instead of waiting until the full queue is done.

## Graph Editor improvements

The graph canvas now supports Shift-click range selection and Ctrl/Cmd-click toggling on nodes, alongside box selection and grouped dragging.

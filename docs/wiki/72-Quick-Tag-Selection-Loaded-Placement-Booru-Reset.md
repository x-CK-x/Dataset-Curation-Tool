# Quick Tag Selection, Loaded Placement, and Booru Reset

v5.8.42 improves live Quick Tag queue behavior and adds tag reset from source booru metadata.

- Multi-selected Quick Tag rows are retained and used for all queue actions.
- Queue panels and model menus preserve internal scroll state while status patches live.
- A use-loaded-placement checkbox runs already-loaded models on their current CPU/CUDA/sharded residency.
- Booru reset replaces tags from fresh source metadata when the media has a usable `.download.json` sidecar.
- Missing post IDs, mismatched sources, deleted posts, and network/API failures are collected in a persisted report under `runtime/booru_tag_resets/`.

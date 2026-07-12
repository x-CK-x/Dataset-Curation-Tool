# v5.8.25 — EVA Attention-Pool Compatibility and Live Refresh Fixes

This update addresses a remaining legacy Thouph EVA/timm compatibility error and a recurring UI refresh issue where model/gallery/jobs state sometimes appeared stale until the user left and returned to a tab.

## EVA legacy tagger compatibility

The `legacy-eva02-vit-large-448-8046` model is an older pickled timm EVA classifier. Newer timm runtime code can reference optional fields that were not serialized into that older model object. The adapter already patched several missing EVA fields; v5.8.25 adds the missing pooling/head defaults surfaced by the latest error:

- `attn_pool = None`
- `head_drop = Identity`
- `pos_drop = Identity`

The retry loop remains in place so nullable/no-op EVA attributes discovered during forward execution can be patched without failing one missing attribute at a time.

## Live tab refresh

The frontend now distinguishes user-initiated refresh/action renders from passive polling renders. Explicit model/job/gallery refresh actions and completed inference jobs force a state-preserving repaint instead of being deferred by the scroll/control-interaction debounce layer.

This targets cases where:

- model load/unload/list state did not visually update until switching tabs,
- job/error details did not refresh after pressing the refresh button,
- gallery/tag-editor prediction state was stale until leaving and returning to the tab.

## Notes

The live refresh fix still preserves form and scroll state before repainting. Passive polling remains debounce-protected to avoid scrollbar jitter during normal scrolling.

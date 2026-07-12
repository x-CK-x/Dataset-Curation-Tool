# v5.8.25 — EVA Attention Pool and Live Tab Refresh Fixes

This release fixes another legacy EVA/timm compatibility gap and removes an over-broad frontend render deferral that made several tabs look stale until the user switched away and back.

## Legacy EVA fix

Older pickled EVA classifiers may not contain optional attributes read by newer `timm` forward paths. The adapter now provides neutral defaults for `attn_pool`, `head_drop`, `head_init_scale`, `pos_drop`, dropout modules with `.p`, and newer EVA attention flags such as `fused_attn`, `qkv_bias_separate`, `rotate_half`, and `gate`. It can retry additional missing optional EVA attributes during one inference attempt.

## Live tab refresh fix

The frontend previously deferred renders for several seconds after ordinary button clicks on dense tabs. That protected scrolling, but it also delayed model status changes, error-log refreshes, gallery refreshes, and prediction updates. Rendering is now deferred only while a text/select control is actively being edited or while the user is actively scrolling.


## Model-page/status performance

The hot `/api/models/status` polling path no longer scans large model folders. It uses the in-memory registry record map and overlays lifecycle/placement state, leaving expensive filesystem reconciliation to explicit model-list refreshes, rescans, downloads, and load/unload operations.

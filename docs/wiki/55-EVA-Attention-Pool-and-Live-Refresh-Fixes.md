# EVA Attention-Pool and Live Refresh Fixes

v5.8.25 fixes the remaining Thouph EVA legacy tagger error reported as:

```text
'Eva' object has no attribute 'attn_pool'
```

The legacy EVA adapter now applies additional neutral timm compatibility shims for older pickled EVA classifiers, including `attn_pool = None`, identity `head_drop`, and identity `pos_drop`.

The release also fixes UI refresh cases where model load status, job log details, gallery state, or tag/prediction results did not visually update until switching away from the current tab and returning. Explicit refresh buttons and completed model inference jobs now use a state-preserving immediate repaint path.

Passive background polling is still debounce-protected to avoid scrollbar jitter while the user is actively scrolling.

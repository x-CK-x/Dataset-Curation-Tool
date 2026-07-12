# v5.8.12 — Model Prediction Normalization, Score Hovers, and Unload UI Fixes

This release fixes model-generated tag application so every classifier/tagger output goes through the same canonical post-processing path before it is stored, scored, shown in the tag editor, or written to sidecars.

## Model prediction tag normalization

Model outputs are now normalized before application:

- active tag text mode is respected (`blue_eyes` or `blue eyes`);
- profile aliases are resolved before tags are applied;
- profile implications are expanded before tags are applied;
- implied tags inherit the originating model score;
- persisted prediction-score rows use the same tag strings as the active tool UI;
- older underscore score rows can still be found when the active tool mode is spaces.

This specifically fixes the case where Hydra/JTP/legacy e621 taggers emitted booru-style underscore labels while the tool was configured for spaces.

## Hover score behavior

Tag chips with stored model scores now show a richer hover panel:

- each model gets a stable color lane;
- each prediction row shows model name, kind, bar, and score;
- tags with more than one stored prediction row show an average score row;
- multi-model predicted tags get a distinct chip outline.

## Unload lifecycle UI

Unload actions now apply an optimistic `unloading` state immediately so the same load/unload lifecycle circle updates across the Models tab, Tag Editor, Compare, and other model-selection surfaces.

After unload completes, the load stage returns to idle/zero and inference is reset to idle for that model.

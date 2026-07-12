# Model Prediction Normalization and Unload UI Fixes

The model prediction path now applies a single canonical postprocessor before any generated tag is stored, scored, displayed, or applied to media.

## What is normalized

The postprocessor handles:

| Step | Purpose |
| --- | --- |
| Active tag text mode | Converts model-native underscores into spaces when the tool is configured for space-separated tags. |
| Alias resolution | Converts emitted aliases to the profile's canonical tag target. |
| Implication expansion | Adds implied tags before application. |
| Score preservation | Carries the originating prediction score to aliases and implied tags. |
| Score lookup compatibility | Finds older score rows whether they were stored with underscores or spaces. |

## Hover score display

Tag chips with stored prediction scores now show:

- one stable color lane per model;
- score bars per prediction row;
- an average row when multiple prediction rows exist for one tag;
- a distinct multi-model chip outline when multiple predictions are available.

## Unload lifecycle display

Unload operations now immediately set the model's load-stage circle to `unloading`, then return it to idle/zero after completion. This state is shared by the Models tab, Tag Editor, Compare, and other model-selection panels.

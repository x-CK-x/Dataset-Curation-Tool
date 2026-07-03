# v5.25 Feature Completeness and Prediction Score Analytics

This build adds the missing user-facing pieces around curation model scores,
model-family coverage, image editing/augmentation, and external licensed tool
bridges.

## Implemented in this build

- Normalized per-tag prediction score persistence in SQLite.
- Tag hovercards that show model names and confidence/probability scores.
- Prediction Analytics tab with per-tag/per-model bar graph style comparison.
- Expanded model catalog coverage for tagging, captioning, caption-to-tags,
  upscaling, segmentation, detection/cropping, quality/safety, and external
  image tools.
- More image augmentation/editing controls.
- External image tool bridge for locally installed/licensed tools such as
  Gigapixel, Photo AI, DeNoise, Sharpen, and Mask via interactive open mode or a
  user-supplied CLI template.
- Gallery shortcut into the Augment/Edit/Topaz workflow.

## Score persistence behavior

Whenever a tag/class/rating model emits predictions, rows are stored in:

- predictions: full payload history
- tag_prediction_scores: normalized latest per media/model/kind/tag scores

The tag editor, gallery, and comparer can use those scores for hovercards. The
Prediction Analytics tab can aggregate the same rows across selected media or a
whole dataset.

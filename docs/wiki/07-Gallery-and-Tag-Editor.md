# Gallery and Tag Editor

<!-- DCT_VISUAL_START -->
![Gallery and Tag Editor visual guide](assets/images/gallery_tag_editor.png)
<!-- DCT_VISUAL_END -->


The Gallery and Tag Editor are the core review/edit workflow.

## Gallery

Use **Gallery** to browse, filter, and select media.

Typical actions:

- Filter by dataset, tag, media type, duplicate status, or text query.
- Select one or more images.
- Send selection to Tag Editor, Compare, Batch Tags, annotation tabs, or external tools.
- Load page prediction scores only when you need them.

## Multi-image selection

When multiple images are selected, the app stores a selected-media cache so Tag Editor and Compare can cycle through selected images even after the visible gallery page refreshes.

Recommended workflow:

1. Select the images in Gallery.
2. Open Tag Editor.
3. Use next/previous navigation to cycle through the selected images.
4. Use Compare for side-by-side review.

## Tag Editor layout

The Tag Editor is used for:

- Manual tag edits.
- Category-aware tag sorting.
- Autocomplete.
- Caption edits.
- Model-assisted tag prediction.
- LLM/VLM/Assistant tag validation.
- Conversational chat about the current image and tags.

## Tag chips

Tag chips can show:

- Category color.
- Manual selection/highlight state.
- Predicted score/accuracy state.
- Alias/canonical status.

Manual selection controls include:

- Select All.
- Deselect All.
- Inverse All.
- Select by Category.
- Deselect by Category.

## Sorting tags

Tag sorting is intentionally user-controlled.

| Button | Behavior |
| --- | --- |
| Sort Predicted by Category | Sorts predicted/scored tags by category while leaving manual/unscored tags at the end. |
| Sort Predicted by Accuracy | Sorts predicted/scored tags by model confidence while leaving manual/unscored tags at the end. |
| Sort All by Category | Explicit override that category-sorts the full draft tag list. |

This preserves manually curated order unless you choose to sort it.

## LLM/VLM/Assistant tag selection

Use this panel when you want a model to reason over the image and the current tag list.

Common modes:

```text
look at the image and validate existing tags by selecting or highlighting the ones that match and/or are present in the image.
```

```text
select all tags that are visible in the image.
```

```text
suggest missing tags, but do not apply anything yet.
```

```text
prune tags that are not visible or not supported by the image.
```

Use preview before destructive operations such as prune, set, or keep-only.

## Chat about current target

The chat interface at the bottom of the assistant panel is for normal conversation about the current image/data.

It can use:

- Current image.
- Current tags.
- Current caption.
- Metadata.
- Model predictions.
- Conversation history.
- Condensed memory.

Useful prompts:

```text
Explain which tags are questionable and why.
```

```text
Write a short caption based on the current tags and visible content.
```

```text
Compare the current tags against the image and list missing high-confidence tags.
```

```text
Continue the previous answer without repeating anything already shown.
```

## Finish Last Output

Small local models can stop mid-sentence or mid-list. Use **Finish Last Output** when the previous response appears incomplete.

The app instructs the model to continue without repeating already displayed text.

## Completion guard for tag operations

For tag-selection/pruning tasks, the backend asks the model to end with:

```text
[TASK_COMPLETE]
```

If the marker is missing or the response appears incomplete, the app attempts continuation/verification before returning results. Non-preview destructive operations are blocked when the response still appears incomplete.

## Saving changes

Always confirm whether you are editing:

- Draft tags only.
- Applied tags for the active image.
- Batch-applied tags for selected images.
- Caption text.
- Model suggestions not yet applied.

Use preview modes when testing a new model or prompt.

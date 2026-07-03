# v5.39 model tag refresh, duplicate-load, and typing-focus fixes

This patch targets the model-to-tag workflows in Tag Editor, Compare, Batch Tags, and the Models tab.

## Fixed

- **No duplicate load job for already-loaded models.** `/api/models/load` now checks the live registry first. If the selected model is already resident in memory, it returns a completed no-op with `already_loaded: true` and does not spawn a new Jobs entry.
- **Inference no longer makes a loaded model look like it reloaded.** When an inference/chat/tag-selection path uses a model that is already loaded, the load lifecycle stage remains completed and keeps the original explicit load job id instead of being reassigned to the inference job.
- **Applied model labels update the visible tag editor.** Completed model-inference jobs that apply tags or captions now invalidate tag drafts, refresh media rows, refresh the active image, and clear prediction-score cache entries for affected media.
- **Assistant/VLM/LLM tag-selection apply refreshes immediately.** Non-preview operations now refresh affected media rows right after the API call completes, so added/removed/kept/set tags appear without reloading the whole web page.
- **Prompt textarea focus is preserved.** Automatic polling renders now snapshot focused controls, restore caret/selection/scroll where safe, and defer nonessential rerenders while the user is actively typing in text fields or textareas.

## Regression coverage

Added `tests/test_v539_model_tag_refresh_focus.py` covering:

- already-loaded `/api/models/load` calls are completed no-ops;
- inference with an already-loaded filename tagger applies tags and does not reassign the load lifecycle job id;
- frontend guardrails for active media refresh, completed model-job refresh, no-persist tag/caption controls, and typing-focus preservation are present.

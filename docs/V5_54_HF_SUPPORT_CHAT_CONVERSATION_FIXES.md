# v5.54 HF Support Files and Conversational Assistant Fixes

## Why this patch exists

Older model download allow-lists could create local Hugging Face folders that contained weights but omitted lightweight support files required by newer VLM repositories. This made the UI show a model as downloaded, but load/inference failed with errors such as missing `processing_florence2.py`, missing chat templates, or image-token count mismatches.

This patch treats model support files as first-class download/integrity assets and adds a real conversational assistant mode to the Tag Editor’s LLM/VLM card.

## Fixed: Florence-2 missing remote-code files

Florence-2 local folders are no longer considered complete unless they include:

- `processing_florence2.py`
- `configuration_florence2.py`
- `modeling_florence2.py`

If an old local folder has weights but is missing those files, loading now routes the existing folder to the Florence adapter with the original repo id preserved. The adapter then attempts a lightweight in-place repair by downloading only support files into the existing local folder.

Recommended user action for old Florence downloads:

1. Open the Models tab.
2. Find the Florence model.
3. Use Re-download / Update if it still shows incomplete support files.
4. Load again.

## Fixed: LFM/Gemma-style VLM missing chat-template support

LFM/Gemma multimodal chat rows are no longer treated as complete when the local folder lacks a chat template via either:

- `chat_template*`
- `*.jinja`
- `tokenizer_config.json` / `processor_config.json` with a `chat_template` field

The download allow-list now includes Python remote-code files and chat-template files by default.

## Improved VLM image+prompt routing

The generic Hugging Face VLM adapter now tries official and compatibility paths for image+text calls:

- image-text pipeline messages with image URLs/file URIs
- image-text pipeline messages with embedded PIL images
- LFM-style system/user extraction messages
- Gemma/Qwen-style image-token fallbacks
- manual processor/model generation when the pipeline wrapper fails but the model/processor loaded

The text prompt now includes the selected media tags, captions, metadata, model predictions, annotations, and conversation history.

## New conversational mode in Tag Editor

The existing “LLM/VLM/Assistant Tag Selection for This Image” card now has a separate conversation mode:

- **Chat About Current Target** sends the current image/media context to the selected LLM/VLM.
- Conversation mode uses `/api/models/chat`, not `/api/models/select-tags`.
- Conversation history is persisted through the existing chat conversation system.
- Optional checkboxes allow applying tags or captions parsed from the response.

This means the same model card can now be used for both:

- structured tag operations: select/add/remove/keep/set tags
- open-ended conversation: ask about the current image, tags, captions, metadata, predictions, or curation decisions

## Better tag response parsing

Tag extraction now accepts structured keys such as:

- `tags`
- `selected_tags`
- `selected_existing_tags`
- `valid_tags`
- `matching_tags`
- `present_tags`
- `visible_tags`
- `chosen_tags`
- `add_tags`
- `remove_tags`
- `keep_tags`

It also accepts line formats such as:

```text
tags: tag_one, tag_two
selected existing tags: tag_one, tag_two
present_tags: tag_one, tag_two
```

## Notes for symlink/external model layouts

Symlinked or externally rooted model folders still work. For Hugging Face VLMs, make sure the symlink target contains the whole usable local snapshot, not just weights. A complete snapshot normally includes model weights plus config/tokenizer/processor files and any required remote-code/chat-template files.

For Florence-2, the support-code files listed above are required. For LFM/Gemma multimodal chat models, chat-template files are required.

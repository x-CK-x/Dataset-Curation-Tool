# v5.53 VLM Adapter, Unload Lifecycle, and Tag Selection Fixes

This patch fixes model-load rows that were previously catalog placeholders, improves VLM prompt/image handling, and makes simple tag-selection commands deterministic.

## Concrete VLM adapters

The following catalog entries now use concrete adapters instead of unavailable placeholder adapters:

- Florence-2 Base
- Florence-2 Base Curation
- Florence-2 Large Curation
- Florence-2 Large Multitask Vision
- InstructBLIP Vicuna 7B

Florence-2 uses a promptable vision adapter that maps app prompts to Florence task tokens such as `<MORE_DETAILED_CAPTION>`, `<OCR>`, and `<OD>`. InstructBLIP uses its image+instruction processor path instead of the generic chat-template path.

## VLM image/prompt compatibility

The generic Hugging Face VLM adapter now tries additional image-token formats, including `<image>` and Qwen-style vision placeholders, before failing. This helps models whose processors report image/token count mismatches when the local folder has no usable chat template.

For LFM2.5-VL models, the downloader already includes `chat_template*` and `*.jinja`; if a model was downloaded with an older build and inference reports a missing chat template, run Re-download / Update for that model.

## Unload lifecycle UI

Unload now uses a purple `unloading` lifecycle state. After unload finishes, the load and inference circles reset to idle/0% instead of staying green/completed and implying the model is still resident in VRAM.

## Tag-selection reliability

The Tag Editor assistant now handles `select all tags` without calling a model. For VLM/LLM validation flows, JSON responses such as `{ "tags": [...] }` are parsed, and caption/prose responses are mined for existing tag names when `validate_existing_tags` is enabled.

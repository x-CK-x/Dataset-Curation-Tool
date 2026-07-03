# v5.24 model and feature coverage audit

This audit exists so the app can keep growing without losing feature families that matter for dataset curation.

## Core workflow coverage

- Dataset import, recursive media indexing, sidecar parsing, embedded generation metadata extraction, video frame extraction, audio extraction, and audio recording.
- Gallery review with refresh, tag/category recategorization, media playback for image, animation, video, and audio formats.
- Prompt-style ordered tag editor with drag/drop, category colors, custom category overrides, autocomplete, aliases, implications, and selected-image navigation.
- Batch tag editor, dual compare, assistant/model tag selection, and agentic orchestration.
- Booru/source downloading with presets, category expansion, date range, newest/oldest ordering, API/file delay controls, retries, page limits, and source validation diagnostics.
- Tag dictionaries from `tags`, `tag_aliases`, `tag_implications`, and `artists` exports using the modern SQLite search tables rather than the older trie.
- Metadata schema field picker/concatenator for JSON-like generation metadata.
- Reference Finder/source-browser workflow with Firefox/geckodriver private-mode launch, local source review, and verified-reference/query tooling.
- Annotation editor for bbox, polygon/mask, segmentation masks, 2D pose, 3D pose, animation pose, Krita mask round-trip, and Blender armature bridge.

## Model families tracked

- RedRocket JTP-3 native repo adapter for e621/furry visual tag/rating signals.
- RedRocket e6 visual ratings Hugging Face classifier adapter.
- WD / booru-style tagger contracts.
- Basic ViT/image classifiers.
- Captioners and VLMs, including BLIP, SmolVLM, Qwen/Gemma-family catalog rows, and custom local/Hugging Face model ids.
- Cloud LLM/VLM rows for assistant, tag selection, comparison, annotation context, and orchestration.
- SAM, SAM-HQ, SAM2, YOLO detection/segmentation/pose, GroundingDINO/OWLv2/Florence-style annotation contracts, and custom local checkpoint paths.
- JoyCaption-compatible captioning, model-builder classifier contracts, and clean-tags LLM pruning contracts.

## v5.24 coverage fixes

- RedRocket JTP-3 and RedRocket e6 visual ratings are first-class catalog records and are visible to model-driven curation surfaces.
- Tag/rating/classification models can be used from Models, Tag Editor, Batch Tags, Compare, Annotation context, Assistant support paths, and Orchestration.
- Booru source validation now covers configured source parser fixtures and optional live smoke checks instead of only validating one site manually.
- Firefox/geckodriver now has status, install/verify, visible private self-test, Selenium launch, direct Firefox fallback launch, and stop controls.

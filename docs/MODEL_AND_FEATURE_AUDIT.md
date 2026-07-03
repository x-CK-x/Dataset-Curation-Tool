# Model and Feature Audit

This file tracks the curation features that should remain visible as the tool grows.

## Core curation workflow

- Dataset import, sidecar import, embedded metadata extraction, and media playback.
- Gallery search/refresh/select operations.
- Ordered prompt-style tag editor with category colors, drag/drop order, and per-tag removal.
- Batch tag add/remove/set/replace/copy/prune/order operations.
- Dual image comparer with tag transfer and multi-image cycling.
- Tag dictionary profiles, custom categories, aliases, implications, artist aliases, and DB-export refresh.
- Model downloads, local inference, cloud/API inference, multi-GPU placement, and optional sharding.
- Assistant chat, assistant/model tag selection, and orchestrated multi-step jobs.
- Reference finder, annotation editor, bbox/mask/polygon/pose tools, Krita bridge, Blender bridge, and export scaffolds.
- Download presets, direct downloader jobs, source diagnostics, rate-limit pacing, and parallel download controls.

## Must-keep model families

- e621/furry taggers and rating classifiers, including RedRocket JTP-3 and RedRocket e6 Visual Ratings.
- WD/SmilingWolf taggers and other fast image taggers.
- VLM caption/chat models for user-guided tag/caption cleanup.
- Embedding/verifier models for reference-image matching, duplicate checks, and clustering.
- Detector/segmenter models: YOLO, GroundingDINO, OWLv2, SAM, SAM-HQ, SAM2, and custom local checkpoints.
- OCR/metadata models for scanned/generated media metadata extraction.
- Text LLMs and cloud models for rules, cleanup, orchestration, and user dialogue.

## Source/browser validation

The Source Browser must keep a Firefox/geckodriver path for workflows that need visible private browsing. The downloader source fixture validator should be run when adding or changing any source parser.

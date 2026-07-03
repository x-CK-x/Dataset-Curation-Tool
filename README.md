# Data Curation Tool

![Data Curation Tool Modern visual index](docs/wiki/assets/images/repo_main_visual_index.png)

Repository: https://github.com/x-CK-x/Dataset-Curation-Tool

Data Curation Tool is a local-first dataset curation, tagging, model-management, downloader, 3D generation, media metadata, and tool-orchestration application. The current documentation set is stored in `docs/wiki/` and is designed to be pushed directly into the repository or copied into the GitHub Wiki.

## [WIKI & Tutorial](https://github.com/x-CK-x/Dataset-Curation-Tool/wiki)

## Current highlights

- Modern dataset import, gallery review, tag editing, comparison, metadata extraction, and media tooling.
- Model catalog with local/cloud model settings, lifecycle progress indicators, GPU placement, loading, inference, and training status surfaces.
- 3D generation catalog covering text-to-3D, image-to-3D, multi-image-to-3D, and video-to-3D provider workflows.
- MCP tool integration surfaces for Blender, Krita, Audacity, OBS Studio, and ComfyUI.
- Downloader updates with e621/booru Boolean logic gates, presets, queues, deduplication, and tag dictionaries.
- GitHub-ready visual documentation assets under `docs/wiki/assets/images/`.

## Visual documentation map

All visuals are stored in `docs/wiki/assets/images/` and are referenced with repo-local paths so they work after the files are pushed to GitHub.

| Area | Visual | Local path |
|---|---|---|
| Repository overview | ![Repository visual index](docs/wiki/assets/images/repo_main_visual_index.png) | `docs/wiki/assets/images/repo_main_visual_index.png` |
| Main GUI face | ![Main GUI face](docs/wiki/assets/images/main_gui_face.png) | `docs/wiki/assets/images/main_gui_face.png` |
| Quick start | ![Quick start](docs/wiki/assets/images/quick_start_overview.png) | `docs/wiki/assets/images/quick_start_overview.png` |
| Windows install | ![Windows install](docs/wiki/assets/images/windows_installation.png) | `docs/wiki/assets/images/windows_installation.png` |
| First run | ![First run](docs/wiki/assets/images/first_run_configuration.png) | `docs/wiki/assets/images/first_run_configuration.png` |
| Folder layout and migration | ![Folder layout and migration](docs/wiki/assets/images/project_folder_layout_migration.png) | `docs/wiki/assets/images/project_folder_layout_migration.png` |
| Import workflow | ![Import workflow](docs/wiki/assets/images/dataset_import_workflow.png) | `docs/wiki/assets/images/dataset_import_workflow.png` |
| Gallery and tags | ![Gallery and tag editor](docs/wiki/assets/images/gallery_tag_editor.png) | `docs/wiki/assets/images/gallery_tag_editor.png` |
| Models and GPU jobs | ![Models and GPU jobs](docs/wiki/assets/images/model_lifecycle_gpu_jobs.png) | `docs/wiki/assets/images/model_lifecycle_gpu_jobs.png` |
| Assistant and orchestration | ![Assistant and orchestration](docs/wiki/assets/images/assistant_orchestrator_chat.png) | `docs/wiki/assets/images/assistant_orchestrator_chat.png` |
| Detection, pose, and 3D | ![Detection pose 3D](docs/wiki/assets/images/annotation_detection_segmentation_pose_3d.png) | `docs/wiki/assets/images/annotation_detection_segmentation_pose_3d.png` |
| Downloaders and logic gates | ![Downloaders and logic gates](docs/wiki/assets/images/downloaders_tag_dictionaries_logic.png) | `docs/wiki/assets/images/downloaders_tag_dictionaries_logic.png` |
| Metadata, media, MCP tools | ![Metadata media MCP](docs/wiki/assets/images/metadata_media_mcp_tools.png) | `docs/wiki/assets/images/metadata_media_mcp_tools.png` |
| Jobs and troubleshooting | ![Jobs and troubleshooting](docs/wiki/assets/images/jobs_queues_troubleshooting.png) | `docs/wiki/assets/images/jobs_queues_troubleshooting.png` |
| Best practices | ![Best practices](docs/wiki/assets/images/best_practices_operations_playbook.png) | `docs/wiki/assets/images/best_practices_operations_playbook.png` |
| Voice and roadmap | ![Voice roadmap](docs/wiki/assets/images/voice_roadmap_best_practices_faq_dev.png) | `docs/wiki/assets/images/voice_roadmap_best_practices_faq_dev.png` |
| Voice model catalog | ![Voice model catalog](docs/wiki/assets/images/voice_model_catalog_hf_access.png) | `docs/wiki/assets/images/voice_model_catalog_hf_access.png` |
| v5.78 3D/MCP/cloud/logic overview | ![v5.78 overview](docs/wiki/assets/images/v578_3d_cloud_mcp_logic_overview.png) | `docs/wiki/assets/images/v578_3d_cloud_mcp_logic_overview.png` |

## Historical patch notes

## v5.45 configurable Assistant / Orchestrator model

- Added Assistant-tab controls to choose which downloaded/local/API LLM or VLM acts as the app assistant.
- Added persistent `assistant_model_name` and `orchestrator_model_name` settings.
- Added `GET/PUT /api/models/assistant-config` for saving and reading Assistant/Orchestrator defaults.
- Added load/unload buttons in the Assistant tab so the selected assistant model uses the same lifecycle circles, GPU placement controls, and RAM/VRAM unload path as other models.
- Orchestration templates now use the configured orchestrator model instead of hardwiring the built-in `dataset-assistant`.
- Explicit `dataset-assistant` chat remains available as the no-model fallback; orchestrator placeholders resolve to the configured orchestrator default.

See `docs/V5_45_CONFIGURABLE_ASSISTANT_ORCHESTRATOR.md`.

## v5.44 stoppable downloads and self-activating Conda scripts

- Added `/api/jobs/cancel` plus Jobs-tab buttons to stop queued/running download jobs. Queued downloads are cancelled immediately; running downloads stop cooperatively.
- Model downloads run in a dedicated `model_download` worker lane so large downloads do not consume the whole general job pool.
- `run`, `install`, and `update` scripts now locate a user-level Conda install and activate `data-curation-tool` automatically.

See `docs/V5_44_STOPPABLE_DOWNLOADS_CONDA_SCRIPTS.md`.

## v5.43 download queue, asset rescan, and VLM defaults

- Added Hugging Face model-download progress heartbeats.
- Refreshing model status rescans local model folders and marks migrated models as downloaded/completed.
- Tag dictionary status reconciles migrated `runtime/tag_exports` files and reports cached export row counts.
- VLM/LLM Tag Editor selection defaults to validating existing image tags and can consider all categories.
- Hugging Face text/VLM load failures now surface stronger Gemma-style diagnostics.

See `docs/V5_43_DOWNLOAD_QUEUE_RESCAN_VLM_DEFAULTS.md`.

## v5.42 GPU controls, dropdown stability, and manual/VLM tag selection

This build fixes global dropdown auto-closing during polling, extends model GPU residency controls, adds manual Tag Editor highlight/deselect controls, and routes chat/VLM models such as Gemma 4 E4B IT through real image-aware tag-selection inference instead of the old heuristic-only path.

See `docs/V5_42_GPU_TAG_SELECTION_DROPDOWN_FIXES.md`.

## v5.41 GPU placement, residency, and unload controls

- Added per-model GPU placement controls so you can choose exact CUDA GPU ids before loading a model.
- Added sharding, dtype, quantization, runtime-engine, tensor-parallel, and per-GPU max-memory fields to the Models tab load panel.
- Added a GPU residency/status panel showing detected GPUs, usable VRAM, app-reserved VRAM, driver-free VRAM, loaded models, and models currently loading.
- Load requests now run a placement/VRAM plan first and block overcommit before the adapter starts allocating memory.
- Added queued unload jobs with lifecycle progress so unloading from RAM/VRAM is reflected in the same status circles.
- Existing loaded models reject incompatible placement changes until you unload and reload with the new GPU selection.

See `docs/V5_41_GPU_PLACEMENT_UNLOAD_CONTROLS.md`.

## v5.40 dropdown stability and previous-install asset migration

- Prevented automatic polling rerenders from closing model/category/profile dropdown menus while the user is trying to select an option.
- Added an **Install Migration** tab to scan one or more previous app installs and move/copy reusable assets into the current install.
- Migrates model folders, cached tag DB-export files, imported tag dictionary rows, custom tags, and optionally presets/download cache/outputs.
- Processes newest installs first, then older installs for unique assets, so the most recent setup wins while older one-off model downloads can still be recovered.
- Added startup migration settings and environment overrides so prior assets can be imported before startup tag DB sync attempts another network download.

See `docs/V5_40_DROPDOWN_MIGRATION_FIXES.md`.

## v5.39 model tag refresh, duplicate-load, and typing-focus fixes

- Prevented duplicate explicit load jobs when a model is already loaded in memory; the API now returns a completed no-op instead of queueing another load.
- Kept the load lifecycle circle tied to the original load job when inference uses an already-loaded model, so running a model no longer looks like a second reload.
- Refreshed active media rows, tag drafts, and prediction-score caches when completed model inference applies tags/captions, so Tag Editor and Compare update without a full browser reload.
- Refreshed synchronous LLM/VLM/Assistant tag-selection apply operations immediately, including the active image in Tag Editor.
- Preserved text input/textarea focus and caret position during automatic polling renders; active typing now defers nonessential rerenders instead of bumping the cursor out of the prompt field.

See `docs/V5_39_MODEL_TAG_REFRESH_FOCUS_FIXES.md`.

## v5.38 status, gallery, scroll, and downloader stability fixes

- Fixed model load/run visibility after queueing: Jobs and lifecycle circles refresh immediately without a browser reload.
- Preserved selected model dropdowns across status polling so buttons act on the model the user selected.
- Stopped Gallery model-score request recursion by caching score requests per media/tag signature.
- Preserved global and nested tab scroll positions across automatic renders.
- Hardened downloader parallel preset dedupe using source post/file identity keys, not just URL strings.
- Changed downloader defaults: Download All Posts enabled, API/page delay 7s, file delay 7s, timeout 60s, retries 3, backoff 2s.

See `docs/V5_38_STATUS_GALLERY_DOWNLOAD_FIXES.md`.

## v5.37 model lifecycle status circles

- Added a shared model lifecycle status system for four long-running phases: **download**, **load into memory**, **inference**, and **training**.
- Added circular progress indicators in the Models tab, per-model cards, quick tag/rating cards, tag-selection cards, and annotation model panels.
- Added `/api/models/status` and `/api/models/load` so model downloads, explicit memory loads, lazy loads before inference/chat/tag-selection, annotation model downloads/loads, and training scaffolds all report consistent status.
- Running inference/chat/tag selection now refuses to start while the same model is still downloading or loading, preventing use before a compatible adapter has finished initializing.
- The Jobs table remains the durable log; the new lifecycle status layer is a lightweight live UI surface and does not remove the existing download/run/unload behavior.

See `docs/V5_37_MODEL_LIFECYCLE_STATUS.md`.

## v5.31 FlexAvatar complete 3D head avatar integration

- Added a dedicated **FlexAvatar** tab for single-image, few-shot, and monocular-video complete 3D Gaussian head avatars.
- Added an isolated `dct-flexavatar` Conda runtime so the upstream Python 3.9 / CUDA 11.8 stack does not overwrite the main tool environment.
- Added official FLEX-1 checkpoint installation, pretracked example seeding, Pixel3DMM custom-input tracking, latent fitting, custom/bundled drivers, 360° rendering, avatar-code reuse, and identity interpolation.
- Added output previews, the official interactive viewer launcher, workspace asset management, and queued Jobs integration.
- Added mixed-supervision research bundles with 2D/3D bias-sink labels and paper-baseline settings, plus an honest external-trainer validation/launch path. The supplied upstream release does not contain a complete official base-model training entrypoint.
- Preserved the upstream CC BY-NC 4.0 component as a separately executed optional integration; its model checkpoint is not redistributed.

See `docs/V5_31_FLEXAVATAR_INTEGRATION.md`. Run `python scripts/verify_v531_flexavatar.py` for an offline integration check that does not require the large checkpoint or CUDA inference.

## v5.30 editable 2D/3D pose, 3D generation/rigging, Blender, and cumulative SAM prompting

- Pose bones are now visibly rendered and remain connected while joints are dragged on the image or in the interactive 3D viewer.
- Pose inference includes YOLO, MediaPipe Pose Landmarker, MMPose RTMPose/ViTPose/WholeBody/Animal, MotionBERT human 3D, InterNet hand 3D, and custom MMPose paths.
- The new **3D Studio** provides queued TripoSR, Stable Fast 3D, TRELLIS, Hunyuan3D, Meshy, generic REST, UniRig, and Blender pose-rig adapters plus a managed GLB/FBX/OBJ asset library.
- Blender bridge v0.3 exchanges pose/asset data and can queue generation or rigging from Blender.
- The cumulative SAM workflow includes one-click family setup, positive/negative point prompts, box-plus-point prompting, instance candidates, and semantic union masks.
- A top-level **Help & Workflows** tab documents SAM, pose, 3D generation, rigging, Blender, and troubleshooting.

See `docs/V5_30_POSE_3D_GENERATION_RIGGING.md` and `docs/V5_30_SAM_SETUP_POINT_PROMPTS.md`.

## v5.28 persistent spatial layers and mask compositor

Detection boxes and segmentation masks now behave as persistent, editable layer stacks. Users can select and combine any number of model-generated, manual, Krita-imported, or previously composed layers; reorder, duplicate, hide, lock, rename, recolor, edit, and delete them; and retain the layers for later model runs. Detection supports union, intersection, average, and confidence-weighted composites. Segmentation supports soft-mask-preserving union, intersection, subtract, and XOR plus threshold, feather, and grow/shrink processing. Selected unsaved model previews can be promoted automatically when they are composed with saved layers.

The mask editor now includes brush, eraser, variable size/opacity/hardness, lasso, ellipse, rectangle, magic selection, add/subtract/replace modes, overlay transparency, and undo/redo. Saved edits keep revision/provenance data, and model-only cleanup no longer removes user-edited or composite layers. See `docs/V5_28_SPATIAL_LAYER_COMPOSITOR.md`.

## v5.27 class-aware detection and segmentation

- Fixed closed-set YOLO inference so the requested class/name is resolved to a real trained class ID and passed to the model instead of merely renaming identical outputs after inference.
- Added safe custom-model class discovery from `model.names`, YAML/JSON/TXT/CSV sidecars, ONNX metadata, and safetensors metadata, with searchable class lists in Detection and Segmentation.
- Added generated-preview clear controls and separate deletion of saved model-generated boxes/masks while preserving user-drawn annotations.
- Added detector-guided semantic segmentation: a class-aware detector finds every matching instance and sends each bbox to SAM/SAM-HQ/SAM2 as an independent prompt.
- SAM-family models now explicitly reject a semantic class token without a spatial prompt or detector guide, preventing misleading identical class-labeled masks.
- Wired multiple-output controls into the actual runtimes: YOLO `max_det`, class filtering, NMS IoU, class-agnostic NMS, TTA, retina masks, and configurable SAM automatic-mask thresholds/crop settings.

See `docs/V5_27_CLASS_AWARE_SPATIAL_INFERENCE.md` for model semantics and workflow details.

## v5.26 local-app handoff and separated spatial annotation workflows

- Gallery external-app actions now launch immediately and report errors directly instead of only changing to the Augment tab or hiding failures in a background job.
- Added bounded discovery for portable/local Topaz, Krita, and ComfyUI installations under the user home directory, common Windows application folders, and project-adjacent folders.
- Interactive handoffs use timestamped safe copies and a manifest so dataset originals are not overwritten. ComfyUI handoffs copy selected images into its input directory.
- Split the former combined annotation screen into **Detection & Boxes**, **Segmentation & Masks**, and **Pose & 3D** tabs.
- Added explicit `/api/spatial/detection/*` and `/api/spatial/segmentation/*` contracts for future orchestration nodes.
- Detection rejects mask-only models. Segmentation rejects bbox-only output and previews real mask PNGs as translucent overlays.
- Manual masks now use unique filenames, preserving multiple masks on the same image instead of overwriting earlier masks.

## v5.24 model/source/geckodriver audit pass

- Added first-class RedRocket JTP-3 and RedRocket e6 Visual Ratings model rows for tag/rating workflows in Models, Tag Editor quick-run, Batch Tags, Compare, Annotation context, and orchestration. JTP-3 uses a native downloaded-repo inference path so its threshold, category exclusion, and implication options are not hidden behind a generic placeholder.
- Added offline validation for all bundled booru/generic downloader source definitions: e621, e926, Danbooru, Gelbooru, Safebooru, Rule34, Konachan, Yande.re, and Generic JSON. The Downloads API now exposes source validation for parser/page/tag/file-url configuration sanity checks.
- Improved the Firefox/geckodriver Source Browser with a private-mode smoke-test endpoint/button, stronger Firefox profile/download/log handling, fallback geckodriver asset resolution, and clearer status output.
- Added a system feature-audit endpoint to confirm critical feature groups and model/source coverage without needing to inspect code manually.

## v5.19 reference/annotation/download stability patch

- Fixed Reference Finder rendering by wiring the missing query/training dataset selectors.
- Added an Annotation Editor tab with visual bbox drawing, polygon/mask drawing, mask rasterization, annotation listing, and model/assistant proposal hooks.
- Added Krita annotation-package export and mask import endpoints, plus an updated optional Krita bridge plugin action for sending masks back to the app.
- Hardened downloader job progress so parallel downloads report one monotonic total instead of jumping backward between presets/pages.
- Added max-pages/start-page downloader controls and safer pagination/duplicate-url guards to prevent stuck download loops.


## v5.18 dependency, CUDA, tag-count, jobs, and downloader-control repair

This build hardens the large booru tag-export path and the install/update scripts.

- `pyarrow` is a required core dependency and is installed through both Conda and pip fallback paths.
- `run.bat` / `run.sh` check required dependencies and call the updater when the existing environment is missing core packages.
- `update.bat` / `update.sh` now install `requirements.txt` as well as the editable package.
- CUDA torch repair now replaces a CPU-only torch wheel with CUDA 12.8 wheels when NVIDIA GPUs are detected and `DCT_INSTALL_TORCH=auto` or `cu128`.
- e621/e926 official tag exports now require the canonical `tags.csv.gz` import to exceed one million rows, preventing partial exports such as ~119k rows from being accepted as complete.
- `scripts/verify_tag_loader_full_count.py` verifies a 1,668,155-row `tags.csv.gz` import end-to-end.
- Jobs can be cleared by checked rows, completed/failed status, or all non-running jobs.
- Downloader UI now exposes API/page delay, file delay, request timeout, retries, backoff, and parallel workers.
- Reference Finder and Orchestrate tab render errors caused by undefined frontend variables were fixed.


## v5.16 PyArrow tag DB-export loader and alias/implication support

This build focuses on the booru tag dictionary import path. Official `tags.csv.gz` files with `id,name,category,post_count` now use a PyArrow-first streaming loader and keep all valid rows, including zero-count rows, so the active dictionary/search tables can exceed 100,000 tags instead of stopping at a small partial count.

The loader also parses `tag_aliases.csv.gz` and `tag_implications.csv.gz` using `antecedent_name` and `consequent_name`, and parses `artists.csv.gz` using `name` plus braced `other_names` values such as `{alias1,alias2}`. Alias and implication terms are inserted into the searchable dictionary with `alias_target`, `alias_targets`, or `implications` metadata so the suggestion menu can show corrections and related terms while users type.

The e621/e926 numeric category mapping is explicit: `0=general`, `1=artist`, `2=rating`, `3=copyright`, `4=character`, `5=species`, `6=invalid`, `7=meta`, `8=lore`. The active dictionary, autocomplete search table, and legacy dictionary mirror are rebuilt after import so gallery/editor/comparer coloring and suggestions use the same loaded data.

## v5.15 reference-finder, annotation, training-set, and source-browser integration

- Added a **Reference Finder** workflow ported from the uploaded character-reference tool as native FastAPI/HUD features rather than Gradio tabs.
- Added reference target/concept memory, saved reference images, reference runs, candidate detections, user verification labels, and reusable verification memory in SQLite.
- Added an always-available CPU demo backend for one/few-reference search using deterministic image similarity, with optional pipeline contracts for SigLIP2, OWLv2, Grounding DINO, YOLOE, and future SAM-style segmentation adapters.
- Added BBCode/booru-style tag query parsing and evaluation against verified positives/negatives, including `[tag:name]`, quoted tags, bare tags, implicit AND, explicit AND/OR/NOT, parentheses, and wildcard tag terms.
- Added annotation helpers for bbox/polygon/mask records and YOLO/caption training-set export scaffolds so curated reference results can become training data.
- Added a **Source Browser** tool that installs/manages local geckodriver, launches Firefox in private mode by default, and exposes status/stop controls for authorized source-review workflows.
- Added model catalog rows for reference-finder detectors/verifiers and source-browser/Krita/media integration documentation while preserving the existing tag dictionary, metadata, downloader, model, orchestration, and media tooling.

## v5.15 reference search, source browser, annotations, and training-set bridge

This build integrates the reusable dataset-curation features from the reference-image finder prototype into the modern FastAPI/HUD application. It adds a **Reference Finder** tab for one/few-reference character or concept search, duplicate-aware memory, user verification feedback, BBCode/tag-query optimization, manual bbox/polygon/mask annotation helpers, training-set creation, YOLO/caption exports, and training-job script scaffolding.

It also adds a **Source Browser** tab that can verify/install a local geckodriver, launch Firefox in private mode through Selenium when optional browser dependencies are installed, and stop the controlled browser session.

The always-available backend is a deterministic CPU ColorHash sanity workflow so users can test the full reference-search/verification/query loop without model downloads. OWLv2, SigLIP2, GroundingDINO/SAM, and YOLOE-related rows are exposed as optional model-backed contracts/download targets so support can be expanded model-by-model without changing the UI or database layout.


## v5.14 original-style DB-export downloader hardening

This build fixes the observed e621 startup-sync failure where a canonical tags export around 69k rows was rejected before alias and implication exports could expand the searchable dictionary. The loader now imports canonical tags first, imports aliases and implications, expands the autocomplete/category dictionary from those relation files, and only then enforces the >100k searchable dictionary guardrail.

## v5.12 verified tag DB-export ingestion pass

- refuses to treat alias-sized/partial tag exports as complete dictionaries
- pre-counts candidate tag CSV/GZ files before replacing the active dictionary
- keeps alias and implication exports in normalized tables without inflating tag counts
- migrates legacy alias-placeholder rows out of the dictionary/search tables
- adds large synthetic import tests proving more than 100,000 tag rows are retained


## v5.10 complete tag dictionary import and metadata JSON field selection pass

- Tag dictionary import no longer discards zero-count rows from booru tag CSV exports; all valid tag names are preserved so autocomplete, category coloring, comparison, pruning, and assistant criteria can see the full dictionary.
- e621/e926 default export sync now always adds dated `tags-YYYY-MM-DD.csv.gz`, `tag_aliases-YYYY-MM-DD.csv.gz`, and `tag_implications-YYYY-MM-DD.csv.gz` candidates, even when generic fixed filenames exist.
- Startup sync now treats very small e621/e926 dictionaries as incomplete and retries the default export import instead of keeping a partial tag table.
- Metadata extraction now exposes a JSON schema/field picker for extracted image/video/LoRA metadata, including nested JSON strings. Users can select any paths, concatenate them in arbitrary order, choose input and output delimiters, and decide whether to keep or strip parentheses, curly braces, square brackets, and weight syntax.

## v5.10 tag-dictionary completeness and metadata schema composition pass

- Fixed booru tag DB-export imports so **zero-count tags are retained** instead of skipped. The previous fast importer only kept rows with `post_count > 0`, which could reduce a several-hundred-thousand-row tag CSV to a much smaller active-tag subset. Zero-count tags now remain available for category color lookup, autocomplete, implications/aliases, comparison, batch edits, and custom dataset cleanup while still sorting below high-count tags.
- Metadata extraction now exposes a full flattened JSON/schema path browser. JSON-looking strings inside PNG/WebP/video/LoRA metadata are parsed recursively and shown with selectable paths using a `::<json>` path segment.
- Added metadata field composition: users can select multiple metadata paths, choose the original delimiter, choose the final output delimiter, reorder paths manually, split to individual tags, preserve/remove parentheses/curly braces/square brackets, preserve/remove weighted prompt syntax, preview token analysis, and apply the result as tags or a caption.
- Added tests proving zero-count tags import and nested metadata JSON composition.

## v5.9 parallel downloader and multi-GPU model runtime pass

- Downloader UI now exposes category/tag expansion, date range filters, newest/oldest ordering, per-category limits, and parallel preset/file download controls.
- Job runtime supports more concurrent jobs, while downloader/model jobs expose their own safe per-job parallel worker controls.
- Model registry now includes additional current local Hugging Face LLM/VLM rows, OpenAI cloud rows, OpenRouter cloud rows, and explicit GPU placement/sharding metadata.
- Model run settings support default no-sharding one-GPU placement, optional Accelerate-style sharding across selected GPU IDs, dtype, quantization, max-memory maps, and parallel prediction workers.
- Optional heavy serving dependencies for vLLM/SGLang/bitsandbytes are listed separately in `requirements-models-serving.txt` so Conda installs stay stable by default.

A local-first dataset curation application for building, auditing, tagging, captioning, pruning, augmenting, downloading, and exporting image/video datasets. This modernization replaces the old single-file UI approach with a Conda-first FastAPI backend, a browser-based single-page HUD, a SQLite project database, background jobs, and optional model adapters for auto-tagging, captioning, VLM/ViT inference, embeddings, deduplication, segmentation-assisted workflows, and dataset chat.

## What changed

- Conda-first installation with additional pip dependencies for model ecosystems.
- Automatic CUDA PyTorch installation on NVIDIA systems when `nvidia-smi` is detected.
- No Gradio dependency.
- FastAPI backend with typed API contracts and background jobs.
- Local static single-page HUD served from the same Python app.
- SQLite database for datasets, media, tags, captions, groups, duplicates, predictions, presets, settings, download runs, and job history.
- Native folder picker endpoint for local dataset/import/output folder selection.
- Optional model layer that can launch without PyTorch, Transformers, CUDA, or model packages installed.
- Model registry supports built-in rule-based tagging plus optional Hugging Face, ViT, VLM, CLIP/DINO-style embedding, segmentation, and captioning adapters.
- Assistant tab for talking with selected dataset media through a built-in helper, a local text LLM, or a local VLM adapter.
- Gallery-first workflow with visible ordered tag strings, pointer-based drag/reorder tag chips, per-tag delete buttons, batch tag editing, category colors, side-by-side comparison, duplicate review, and export tools.
- Downloader plugins for multiple compatible booru-style JSON/DAPI sources plus a generic JSON source, gated behind user authorization confirmation.



## v5.8 fast tag/database import and fast dataset indexing pass

- Tag DB-export imports now stream `tags.csv.gz` through one long SQLite transaction, insert only canonical profile rows while parsing, and rebuild autocomplete/legacy mirrors with set-based SQL instead of per-row Python inserts.
- Tag category normalization during import is now precomputed per profile instead of querying the profile/category table for every CSV row.
- Alias and implication exports are imported into normalized `tag_aliases` and `tag_implications` tables with bulk inserts instead of repeatedly updating JSON blobs one row at a time.
- Startup tag sync job progress now reports row-count messages while importing large tag exports.
- Dataset import now commits media, tag rows, captions, and metadata in batches instead of one SQLite transaction per file or per image tag list.
- Import category lookups are batched across the whole commit batch, which removes repeated per-tag/per-image dictionary queries.
- Embedded metadata extraction is no longer enabled by default during import because it is intentionally much heavier than sidecar parsing. It remains available as an explicit checkbox and in Settings.
- Perceptual hashes and near-duplicate scanning are explicit import options. Near-duplicate scanning is disabled by default because it can be quadratic on large datasets; run it only when you need that audit step.
- Import now exposes compute SHA-256, compute perceptual hash, probe dimensions, near-duplicate scan, worker count, and SQLite commit batch size controls.


## v5.7 metadata/media/Krita/audio pass

- Added a **Media Tools** tab for generation-metadata extraction, video frame extraction, audio extraction/recording, and Krita edit packages.
- Vendored the reusable parser modules from the uploaded metadata toolkit as standalone backend integration code; no ComfyUI runtime or node registration is required.
- Image metadata extraction supports A1111-compatible PNG parameters, ComfyUI prompt/workflow metadata, NovelAI-style JSON/stealth metadata, Fooocus/Civitai/Invoke-style JSON comments, generic PNG/EXIF/WebP metadata exposed by Pillow, and LoRA references found in prompts.
- Video metadata extraction uses `ffprobe` when available and parses generation metadata stored in container/stream tags.
- LoRA metadata extraction supports safetensors headers, trigger words, training tags, base model, and architecture fields without tensor deserialization.
- Import can optionally read embedded generation metadata and use it as a fallback tag/caption source when `.txt`, `.caption`, or JSON sidecars are missing.
- Metadata extraction can preview tags/captions or apply them to selected media with the active tag profile/order strategy.
- Video tools can extract PNG frames at a chosen FPS or every-N-frames interval without adding JPEG-style recompression loss after decoding.
- Audio tools can extract audio streams from videos and save browser-recorded custom audio clips for future audio dataset workflows.
- Krita tools can create edit handoff packages with sidecars and import edited images back into the dataset while preserving tags/captions.


## v5.6 DB-export refresh, category override, selected-editor navigation, and model catalog pass

- Selected/default tag profile DB exports are now considered stale after **336 hours / 14 days** and are refreshed at startup when sync is enabled.
- e621/e926 sync prefers `/db_exports/`, keeps legacy `/db_export/` as fallback, discovers dated export links, and imports the newest successful export for **tags**, **tag aliases**, and **tag implications**.
- Tag export metadata is tracked in SQLite so the HUD can show latest import time, missing roles, stale status, and per-role import results.
- The tag CSV importer follows the original e621 export mapping: `name`, `category`, and `post_count`, while also tolerating equivalent/custom column names. Zero-count tags are skipped for autocomplete.
- TXT-only custom datasets use the active profile dictionary for tag categories, ordering, autocomplete, implication pruning, and assistant criteria when JSON sidecars are absent.
- Global custom tag/category overrides now take priority over every selected booru profile and are persisted in `runtime/custom_tags.json` plus SQLite autocomplete tables.
- Tag Dictionaries now includes a global custom category/color editor and a global tag→category override editor.
- Gallery now has **Reapply Profile/Custom Categories** to recalculate visible/selected media tag colors from custom overrides and the active profile.
- Tag Editor can cycle through multiple selected gallery images with previous/next controls and a selected-image dropdown.
- Model catalog was expanded with newer/staged Hugging Face model rows for VLMs, OCR, image classification, watermark/safety filtering, PixAI-style tagging, JoyCaption-style captioning, model-builder classifier contracts, and clean-tags/LLM pruning workflows.

## v5.5.1 DB-exports sync path fix, model downloads, and parallel import

- Startup can now auto-sync the selected/default booru tag database when the local dictionary is empty or stale.
- Supported default DB-export sync pulls compatible tag, alias, and implication exports when available, caches them under `runtime/tag_exports/`, and imports them into the local SQLite search tables.
- Custom datasets with only `.txt` tag sidecars can still use the selected booru profile for category colors, autocomplete, implication pruning, and tag ordering after dictionary sync.
- Import now parallelizes SHA-256 hashing, perceptual hashing, image-size probing, and JSON/TXT sidecar parsing across configurable CPU worker threads.
- DB writes remain serialized to protect SQLite integrity. GPU acceleration is intentionally reserved for optional post-import model inference/classification/tagging jobs.
- The Import tab exposes **Parallel import workers** and **Auto-sync selected booru tag DB if empty/stale ≥2 weeks** controls.
- Settings now include startup DB-export sync options, cache age, and default import worker count.
- The Models tab now has a scrollable model catalog with approximate model size, approximate VRAM need, precision, provider, repo id, download status, dry-run size check, download, and unload actions.
- The model registry includes runnable built-ins plus staged Hugging Face classifier/caption/LLM/VLM entries and placeholder records for larger tagger, embedding, and segmentation families that can be implemented one adapter at a time.

## v5.4 gallery refresh and JSON-sidecar category fix

This build fixes the gallery/category issues reported after v5.3:

- Gallery toolbar now has **Search / Refresh**, **Reload Page**, and **Refresh JSON/Sidecars + Reload** buttons.
- The sidecar refresh action re-reads adjacent `.txt`, `.caption`, `.json`, `image.ext.json`, and `.metadata.json` files for the selected media, or the visible page if nothing is selected.
- JSON sidecars are parsed for booru-style grouped tags such as `{"tags": {"character": [...]}}`, explicit `{"categories": {"tag": "category"}}` maps, flat tag lists, tag dictionaries, captions, descriptions, and rating fields.
- Category maps from JSON sidecars are preserved in the media tag rows instead of being overwritten by dictionary guesses.
- Numeric booru category IDs are normalized before rendering, so values like `4` render as `character`, `3` as `copyright`, and `1` as `artist`.
- Gallery thumbnails request metadata for visible tags so dictionary-backed colors can render even when sidecar category data is incomplete.


## v5.4 editor/compare assistant pass

- Added **LLM/VLM/Assistant Tag Selection** directly to the Tag Editor for the open image. Preview highlights matching chips; apply operations update only that image.
- Added **LLM/VLM/Assistant Tag Selection** directly to Compare for the current left/right pair. Preview selects matching chips on each side; apply operations update only those two displayed images.
- Multi-image comparison now defaults to the first two selected images in gallery order, with independent left/right cycling and dropdown selection so users can compare one-by-one without changing the full selection.
- Category criteria used by the assistant selector now consult saved per-image JSON-sidecar categories first, then dictionary metadata.

## v5.3 concrete tag workflow pass

This build replaces the earlier placeholder/scaffolded tag-HUD work with visible, tested controls:

- Dedicated **Tag Dictionaries** tab with profile status, import-from-file, import-from-URL, and **Load Default DB Export** actions.
- Profile-specific autocomplete dictionaries for booru/custom workflows.
- Indexed SQLite search mirror for responsive top-k suggestions while typing.
- Suggestion dropdowns show category-colored tag chips and post counts.
- Unknown tags can be remembered into the active profile and are persisted in `runtime/custom_tags.json`.
- The tag editor uses one prompt-style left-to-right strip with category colors, pointer drag/drop reordering, insertion marker, raw text sync, and per-chip `×` deletion.
- Added a dedicated **Batch Tags** tab so quick select and add/remove/set/replace/copy/prune/order operations are always visible.
- Compare view exposes selectable tag chips, add/move/copy buttons, first-two defaults for multi-selection, left/right image cycling, and assistant tag selection for the current pair.
- Profile precedence can be edited from the HUD so booru, custom dataset, and LoRA/style/character/concept orderings can be maintained by the user.

## Install

### Windows

Run from **Anaconda Prompt** or **Miniconda Prompt**:

```bat
install.bat
run.bat
```

The default installer uses this behavior:

- `DCT_INSTALL_TORCH=auto` by default.
- If `nvidia-smi` is found, CUDA 12.8 PyTorch wheels are installed.
- If no NVIDIA GPU is detected, PyTorch is skipped by default.
- Set `DCT_INSTALL_TORCH=cpu` to force CPU PyTorch.
- Set `DCT_INSTALL_TORCH=skip` to skip PyTorch.

For a CUDA reinstall inside the Conda environment:

```bat
install_torch_cuda128.bat
verify_gpu.bat
```

### Linux/macOS

```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

CUDA helper:

```bash
./install_torch_cuda128.sh
./verify_gpu.sh
```

### Manual Conda

```bash
conda env update -f environment.yml --prune
conda activate data-curation-tool
python -m pip install -e .
python run.py --host 127.0.0.1 --port 7865 --open-browser
```

Open the local URL printed in the terminal. By default, the app uses:

```text
http://127.0.0.1:7865
```

## Core feature coverage

### Dataset and media management

- Load local datasets recursively from folders.
- Use HUD buttons to select dataset folders through the native operating-system folder picker.
- Import one folder or a queue of multiple folders.
- Track image, animated image, video, and metadata sidecar files.
- Validate common image formats: JPG/JPEG, PNG, WEBP, BMP, GIF, TIFF, AVIF when Pillow supports it.
- Track video-like files for later frame/audio extraction: MP4, WEBM, MOV, MKV, AVI.
- Generate thumbnails without changing original files.
- Compute SHA-256 and perceptual average hashes.
- Skip duplicates by exact hash and flag near duplicates by Hamming distance.
- Store metadata in SQLite for fast filtering and resume-safe workflows.

### Ordered category-colored tag workflow

- Tags remain in one left-to-right prompt-style order.
- Tag category is shown with color only; categories are not forced into separate sections.
- A legend shows the category/color mapping.
- Drag tags with the mouse to reorder them.
- Click the `×` inside a tag chip to delete it.
- Save the exact ordered tag string back to the sidecar.
- Raw tag-string editing remains available for power users.
- Bulk add, remove, replace, set, copy, and prune tags.
- Tag autocomplete with trie-safe sanitization for malformed CSV rows.
- Tag implication pruning so broader tags can be removed when more specific tags exist.
- Caption splitting into valid tags, inferred tags, and filler text.
- Side-by-side image comparison with tag transfer/removal.
- Persistent image groups with save/load/delete/subtract operations.

### Model support

- Rule-based offline tagger that works immediately.
- Built-in caption splitter adapter.
- Built-in dataset assistant for tag/caption planning before a model is installed.
- Optional Hugging Face image classifier adapter.
- Optional Hugging Face image captioning adapter.
- Optional Hugging Face text LLM chat adapter using `options.model_id` or a local model path.
- Optional Hugging Face VLM image chat adapter using selected dataset images or external image paths.
- Optional ViT/embedding adapter contract for similarity, clustering, and dedupe-assisted review.
- Optional segmentation adapter contract for mask-assisted curation.
- GPU/CPU capability detection that reports NVIDIA GPUs through `nvidia-smi` even when torch is not importable yet.
- Torch CUDA readiness check through `torch.cuda.is_available()` when torch is installed.
- Multi-device scheduling hooks for CPU/GPU routing and future distributed inference.

### Assistant workflow

The Assistant tab lets the user talk to the selected dataset/media context.

Supported modes:

- Built-in no-model assistant for immediate tag/caption strategy.
- Text LLM chat through the local Hugging Face text-generation adapter.
- VLM image chat through the local Hugging Face image-text-to-text adapter.
- Optional voice input from browsers that support Web Speech Recognition.
- Optional application of suggested tags/captions to the selected media.

For model-backed chat, install torch and provide a local path or Hugging Face model id in the HUD model-id field.

### Downloading, presets, and archives

Supported source adapters:

- e621 JSON API
- e926 JSON API
- Danbooru JSON API
- Gelbooru DAPI JSON
- Safebooru DAPI JSON
- Rule34 DAPI JSON
- Konachan JSON API
- Yande.re JSON API
- Generic JSON source

Downloader behavior:

- Runs only after the user confirms they are authorized to download from the configured source.
- Saves downloaded files to a selected output folder.
- Writes tag sidecars when the source response includes tags.
- Writes `.download.json` metadata sidecars for traceability.
- Presets are stored separately from runtime settings.
- Preset import supports positive/negative sections separated by `;;;`.
- Batch preset actions include archive, remove, and delete with normalized single/multi-select behavior.

### Augmentation and post-processing

- Include augmented data with originals or generate augmented-only outputs.
- Image augmentations include horizontal flip, rotation, brightness, contrast, sharpen, denoise, crop square, and long-side resize.
- The preprocessing resize used for model inference is not saved back over the curated image unless the user explicitly exports an augmentation.
- Session output options allow generated frames or extracted artifacts to be attached to the current dataset.


### v5.7 metadata, video, audio, and Krita bridge additions

- Embedded generation metadata extraction for PNG/JPEG/WebP/video files using the standalone parser code from the media metadata toolkit.
- Supported metadata sources include Automatic1111-style `parameters`, ComfyUI prompt/workflow JSON, NovelAI-style metadata/stealth PNG payloads, Fooocus/Civitai JSON comments, video container tags exposed through ffprobe, and safetensors LoRA headers.
- Metadata extraction can preview, persist, or apply derived tag strings/captions to selected media while preserving the selected tag profile and category/color resolution.
- Video tools can decode high-quality PNG frames at a target FPS, every-N-frame interval, and optional start/end timestamps.
- Video audio extraction can save WAV/FLAC/M4A/MP3/Opus/copy outputs when ffmpeg is installed.
- Browser audio recording can save custom clips for future audio dataset workflows.
- Optional Krita bridge workflow can create editable image packages, import edited images back into a dataset, and download a minimal Krita Python plugin for sending the active document back to the local app.

### Export and interoperability

- Export tag/caption sidecars.
- Export JSONL manifests.
- Export CSV metadata.
- Export YOLO classification text files.
- Export COCO-like metadata skeleton for downstream annotation pipelines.
- SQL query console for advanced users.

## Runtime folders

```text
runtime/
  app.db
  settings.json
  thumbnails/
  presets/
  downloads/
  exports/
models/
  hf/
  local/
outputs/
```

The runtime folders are created on first launch and are ignored by git.

## Launch flags

```bash
python run.py --host 127.0.0.1 --port 7865
python run.py --runtime ./runtime --models ./models --open-browser
python run.py --reload
```

## API overview

- `GET /api/health` — health check.
- `POST /api/system/pick-folder` — open native local folder picker.
- `GET /api/system/devices` — detect CPU/GPU/torch devices.
- `POST /api/datasets/import` — import a local folder as a dataset.
- `POST /api/datasets/import-many` — import multiple local folders as one background job.
- `GET /api/datasets` — list datasets.
- `GET /api/media` — gallery/filter page.
- `GET /api/media/{id}` — media metadata.
- `GET /api/media/{id}/file` — raw media file.
- `GET /api/media/{id}/thumbnail` — thumbnail.
- `PUT /api/media/{id}/tags` — replace visible ordered tag string.
- `POST /api/tags/bulk` — bulk tag operations.
- `POST /api/tags/prune` — tag implication pruning.
- `POST /api/models/run` — run model inference as a background job.
- `POST /api/models/chat` — chat with the dataset assistant, local LLM, or local VLM.
- `GET /api/downloads/sources` — list compatible downloader adapters.
- `POST /api/downloads/run` — run direct or preset downloads.
- `GET /api/jobs` — list jobs.
- `GET /api/jobs/{id}` — inspect job status.
- `POST /api/augment/run` — run augmentation as a background job.
- `POST /api/export/run` — export dataset assets/manifests.

- `GET /api/metadata/sources` — list embedded metadata parser capabilities.
- `POST /api/metadata/extract-now` — extract/apply metadata immediately.
- `POST /api/media-tools/video/extract-frames` — queue frame extraction from selected videos.
- `POST /api/media-tools/video/extract-audio` — queue audio extraction from selected videos.
- `POST /api/media-tools/audio/recording` — save browser-recorded audio.
- `GET /api/krita/plugin` — download the optional Krita bridge plugin zip.
- `POST /api/database/query` — execute read-only SQL.

## Development

```bash
conda activate data-curation-tool
python -m pip install -e .
pytest
python -m compileall data_curation_tool
```

The frontend is plain modern browser JavaScript so it can run offline without Node, npm, or a bundler. A future Tauri/Electron shell can wrap the same backend and static HUD without changing the API.

## License

This project is licensed under the terms of the
[GNU General Public License v3.0](LICENSE).

## Usage conditions
By using this downloader, the user agrees that the author is not liable for any misuse of this downloader. This downloader is open-source and free to use.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## v5.7 media metadata, video/audio extraction, and Krita bridge pass

This pass adds a **Media Tools** workflow without turning the application into a ComfyUI node pack.  The reusable parser logic is integrated as normal backend services so datasets can be curated directly inside the local web application.

### Generation metadata extraction

The Media Tools tab can extract tags, tag strings, captions, LoRA references, and prompt/settings text from supported image/video metadata sources, including:

- Automatic1111-style PNG `parameters`
- ComfyUI prompt/workflow JSON stored in image metadata
- StableSwarm/SwarmUI-style JSON metadata
- NovelAI metadata and stealth PNG payloads where available
- Fooocus/Civitai/InvokeAI/generic JSON comment blocks
- XMP/EXIF/comment metadata exposed by Pillow
- video container tags discovered through `ffprobe`
- LoRA safetensors headers and training tag-frequency metadata through the safe metadata parser

Metadata extraction has non-destructive preview behavior by default.  When requested, extracted tags/captions can be applied to selected media while preserving the existing tag-order/category system.

### Video frame extraction

Selected videos, or external video paths, can be decoded to high-quality PNG frames at a user-selected FPS or every-N-frames interval.  PNG is the default output format to avoid adding another JPEG-style lossy encode after video decoding.  The extraction job can optionally attach generated frames back into the current dataset.

### Audio extraction and recording

Videos can have audio streams extracted to WAV/FLAC/M4A/MP3 for future audio-dataset workflows.  Browsers that support `MediaRecorder` can also record custom audio clips from the Media Tools tab and save them to the local runtime recording folder.

### Krita bridge

The Krita bridge exports selected images plus sidecars into an edit package with a manifest.  Users can open the exported image in Krita, save an edited copy, and import that edited image back into the source dataset while preserving tags and captions when requested.

## v5.15 reference finder, query optimizer, annotation, and browser pass

This pass integrates reference-image dataset curation workflows into the modern FastAPI/HUD application.

### Reference Finder

The Reference Finder tab can register a target character/object, attach one or more reference images, and scan selected media, an active dataset, or an external folder. A CPU-only ColorHash verifier is always available for smoke tests and light local matching. Optional OWLv2/SigLIP2-style detector/verifier pipelines are represented in the model catalog and service contracts so model-specific adapters can be enabled as dependencies and weights are installed.

### Verification memory and query optimization

Search results can be marked correct, incorrect, or uncertain. The app stores verification memory and can evaluate BBCode/tag-style queries such as `[tag:blue_hair] AND NOT [tag:group]` against known positives/negatives. This helps users discover better tag queries before downloading, filtering, or building a training set.

### Annotation and training exports

The tool now stores bbox, polygon, and mask-style annotation records. It can create query-derived training sets and export YOLO detection/segmentation folder structures or caption JSONL files for downstream training workflows.

### Source Browser

A local Firefox/geckodriver source browser tab was added for authorized browsing/review workflows. It can install/verify geckodriver, launch Firefox in private mode by default, and stop the local browser session from the HUD.

## v5.15 reference-finder and annotation/training additions

The current build includes a new **Reference Finder** tab for one/few-reference image search, verification feedback, BBCode-style tag-query evaluation, annotation primitives, training-set creation, YOLO export, caption JSONL export, and training script scaffolding. It also includes a **Source Browser** tab for Firefox/geckodriver status, local geckodriver installation, private-mode Firefox launching, and browser shutdown.

The built-in `demo_colorhash` reference pipeline is available immediately as a no-model sanity backend. OWLv2, SigLIP2, Florence-2, Grounding DINO, SAM2, and YOLO/YOLOE are represented in the model catalog as downloadable/staged integration points so model-specific adapters can be completed incrementally without breaking startup on machines that do not have those optional dependencies installed.

## v5.16 tag DB-export loader fix

The tag dictionary importer now uses PyArrow first for booru-style `tags.csv.gz` files with `id,name,category,post_count`, then falls back to the built-in Python CSV path for custom files. It also imports `tag_aliases.csv.gz`, `tag_implications.csv.gz`, and `artists.csv.gz` as separate export roles so tag suggestions can surface alias targets, implication targets, and artist alias corrections while the user types.

The e621/e926 numeric category mapping is now explicit:

```json
{"0":"general","1":"artist","2":"rating","3":"copyright","4":"character","5":"species","6":"invalid","7":"meta","8":"lore"}
```

The active profile dictionary, autocomplete/search table, and legacy mirror are rebuilt from the same loaded data so category coloring and suggestions stay consistent across the gallery, tag editor, comparer, batch tools, and assistant tag-selection workflows.

## Recovering from a malformed local SQLite database

If the computer/app is stopped while a very large DB-export import is running and startup reports `database disk image is malformed`, run:

Windows:

```bat
repair_database.bat
```

Linux/macOS:

```bash
./repair_database.sh
```

The repair script does not delete files permanently. It moves `runtime/app.db`, `runtime/app.db-wal`, and `runtime/app.db-shm` into `runtime/corrupt_databases/<timestamp>/` and lets the app create a clean database at next startup.

## v5.18 database safety and large tag import recovery

This build adds a startup SQLite quick-check. If `runtime/app.db` is malformed, the app automatically moves `app.db`, `app.db-wal`, and `app.db-shm` into `runtime/corrupt_databases/<timestamp>/` and creates a fresh database instead of crashing.

The tag DB-export importer now stages large tag dictionaries under a temporary source first, validates the row count, and only then atomically promotes the staged rows to the selected profile. It also removes unsafe `PRAGMA synchronous=OFF` usage from tag imports.

For an existing malformed database, use `repair_database.bat` or `./repair_database.sh` to quarantine the database files manually before startup.


## v5.20 annotation model tooling

The Annotation Editor includes first-class bbox, mask, 2D pose, 3D pose, and animation-pose dataset controls. SAM/SAM-HQ/SAM2, YOLO detection/segmentation/pose, custom local YOLO/SAM-style checkpoints, VLM/API proposal routes, and pose dataset contract rows are exposed in the model catalog. Optional heavy annotation dependencies can be installed with `install_annotation_models.bat` or `install_annotation_models.sh`.

## v5.21 annotation/model/media updates

This build improves the annotation workflow with first-class dependency installation, on-page annotation model downloads, load/validate/unload controls, additional YOLO11 detection/segmentation/pose rows, a lightweight 3D pose/bone viewer, a Blender bridge plugin, annotation deletion/loading into draft, and richer gallery playback for image, animated, video, and audio media.

For annotation model runtimes, use the Annotation Editor button **Install Annotation Dependencies** or run:

```bat
install_annotation_models.bat
```

Then use **Download Weights**, **Load / Validate**, and **Preview Proposal** or **Generate + Save** from the Annotation Editor.


## v5.22 annotation model preview/generation hardening

This build removes the no-model deterministic preview fallback from the annotation workflow.
Preview and Generate + Save now only create proposals when a selected runnable model returns
actual model output, or when the user manually draws/saves an annotation. Missing optional
dependencies, missing checkpoints, unsupported SAM2/SAM-HQ adapter rows, and zero-detection
model runs return structured errors with zero proposals instead of fake center boxes/masks.

The Annotation Editor now displays this behavior in the HUD and includes tests proving that
no-model preview/save cannot create fake annotations.


## v5.23 SAM/SAM-HQ/SAM2 annotation dispatch fix

- Restricts the Annotation Editor model dropdown to real spatial annotation models so generic assistants cannot be accidentally used as SAM checkpoints.
- Fixes checkpoint resolution so SAM/SAM-HQ/SAM2 use actual downloaded files or explicit custom local paths, not model keys such as `dataset-assistant`.
- Adds SAM-HQ runtime support through `segment-anything-hq` and exposes it in the annotation dependency installer.
- Adds a SAM2.1 image proposal adapter path for bbox-prompt and automatic masks when the optional `sam2` runtime is installed.
- Keeps no-fake-fallback behavior: failed/missing models return structured errors and do not create artificial boxes or masks.

### v5.35 Metadata, Model Runtime, and Conversation-State Update

- Added model runtime contract audit with a dedicated JTP-3 parser regression.
- Added inline metadata extraction/compose controls to Tag Editor, Compare, and Batch Tags.
- Added persistent assistant conversations with resume, archive, and fork-from-message support.
- Added metadata-aware assistant context for selected media and external paths.
- Preserved neutral metadata/ComfyUI bridge naming without legacy source-node prefixes.

See `docs/V5_35_METADATA_MODEL_CHAT_AUDIT.md`.



## v5.40 Dropdown Stability and Previous-Install Asset Migration

- Fixed polling-driven rerenders that could close open model/category/profile dropdowns before the user could choose an option. The frontend now defers automatic renders while any input, textarea, or select control is actively being used.
- Added an **Install Migration** tab for reusing assets from one or more older app installs. It scans newest installs first, then older installs for unique files.
- Migration can move or copy model folders, cached tag DB-export files, imported tag dictionary database rows, custom tags, presets, downloaded media cache, and outputs into the current install layout.
- Added startup migration settings and environment overrides so cached tag exports/model assets can be brought in before startup tag DB sync decides whether a network download is needed.
## v5.78 additions

- Expanded the 3D generation catalog and 3D Studio provider contracts for text-to-3D, image-to-3D, multi-image-to-3D, video-to-3D, ComfyUI workflow handoff, and Blender refinement overlap.
- Added MCP tool discovery/status/config endpoints and installers for Blender, Krita, Audacity, OBS Studio, and ComfyUI bridge usage.
- Added provider-level cloud model runtime defaults, including an OpenRouter DeepSeek V4 Pro template with context-shrinker metadata.
- Added booru/e621 Boolean logic gates for Downloads and Presets, with preview expansion and raw append mode.
- Updated the GitHub wiki docs under `docs/wiki/27-3D-Generation-MCP-Cloud-and-Booru-Logic.md`.


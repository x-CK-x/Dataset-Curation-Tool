# Feature Matrix

| Area | Status | Notes |
|---|---:|---|
| Conda runtime | Implemented | `environment.yml`, Conda-first install/run/update scripts, pip extras for model packages. |
| CUDA/PyTorch setup | Implemented | Auto CUDA 12.8 torch install on NVIDIA systems; CPU/skip modes available. |
| GPU detection | Implemented | Detects GPUs with `nvidia-smi` even before torch imports; torch CUDA readiness reported separately. |
| Local folder selection | Implemented | Native folder picker endpoint and HUD buttons for dataset/import/output folders. |
| Dataset import | Implemented | Single-folder and multi-folder queued imports with sidecars and duplicate skipping. |
| Gallery | Implemented | Search/filter/select/page thumbnails, Search/Refresh, Reload Page, and JSON/sidecar refresh controls. |
| Ordered tag editor | Implemented | One left-to-right ordered tag strip, category-color legend, pointer drag/reorder, insertion marker, X delete, raw string editor, and assistant tag selection for the open image. |
| Tag dictionary HUD | Implemented | Dedicated tab for status, file/URL/default export imports, custom categories, profile cloning, and precedence editing. |
| Tag categories | Implemented | Category dictionary + heuristics + category CSS classes. |
| Bulk tag editing | Implemented | Add/remove/set/copy/prune plus assistant tag selection by criteria/category. |
| Caption workflow | Implemented | Caption sidecars, caption editor, caption splitter model. |
| Compare view | Implemented | Two-image comparison, first-two default from multi-selection, independent left/right cycling, tag transfer, and assistant tag selection for the current pair. |
| Assistant chat | Implemented | Built-in assistant plus optional Hugging Face text LLM and VLM chat adapters. |
| ViT/VLM/model registry | Implemented | Built-in adapters plus optional registry contracts for ViT, VLM, embeddings, segmentation. |
| Downloader sources | Implemented | e621/e926/Danbooru/Gelbooru/Safebooru/Rule34/Konachan/Yande.re/generic JSON. |
| Download authorization gate | Implemented | User must confirm authorization before source/preset downloads run. |
| Presets | Implemented | Create/import/list/run presets. |
| Augmentation | Implemented | Basic image augmentation jobs and output selection. |
| Export | Implemented | Sidecars, JSONL, CSV, YOLO classification, COCO-like skeleton. |
| Distributed hooks | Scaffolded | Coordinator/worker schema and shard planning hooks. |
| Video processing | Scaffolded | Video media indexing and service placeholder for frame/audio workflows. |


## v5.4 gallery refresh and sidecar category rendering

- Added Gallery **Search / Refresh**, **Reload Page**, and **Refresh JSON/Sidecars + Reload** controls.
- Added `/api/media/refresh-sidecars` to re-read selected or visible-page media sidecars without fully re-importing a dataset.
- JSON sidecar parser now imports booru-style category-grouped tags, explicit tag-category maps, captions/descriptions, and rating fields.
- Tag rows preserve JSON-provided categories, including normalized numeric booru category IDs, so color-coded chips render from the categories already supplied with the images.
- Frontend category rendering normalizes aliases before CSS lookup, preventing valid categories from falling through to unstyled `cat-4`/`cat-1` style names.


## v5.4 compare/editor assistant controls

- Added the same **LLM/VLM/Assistant Tag Selection** workflow to the single-image Tag Editor and the dual-image Compare view.
- In the Tag Editor, preview mode highlights matching chips on the open image; apply operations update only that image.
- In Compare, preview mode selects matching chips on the current left/right pair; apply operations update only the displayed pair.
- Multi-image compare now defaults to the first two selected images in gallery order and exposes independent left/right cycle/dropdown controls.
- Assistant tag selection now respects stored JSON-sidecar categories for category criteria, instead of relying only on dictionary metadata.

## v5.3 concrete tag, settings, and orchestration upgrades

- Profile-specific booru/custom tag dictionaries with indexed SQLite search mirror for responsive top-k autocomplete while typing.
- Tag dictionary profiles for e621/e926, Danbooru, Gelbooru, Safebooru, Rule34, Konachan, Yande.re, LoRA/model-purpose organization, and custom datasets.
- CSV/TSV/gzip/db-export import route for tag dictionaries per active profile, plus direct URL import for compatible tag exports.
- Unknown/custom tag persistence to `runtime/custom_tags.json` and SQLite so user-defined art styles, character names, and local categories are retained.
- One-line prompt-style tag strip that preserves tag order while category-coloring each chip.
- Drag/drop insertion marker and per-chip remove button.
- Ordering strategies: retain current/custom order, selected booru/profile precedence, custom profile precedence, and LoRA/model-purpose precedence.
- Side-by-side compare with individual tag selection, add/move selected tags between images, select-all, select-missing-on-other, and copy-all controls.
- Batch add/remove/set/replace/copy/prune/order controls for selected media.
- Assistant/model tag selection endpoint for selecting tags by criteria/category and optionally applying add/remove/set/keep-only operations.
- Agentic orchestration service and HUD tab for queued multi-step curation runs across classifiers/taggers, tag-selection criteria, LLM review, and VLM-style review adapters.
- Settings controls for preferred devices, multi-GPU device lists, model cache path, HF/OpenRouter/OpenAI/Anthropic tokens, tag suggestion count, temperature, max tokens, thresholds, workers, and default tag ordering/profile behavior.

## v5.15 Reference Finder / Annotation / Training Integration

This build ports reusable capabilities from the standalone reference-finder prototype into the modern FastAPI/SQLite HUD without reintroducing Gradio.

| Area | Status | Notes |
|---|---:|---|
| Reference-image target records | Implemented | Targets and saved reference image paths are stored in SQLite. |
| Reference search runs | Implemented | `demo_colorhash` works without model downloads; OWLv2/SigLIP2 pipelines are represented as staged optional model-backed rows. |
| Duplicate/memory reuse | Implemented | Results are cached per media, target, pipeline, and reference fingerprint. |
| User verification feedback | Implemented | Correct/incorrect/uncertain labels update reference memory. |
| BBCode/tag-query optimizer | Implemented | Supports `[tag:name]`, quoted tags, AND/OR/NOT, parentheses, baseline comparison, and known positive/negative metrics. |
| Annotation primitives | Implemented | BBox, polygon, bbox mask, and mask records are stored in SQLite; bbox/polygon masks can be rasterized to PNG. |
| Training set creation | Implemented | Build train/val working sets from tag queries. |
| YOLO export | Implemented | Detection and segmentation label export from annotations. |
| Caption JSONL export | Implemented | Exports caption datasets from training sets. |
| Training job script scaffold | Implemented | Creates editable local training command scripts for YOLO-style tasks and future trainer integrations. |
| Firefox/geckodriver source browser | Implemented | Status, install, launch, and stop endpoints with private-mode Firefox defaults. |
| HUD integration | Implemented | Added Reference Finder and Source Browser tabs. |

Heavy model-specific adapters remain staged where they require specialized processors/checkpoints, but the catalog/download/runtime plumbing is in place for adding them one-by-one.

## v5.16 PyArrow tag DB-export loader hardening

| Area | Status | Notes |
|---|---:|---|
| PyArrow tag CSV import | Implemented | `tags.csv.gz` is loaded through PyArrow first when it exposes `id,name,category,post_count`; Python CSV remains as fallback for custom/headerless files. |
| Correct e621/e926 category mapping | Implemented | Numeric categories now map `0=general`, `1=artist`, `2=rating`, `3=copyright`, `4=character`, `5=species`, `6=invalid`, `7=meta`, `8=lore`. |
| Profile tag order | Implemented | e621/e926 default order is aligned with character/species/invalid/artist/general/meta/rating while preserving copyright/lore support for colors. |
| Alias import | Implemented | `tag_aliases.csv(.gz)` columns `antecedent_name` and `consequent_name` load into `tag_aliases`. |
| Implication import | Implemented | `tag_implications.csv(.gz)` columns `antecedent_name` and `consequent_name` load into `tag_implications`. |
| Artist alias import | Implemented | `artists.csv(.gz)` imports canonical artist names as artist-category tags and parses `{alias1,alias2}` from `other_names` into alias tables. |
| Startup/download role support | Implemented | `/db_exports/` discovery now recognizes `tags`, `tag_aliases`, `tag_implications`, and `artists` export roles. |
| Large mirror duplication removed | Implemented | The loader no longer duplicates every profile tag row into the legacy mirror during import; autocomplete queries the profile dictionary directly. |

## v5.24 model/source/browser audit

| Area | Status | Notes |
|---|---:|---|
| RedRocket JTP-3 | Implemented | Added as a first-class downloadable/run-capable image tagger row for quick tag proposals, batch tagging, compare QA, annotation support, assistant/tool use, and orchestration. |
| RedRocket e6 Visual Ratings | Implemented | Added as a first-class downloadable/run-capable rating/classification row for quick visual rating passes and curation workflows. |
| HF image tagger runtime | Implemented | Added a more robust image tagger adapter that prefers downloaded local model paths, supports Transformers image-classification, and includes a timm fallback for timm-style HF repos. |
| Cross-tab tag/rating model access | Implemented | Quick tag/rating model cards are available from Tag Editor, Batch Tags, Compare, and Annotation-adjacent workflows; model tag selection can now route real tagger/rating predictions. |
| Booru source validation | Implemented | Source validation covers e621, e926, Danbooru, Gelbooru, Safebooru, Rule34, Konachan, Yande.re, and generic JSON parser fixtures instead of only one source. |
| Firefox/geckodriver startup | Hardened | run scripts default to Firefox/geckodriver private mode, with system browser fallback if launch fails. Source Browser includes install, status, visible self-test, direct Firefox fallback, and log-tail diagnostics. |
| Existing reference/annotation work | Preserved | Reference Finder, annotation editor, SAM/SAM-HQ/SAM2/YOLO catalog rows, Blender/Krita bridges, metadata extraction, media tools, tag dictionary work, and database recovery remain in place. |

Open model-adapter follow-ups remain for highly specialized architectures that need custom processors/output parsing, but the rows, downloader paths, and generic runtime hooks are now present where they can be safely exposed.

## v5.28 persistent spatial-layer workflow

| Area | Status | Notes |
|---|---:|---|
| Detection layer stack | Implemented | Model, user, composite, and imported boxes remain as independently editable/reorderable layers with visibility, locks, color, opacity, provenance, and revisions. |
| Box composition | Implemented | Combine any selected boxes using union, intersection, coordinate average, or confidence-weighted average while retaining sources by default. |
| Segmentation layer stack | Implemented | Multiple model, user, Krita, and composite masks remain available across later model runs and can be loaded back into the editor. |
| Mask composition | Implemented | Union, intersection, subtract, and XOR with selectable base layer, threshold, feather, and grow/shrink controls. |
| Pixel mask editor | Implemented | Brush, eraser, variable size/opacity/hardness, lasso, ellipse, rectangle, magic selection, add/subtract/replace modes, overlay transparency, and local undo/redo. |
| Layer revisions/provenance | Implemented | Saved geometry/pixel edits create revisions; manual refinement of a model layer preserves its originating model metadata and is not removed by raw-model cleanup. |
| Preview persistence | Implemented | Selected unsaved model preview boxes/masks can be promoted to persistent layers; preview cleanup preserves referenced files. |
| Future orchestration contracts | Implemented | Distinct detection and segmentation layer APIs expose merge, update, duplicate, reorder, revision, preview-persist, and delete operations for future agent nodes. |

## v5.30 editable pose and 3D production workflow

| Area | Status | Notes |
|---|---:|---|
| Visible pose skeleton edges | Implemented | Bones render beneath joints and update continuously while joints are dragged. |
| Editable 2D pose overlay | Implemented | Move, add, rename, connect, delete joints/bones, apply templates, and save persistent pose layers. |
| Editable 3D pose | Implemented | Image-projected editing plus orbitable 3D skeleton viewer, depth slider, and live topology redraw. |
| Pose model breadth | Implemented | YOLO, MediaPipe, RTMPose, ViTPose, WholeBody, animal pose, MotionBERT human 3D, InterNet hand 3D, and custom MMPose. |
| Pose runtime setup | Implemented | Selected-family and all-family installers for Ultralytics, MediaPipe, and MMPose/OpenMIM. |
| 3D generation studio | Implemented | TripoSR, Stable Fast 3D, TRELLIS image/text, Hunyuan3D local API, Meshy API, and generic REST adapters. |
| Managed 3D asset library | Implemented | Generated, rigged, and imported assets have metadata sidecars, download endpoints, and Blender launch actions. |
| Automatic learned rigging | Implemented | UniRig skeleton, skinning, and merge sequence, including Windows-to-WSL path translation. |
| Pose-driven Blender rigging | Implemented | Armature generation from editable DCT pose edges, automatic weights, and GLB/FBX export. |
| Blender bridge v0.3 | Implemented | Pose exchange, asset import, generation queue, and rigging queue actions. |
| 3D local API | Implemented | Provider catalog, generate, rig, asset import/list/download, and Blender-open endpoints use existing queued jobs. |
| SAM family setup | Implemented | Selected SAM/SAM-HQ/SAM2 runtime, checkpoint download, validation, and load are one queued setup operation. |
| SAM positive/negative points | Implemented | Native labels 1/0 reach SAM, SAM-HQ, and SAM2 predictors and can be combined with bbox prompts. |
| SAM semantic union | Implemented | Best valid candidate per prompt is unioned into one class layer; empty masks and synthetic fallbacks are rejected. |
| Help & workflows | Implemented | In-app SAM, pose, 3D generation, rigging, Blender, and troubleshooting documentation. |

## v5.31 FlexAvatar complete 3D head avatar workflow

| Area | Status | Notes |
|---|---:|---|
| Dedicated FlexAvatar tab | Implemented | Setup, checkpoint, source/driver staging, tracking, fitting, animation, rendering, interpolation, outputs, and training research tools. |
| Runtime isolation | Implemented | Separate `dct-flexavatar` Conda environment prevents Python/CUDA/PyTorch conflicts with the main application. |
| Single-image avatar | Implemented | Stage/track one portrait and create a complete animatable 3D Gaussian head avatar. |
| Few-shot fitting | Implemented | Fit one latent avatar code to several tracked observations. |
| Monocular-video fitting | Implemented | Sample tracked video observations and fit one avatar code. |
| Expression drivers | Implemented | Bundled NeRSemble driver, custom tracked video, source expression sequence, and neutral driver. |
| Novel-view rendering | Implemented | Frontal orbit and 360-degree render paths with configurable resolution/FPS/frame limit. |
| Avatar-code persistence | Implemented | Save/reload codes and interpolate between two identities. |
| Official viewer | Implemented | Detached launch of the upstream DearPyGui viewer. |
| Mixed-supervision bundle | Implemented | JSONL manifest with 2D/3D source type and bias-sink identifiers plus the paper baseline. |
| Full base-model trainer | External integration | The supplied official release has no complete training entrypoint; the HUD validates and launches a user-supplied compatible trainer without misrepresenting fitting as training. |
| License separation | Implemented | Bundled optional upstream source remains under CC BY-NC 4.0; checkpoint is downloaded separately. |

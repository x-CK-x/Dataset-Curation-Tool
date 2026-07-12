## v5.8.48 Global Assistant Action and Reasoning Overlays

- Live action notes and a separate live chain-of-thought/reasoning overlay are now visible from any tab while assistant runs are active.
- The reasoning overlay is enabled by default and is persisted through Settings.
- Completed responses store visible reasoning trace metadata next to visible plans/action notes.


- [v5.8.46 Multi-Unload and Live Token Context](76-Multi-Unload-Live-Token-Context.md)
- [v5.8.45 Attention Heatmap Dropdown Queue Refresh](75-Attention-Heatmap-Dropdown-Queue-Refresh.md)
# Data Curation Tool Modern Wiki
- v5.8.44: Quick Tag queue rows stay visible/live for all selected models, hover prediction bars are restored, and Nightshade/Glaze integrity classifiers can sample videos.

- v5.8.43: Non-blocking/GPU-assisted thumbnails, Quick Tag deselection, job-backed booru reset, and Nightshade/Glaze integrity classifier registration.

- v5.8.42: Quick Tag multi-select queue reliability, use-loaded placement mode, booru tag reset reports, and faster thumbnail prewarming.


## v5.8.41 Quick Tag Multiselect, Live Queue Status, and Graph Selection

Adds Ctrl/Cmd-click and Shift-click multiselect for Quick Tag model queues and graph nodes, and patches Quick Tag model menu statuses live as each download/load/unload/inference job changes state.

<!-- DCT_VISUAL_START -->
![Data Curation Tool Modern visual documentation index](assets/images/repo_main_visual_index.png)
<!-- DCT_VISUAL_END -->


Data Curation Tool Modern is a local-first dataset curation application for organizing media, editing tags and captions, running local or cloud AI models, managing model downloads, using VLM/LLM assistants, building annotations, extracting metadata, and preparing datasets for later training or review.

This wiki is designed for three audiences:

- **End users** who want to install the tool and curate image/video/audio datasets.
- **Power users** who want model management, GPU placement, migration, symlinks, assistant/orchestrator workflows, and custom pipelines.
- **Contributors** who want to understand the project layout and add features safely.


<!-- DCT_VISUAL_GALLERY_START -->

## Visual gallery

| Topic | Visual |
|---|---|
| Main repo overview | ![Repo visual index](assets/images/repo_main_visual_index.png) |
| Main GUI face | ![Main GUI face](assets/images/main_gui_face.png) |
| Model lifecycle and jobs | ![Model lifecycle and jobs](assets/images/model_lifecycle_gpu_jobs.png) |
| Downloaders and logic gates | ![Downloaders and logic gates](assets/images/downloaders_tag_dictionaries_logic.png) |
| MCP and external creative tools | ![MCP tools](assets/images/metadata_media_mcp_tools.png) |
| 3D/MCP/cloud/logic overview | ![v5.78 overview](assets/images/v578_3d_cloud_mcp_logic_overview.png) |

<!-- DCT_VISUAL_GALLERY_END -->

## Start here

1. [Quick Start](01-Quick-Start.md) gives the shortest path from download to first dataset import.
2. [Windows Installation](02-Installation-Windows.md) and [Linux Installation](03-Installation-Linux.md) describe setup scripts, Conda activation, CUDA checks, and repair scripts.
3. [First Run Configuration](04-First-Run-Configuration.md) covers settings, tokens, tag dictionaries, models, migrations, and device detection.
4. [Gallery and Tag Editor](07-Gallery-and-Tag-Editor.md) explains the main curation loop.
5. [Models, Downloads, and GPU Placement](08-Models-Downloads-and-GPU-Placement.md) explains local models, cloud/API models, model queues, progress circles, loading, unloading, VRAM planning, and multi-GPU selection.
6. [Assistant, Orchestrator, and Chat](09-Assistant-Orchestrator-and-Chat.md) explains the conversational data assistant, memory, continuation, tag selection, pruning, captioning, and orchestrated model runs.
7. [Jobs, Queues, and Troubleshooting](15-Jobs-Queues-and-Troubleshooting.md) covers logs, failed jobs, retry, cancel, pause/resume, and common errors.
8. [v5.8.33 Download Progress and Guaranteed Agentic Graphs](63-Download-Progress-and-Guaranteed-Agentic-Graphs.md) explains download lifecycle fixes and the new known-good Agentic Workflow README tab.
9. [v5.8.34 Graph Edges, Model Lifecycle, ONNX, and Workflow Certification](64-Graph-Edges-Model-Lifecycle-ONNX-Workflow-Certification.md) explains the graph-edge coordinate repair, immediate model lifecycle jobs, strict GPU placement, ONNX Runtime repair, and certified workflow self-tests.
10. [v5.8.36 Import/Gallery Responsiveness and PixAI NCHW Fix](66-Import-Gallery-Responsiveness-PixAI-NCHW.md) explains the Import picker responsiveness repair, Gallery duplicate suppression, batched Gallery rendering, quick-model availability cues, and PixAI ONNX input-layout fix.

## New in v5.8.39

- [Live Model Card, VRAM, and Gallery Resilience Fix](69-Live-Model-Card-VRAM-Gallery-Resilience.md)

## New in v5.8.36

- [Import/Gallery Responsiveness and PixAI NCHW Fix](66-Import-Gallery-Responsiveness-PixAI-NCHW.md)

## New in v5.8.34

- [Graph Edges, Immediate Model Lifecycle, ONNX Runtime Repair, and Workflow Certification](64-Graph-Edges-Model-Lifecycle-ONNX-Workflow-Certification.md)

## New in v5.8.32

- [Migrated Model Detection and No-Redownload Load Fix](62-Migrated-Model-Detection-No-Redownload.md)

## New in v5.8.31

- [Graph Selection, Node Menu, WD/PixAI Loader Fixes](61-Graph-Selection-Menu-WD-PixAI-Fixes.md)

## New in v5.8.30

- [Graph Immediate Interaction and Chat Fix](60-Graph-Immediate-Interaction-and-Chat-Fix.md)

## New in v5.8.27

- [Multimodal Dataset Builder, LTX/Wan Exports, Training MCPs, and Model-Score Highlighting](57-Multimodal-Dataset-Builder-LTX-Wan-MCP.md)

## Feature map

| Area | Main docs |
| --- | --- |
| Installation and launch | [Quick Start](01-Quick-Start.md), [Windows](02-Installation-Windows.md), [Linux](03-Installation-Linux.md) |
| Dataset import and review | [Importing Datasets](06-Importing-Datasets.md), [Gallery and Tag Editor](07-Gallery-and-Tag-Editor.md) |
| Models and GPUs | [Models, Downloads, and GPU Placement](08-Models-Downloads-and-GPU-Placement.md), [Hydra Runtime Dependency Fix](35-Hydra-Runtime-Dependency-Fix.md) |
| Assistant/orchestrator | [Assistant, Orchestrator, and Chat](09-Assistant-Orchestrator-and-Chat.md), [Automation Workflows](33-Automation-Workflows-and-Cooperative-Curation.md), [Agentic Graph Editor](34-Agentic-Graph-Editor.md) |
| Annotation and spatial labels | [Detection, Segmentation, Pose, and 3D](10-Annotation-Detection-Segmentation-Pose.md) |
| Booru/download/tag DB workflows | [Downloaders and Tag Dictionaries](11-Downloaders-and-Tag-Dictionaries.md) |
| Metadata and media processing | [Metadata, Media Tools, and External Apps](12-Metadata-Media-Tools-and-External-Apps.md) |
| Moving between versions | [Install Migration and Symlinks](13-Install-Migration-and-Symlinks.md) |
| Coding with the app | [Code Assistant](14-Code-Assistant.md) |
| Future audio/video/voice/3D roadmap | [Future Multimodal Voice and Training Roadmap](24-Future-Multimodal-Voice-and-Training-Roadmap.md) |
| Troubleshooting | [Jobs, Queues, and Troubleshooting](15-Jobs-Queues-and-Troubleshooting.md), [FAQ](18-FAQ.md) |

## Main application tabs

The application currently includes these primary tabs:

- Dashboard
- Import
- Gallery
- Tag Editor
- Detection & Boxes
- Segmentation & Masks
- Pose & 3D
- 3D Studio
- 3D Viewport
- ComfyUI Bridge
- FlexAvatar
- Compare
- Batch Tags
- Prediction Analytics
- Media Tools
- Reference Finder
- Source Browser
- Assistant
- Orchestrate
- Models
- Augment
- Downloads
- Presets
- Tag Dictionaries
- Database
- Install Migration
- Code Assistant
- Settings
- Help & Workflows
- Jobs
- Automation Workflows

Each tab is summarized in [Best Practices and Workflows](16-Best-Practices-and-Workflows.md), with deeper pages for the most important workflows.

## Current documentation status

This wiki is a living guide. It is intentionally broader than a small README and should be updated whenever a feature changes, especially around model adapters, downloader defaults, GPU placement behavior, migration rules, assistant/orchestrator features, and troubleshooting steps.

- [Agent Tools](19-Agent-Tools.md) — human-approved function-calling runtime for assistant/orchestrator models.

## New in v5.8.9

- Fixes the startup initialization crash in the Dashboard startup-progress job caused by a missing `time` import.

## New in v5.8.8

- [Hydra UTF-8, Startup Progress, and Gallery Fixes](39-Hydra-UTF8-Startup-Progress-and-Gallery-Fixes.md) documents the RedRocket Hydra 3.5 UTF-8 CSV fix, Dashboard startup-maintenance progress ring, and retained Gallery/page-limit refresh fixes.

## New in v5.8.7

- [Hydra Loader, Workflow, and Gallery Fixes](38-Hydra-Loader-Workflow-and-Gallery-Fixes.md) documents the RedRocket Hydra 3.5 loader compatibility patch, expanded automation presets, scroll preservation, and Gallery page clamping.

## New in v5.8.6

- [Hydra Python Queue Patch and Z3D Removal](37-Hydra-Python-Queue-Patch-and-Z3D-Removal.md) documents the RedRocket Hydra 3.5 `MpQueue[str]`/`Queue[str]` source patch and removal of the unavailable Z3D/Zack3D legacy tagger row.

## New in v5.8.5

- [Hydra Windows libvips DLL Loader Fix](36-Hydra-Windows-libvips-DLL-Loader-Fix.md) documents the Windows DLL search-path, handle-retention, and `pyvips[binary]` fallback fix for local RedRocket Hydra 3.5 loading.

## New in v5.8.4

- [Hydra Runtime Dependency Fix](35-Hydra-Runtime-Dependency-Fix.md) documents the `pyvips`/`libvips` repair path for local RedRocket Hydra 3.5 inference.

## Newer Advanced Pages

- [Assistant Visible Planning](20-Assistant-Visible-Planning)

## New in v5.64

- [Approved COA Execution](21-Approved-COA-Execution.md) explains how assistant-generated plans become user-approved local terminal/Python/file/browser actions.

- [Voice Input and Speech Output](23-Voice-Input-and-Speech-Output.md)


## New in v5.73

- [Future Multimodal Voice and Training Roadmap](24-Future-Multimodal-Voice-and-Training-Roadmap.md) captures the long-term direction for audio, video-with-audio, ethical voice cloning, voice conversion, 3D, and training workflows.
- [Model-Decided Tool Use](25-Model-Decided-Tool-Use)



## New in v5.74

- [Model-Decided Tool Use](25-Model-Decided-Tool-Use.md) explains direct-answer vs in-app GUI action vs local tool COA decisions.



## New in v5.76

- Fixes Text-to-Speech settings/test behavior so enabling/loading TTS is not confused with STT.
- Hardens Hugging Face/Bark-style TTS output handling for NumPy arrays, tuples, tensors, and common waveform keys.
- Adds clearer TTS runtime/debug behavior for assistant Speak/Test TTS workflows.

## New in v5.75

- Expanded the STT/TTS catalog with additional Hugging Face voice models.
- Added visible Hugging Face token / gated / terms-required indicators in Models and voice selectors.
- Added audio diarization rows for pyannote-style audio/video-with-audio curation workflows.

See [Voice Model Catalog and HF Access](26-Voice-Model-Catalog-and-HF-Access).
## New in v5.78

- [3D Generation, MCP Tools, Cloud Runtime Defaults, and Booru Logic Gates](27-3D-Generation-MCP-Cloud-and-Booru-Logic.md) explains the expanded text/image/multi-image/video 3D provider catalog, external creative-app MCP tool bridge, OpenRouter/cloud defaults, and advanced downloader Boolean logic.

- [Global Dataset, Branches, and Variants](28-Global-Dataset-Branches-and-Variants.md)

## New in v5.78.13

- [Dataset Pipeline, Training Prep, and 3D-Print Handoff](29-Dataset-Pipeline-Training-Prep-and-3D-Print-Handoff.md) explains the rule-driven pre-training pipeline, branch readiness reports, external trainer manifests, and 3D-print slicer handoff packages.
- [Hydra 3.5, FLUX/Chroma, and Remote Tagger Offload](30-Hydra-3-5-FLUX-Chroma-and-Remote-Tagger-Offload.md) explains the Hydra tagger integration, remote service/offload path, MCP bridge, and added FLUX/Chroma dataset-prep targets.

## New in v5.8.0

- [Legacy Taggers and Tag/Caption Translation](31-Legacy-Taggers-and-Tag-Caption-Translation.md) explains the original local tagger config integration, profile-aware alias/implication cleanup, and cross-booru/caption translation workflow.

## New in v5.8.1

- [Character Reference and LoRA Augmentation](32-Character-Reference-and-LoRA-Augmentation.md) explains no-new-training character pruning, active reference memory, branch pruning, augmentation presets, and regularization guidance for LoRA/IC-LoRA/ControlNet/embedding dataset prep.



## New in v5.8.3

- [Agentic Graph Editor](34-Agentic-Graph-Editor.md) adds visual node/edge workflow authoring, model-generated graph planning, cooperative graph refinement, workflow conversion, dry-run, queued execution, and graph run manifests.

## New in v5.8.2

- [Automation Workflows and Cooperative Curation](33-Automation-Workflows-and-Cooperative-Curation.md) adds editable user/model/cooperative workflow JSON, templates, dry-runs, approval gates, queued workflow jobs, and run manifests for end-to-end dataset curation automation.

- [Hydra UTF-8, Startup Progress, and Gallery Fixes](39-Hydra-UTF8-Startup-Progress-and-Gallery-Fixes.md)

## New in v5.8.10

- [Agentic Graph Editor Standalone Port and Browser MCPs](40-Agentic-Graph-Editor-Standalone-Port-and-Browser-MCPs.md) documents the expanded graph canvas, standalone-style node families, graph event console, bundle/model/supervisor/tool/browser nodes, and local browser MCP handoff entries.

- **v5.8.11**: fixes tab scroll preservation and makes migration jobs resume the Dashboard startup-maintenance progress indicator after a cancelled first-run tag sync.

## New in v5.8.11

- Agentic Graph Editor now carries over the standalone graph-editor node concepts while keeping the current visual theme.
- Browser MCP entries cover default browser, Edge, Chrome, Firefox, Chromium, and Tor Browser for approval-gated visible lookup/navigation.
- Tab switching preserves scroll position across large views.
- Install Migration resumes Dashboard startup-maintenance progress and post-migration cache reconciliation.



## v5.8.12

Model prediction tags are normalized through the active tag text mode before they are applied. Alias/implication postprocessing now preserves scores, hover cards show per-model scores plus multi-model averages, and model unload lifecycle circles update immediately across tabs.


## New in v5.8.14
- [Legacy Tagger Inference and Scroll Stability Fixes](44-Legacy-Tagger-Inference-and-Scroll-Stability-Fixes.md)
- Fixes legacy EfficientNetV2-M static input shape handling, legacy EVA/timm pickle compatibility, and active-scroll UI jitter.


## New in v5.8.15

- Dashboard refresh controls for startup/migration maintenance state.
- Live migration progress during scanning, file copy/move, migrated tag database imports, and post-migration reconciliation.
- No-cache startup status polling for migration-triggered initialization.


## New in v5.8.16

- [Graph Palette, Prediction Refresh, and EVA Fixes](46-Graph-Palette-Prediction-Refresh-and-EVA-Fixes.md) documents palette-driven node customization, faster model prediction-score refresh, unique per-model hover colors, and expanded legacy EVA compatibility.

- [Graph Canvas Interaction and Migration Finalization](47-Graph-Canvas-Interaction-and-Migration-Finalization.md)


## v5.8.17

- Graph canvas panning, cursor-centered wheel zoom, right-click node palette creation, node context menus, and port-based node connections are now functional.
- Migration finalization no longer reports 100% until reconciliation, compact result writing, and active-profile tag/model checks are complete.
- Dashboard startup maintenance can show a frontend hydration phase while optional UI catalogs continue loading after backend startup reaches 100%.


## v5.8.18

- Legacy EVA/timm inference now patches `norm_pre` and related optional fields with neutral identity/default values.
- Agentic Graph Editor canvas actions now have the missing node update/change handlers and immediate graph-specific render path for right-click palettes, pan/zoom, node movement, and port connections.

See [EVA Norm-Pre and Graph Editor Event Handler Fixes](48-EVA-Norm-Pre-and-Graph-Editor-Event-Handler-Fixes.md).


## v5.8.19

- [Migration Local Cache Reuse and Weekly Startup Sync](49-Migration-Local-Cache-Reuse-and-Weekly-Startup-Sync.md)


## v5.8.20

- [Parallel Migration and First-Run Tag Sync](50-Parallel-Migration-and-First-Run-Tag-Sync.md)
- Install Migration can now copy/move files with parallel workers, enabled by default with 4 workers for SSD-oriented migrations.
- Empty first-run installs now bootstrap the active/default tag dictionary immediately instead of being blocked by stale recent-check markers.
- Tag DB startup sync is still gated to weekly checks by default and can be disabled or forced manually.

## v5.8.21

- [Fast Same-Drive Model Migration](51-Fast-Same-Drive-Model-Migration.md) avoids rewriting hundreds of GiB when moving model folders between installs on the same SSD/drive.



## v5.8.22

- [Migration Fast Model Groups and Progress Fix](52-Migration-Fast-Model-Groups-and-Progress-Fix.md) documents same-drive model-group directory moves, duplicate-group short-circuiting, runtime duplicate checks, and the corrected migration progress mapping.

## New in v5.8.23

- [v5.8.23 Migration Tag Database Stall Fix](53-Migration-Tag-Database-Stall-Fix.md) explains the fix for migrations that appeared stuck while importing `tag_export_files`.
## New in v5.8.24

- [GPU, Hydra, EVA, and Gallery Refresh Fixes](54-GPU-Hydra-EVA-and-Gallery-Refresh-Fixes.md) fixes strict GPU placement, Hydra local-tagger catalog placement, legacy EVA compatibility, model-page responsiveness, and stale gallery/tag refresh behavior.
## New in v5.8.25

- [v5.8.25 EVA Attention Pool and Live Tab Refresh Fixes](55-EVA-Attention-Pool-and-Live-Tab-Refresh-Fixes.md) fixes the latest legacy EVA optional attribute issue and restores immediate tab-local updates after refresh/model actions.


## New in v5.8.26

- [Scroll Stability and Legacy ONNX/GPU Fixes](56-Scroll-Stability-and-Legacy-ONNX-GPU-Fixes.md) fixes automatic-refresh scroll jumps and restores legacy tagger load behavior for ONNX/PyTorch rows.

- [58 — Preprocessing, Scroll Stability, Graph Editor, and LingBot World Models](58-Preprocessing-Scroll-Graph-LingBot-World-Models.md)

## v5.8.29

- [Attention Overlay, Graph Chat, and Threshold Update](59-Attention-Overlay-Graph-Chat-Threshold.md) adds inline heatmap overlays to Tag Editor/Compare, sets tagger thresholds to 0.70, fixes Graph Editor canvas/menu/inspector interactions, and adds graph-linked chat.

## v5.8.30

- [Graph Immediate Interaction and Chat Fix](60-Graph-Immediate-Interaction-and-Chat-Fix.md) restores immediate Agentic Graph Editor canvas/node/menu responses while preserving tab scroll position, and fixes Agentic Graph Chat rendering.



## v5.8.31

- [Graph Selection, Node Menu, WD/PixAI Loader Fixes](61-Graph-Selection-Menu-WD-PixAI-Fixes.md)


## v5.8.32

- [Migrated Model Detection and No-Redownload Load Fix](62-Migrated-Model-Detection-No-Redownload.md)

## v5.8.35

- [Download Finalize, CUDA-12 ONNX, and Refresh Fix](65-Download-Finalize-CUDA12-ONNX-Refresh.md) fixes stale post-download model badges, adds single-model reconcile after completed downloads, pins the CUDA-12 ONNX Runtime GPU stack, preloads CUDA/cuDNN DLLs before WD/PixAI ONNX sessions, and improves stalled-download messages.

## v5.8.37 Quick Tag Refresh and Alias/Score Sync

- [Quick Tag Refresh and Alias/Score Sync](67-Quick-Tag-Refresh-and-Alias-Score-Sync.md)

## v5.8.38 Live Model Runtime Queues

- [Live Model Runtime Queues](68-Live-Model-Runtime-Queues.md) adds live VRAM/system-RAM status patching, Tag Editor quick-tag multi-model queueing, per-job/global queue progress, and an Agent Tools global model-job queue.

## v5.8.40 Gallery, Prediction Scores, Quick Tag, and Workflows

- [Gallery Thumbnails, Prediction Scores, Quick Tag, and Workflows](70-Gallery-Thumbnails-Prediction-Scores-Quick-Tag-Workflows.md) improves Gallery thumbnail prewarming, surfaces persisted per-media/model prediction scores, fixes Quick Tag threshold and queue device controls, and adds categorized advanced dry-run workflows.


- **v5.8.42** — Quick Tag multi-select queue reliability, use-loaded placement mode, booru tag reset reports, and faster thumbnail prewarming.

- [Thumbnails, Multiselect, Booru Reset, Integrity Classifiers](73-Thumbnails-Multiselect-Booru-Reset-Integrity.md)

## v5.8.47 Memory Guard and Assistant Model Tools

The Tag Editor assistant now receives active LoRA/dataset-rule context, can apply JSON tag-pruning directives to the actual media tag list, and can propose approved model load/inference/unload queue operations. Long-running chat sessions now compact stored context payloads and avoid automatic CPU offload under system-RAM pressure.

- [v5.8.48 Global Assistant Action and Reasoning Overlays](78-Global-Assistant-Action-and-Reasoning-Overlays.md)
- [v5.8.46 Multi-Unload and Live Token Context](76-Multi-Unload-Live-Token-Context.md)
- [v5.8.45 Attention Heatmap Dropdown Queue Refresh](75-Attention-Heatmap-Dropdown-Queue-Refresh.md)
# GitHub Wiki Source Folder


## v5.8.41 Quick Tag Multiselect, Live Queue Status, and Graph Selection

Adds Ctrl/Cmd-click and Shift-click multiselect for Quick Tag model queues and graph nodes, and patches Quick Tag model menu statuses live as each download/load/unload/inference job changes state.

This folder contains the GitHub-wiki-ready documentation set for **Data Curation Tool Modern**.

Use it in either of these ways:

1. Keep it in the project as normal developer documentation under `docs/wiki/`.
2. Copy the Markdown files and the `assets/` folder into the GitHub repository wiki after creating the wiki once in the browser.

Repository: https://github.com/x-CK-x/Dataset-Curation-Tool

Recommended GitHub wiki import process:

```bash
# In a separate folder, clone the GitHub wiki repo after creating the wiki once in the browser.
git clone https://github.com/x-CK-x/Dataset-Curation-Tool.wiki.git
cd Dataset-Curation-Tool.wiki

# Copy every file from DataCurationToolModern/docs/wiki/ into this wiki repo, including assets/.
git add .
git commit -m "Add Data Curation Tool Modern wiki"
git push
```


## Latest reliability note

- [v5.8.39 Live Model Card, VRAM, and Gallery Resilience](69-Live-Model-Card-VRAM-Gallery-Resilience.md) documents the immediate loaded-model highlighting/reordering fix, actual VRAM visibility, Gallery failure isolation, and the runtime planning context endpoint.
- [v5.8.36 Import/Gallery Responsiveness and PixAI NCHW Fix](66-Import-Gallery-Responsiveness-PixAI-NCHW.md) documents the child-process folder picker, reduced passive media-tab polling, Gallery duplicate suppression, batched media-page tag/caption lookup, quick model availability cues, and PixAI ONNX NCHW preprocessing fix.
- [v5.8.34 Graph Edges, Model Lifecycle, ONNX, and Workflow Certification](64-Graph-Edges-Model-Lifecycle-ONNX-Workflow-Certification.md) documents the graph-edge coordinate repair, immediate load/unload job tracking, strict GPU placement validation, ONNX Runtime repair path, and the certified workflow self-test suite.
- [v5.8.33 Download Progress and Guaranteed Agentic Graphs](63-Download-Progress-and-Guaranteed-Agentic-Graphs.md) documents the download progress-circle fix and the known-good graph templates rendered in the Agentic Workflow READMEs tab.

## Visual documentation map

All visuals are stored in `assets/images/` and are referenced with repo-local paths so they work after the files are pushed to GitHub.

| Area | Visual | Local path |
|---|---|---|
| Repository overview | ![Repository visual index](assets/images/repo_main_visual_index.png) | `assets/images/repo_main_visual_index.png` |
| Main GUI face | ![Main GUI face](assets/images/main_gui_face.png) | `assets/images/main_gui_face.png` |
| Quick start | ![Quick start](assets/images/quick_start_overview.png) | `assets/images/quick_start_overview.png` |
| Windows install | ![Windows install](assets/images/windows_installation.png) | `assets/images/windows_installation.png` |
| First run | ![First run](assets/images/first_run_configuration.png) | `assets/images/first_run_configuration.png` |
| Folder layout and migration | ![Folder layout and migration](assets/images/project_folder_layout_migration.png) | `assets/images/project_folder_layout_migration.png` |
| Import workflow | ![Import workflow](assets/images/dataset_import_workflow.png) | `assets/images/dataset_import_workflow.png` |
| Gallery and tags | ![Gallery and tag editor](assets/images/gallery_tag_editor.png) | `assets/images/gallery_tag_editor.png` |
| Models and GPU jobs | ![Models and GPU jobs](assets/images/model_lifecycle_gpu_jobs.png) | `assets/images/model_lifecycle_gpu_jobs.png` |
| Assistant and orchestration | ![Assistant and orchestration](assets/images/assistant_orchestrator_chat.png) | `assets/images/assistant_orchestrator_chat.png` |
| Detection, pose, and 3D | ![Detection pose 3D](assets/images/annotation_detection_segmentation_pose_3d.png) | `assets/images/annotation_detection_segmentation_pose_3d.png` |
| Downloaders and logic gates | ![Downloaders and logic gates](assets/images/downloaders_tag_dictionaries_logic.png) | `assets/images/downloaders_tag_dictionaries_logic.png` |
| Metadata, media, MCP tools | ![Metadata media MCP](assets/images/metadata_media_mcp_tools.png) | `assets/images/metadata_media_mcp_tools.png` |
| Jobs and troubleshooting | ![Jobs and troubleshooting](assets/images/jobs_queues_troubleshooting.png) | `assets/images/jobs_queues_troubleshooting.png` |
| Best practices | ![Best practices](assets/images/best_practices_operations_playbook.png) | `assets/images/best_practices_operations_playbook.png` |
| Voice and roadmap | ![Voice roadmap](assets/images/voice_roadmap_best_practices_faq_dev.png) | `assets/images/voice_roadmap_best_practices_faq_dev.png` |
| Voice model catalog | ![Voice model catalog](assets/images/voice_model_catalog_hf_access.png) | `assets/images/voice_model_catalog_hf_access.png` |
| v5.78 3D/MCP/cloud/logic overview | ![v5.78 overview](assets/images/v578_3d_cloud_mcp_logic_overview.png) | `assets/images/v578_3d_cloud_mcp_logic_overview.png` |

## Notes

- Image links are local relative paths.
- There are no references to a project website, hosted docs site, Discord, community site, or status page.
- The only public project URL used here is the GitHub repository URL above.


## v5.8.0

- [Legacy Taggers and Tag/Caption Translation](31-Legacy-Taggers-and-Tag-Caption-Translation.md)

## v5.78.14

- [Hydra 3.5, FLUX/Chroma, and Remote Tagger Offload](30-Hydra-3-5-FLUX-Chroma-and-Remote-Tagger-Offload.md)
- [Character Reference and LoRA Augmentation](32-Character-Reference-and-LoRA-Augmentation.md) — no-new-training character pruning, active memory, branch pruning, and LoRA augmentation/regularization presets.



## Agentic Graph Editor

- [Agentic Graph Editor](34-Agentic-Graph-Editor.md) documents the visual graph editor, user/model/cooperative graph authoring, model-drafted graph plans, node palette, validation, workflow conversion, dry-runs, and queued graph execution.

## Automation Workflows

- [Automation Workflows and Cooperative Curation](33-Automation-Workflows-and-Cooperative-Curation.md) documents template workflows, assistant/model generated workflow JSON, dry-run, approval gates, and queued curation automation.



## v5.8.9

- Startup progress job crash fix for the missing `time` import.

## v5.8.8

- [Hydra UTF-8, Startup Progress, and Gallery Fixes](39-Hydra-UTF8-Startup-Progress-and-Gallery-Fixes.md) covers the Windows Unicode stdout failure fix, UTF-8 temp CSV handoff, startup progress status endpoint, and Dashboard progress ring.

## v5.8.7

- [Hydra Loader, Workflow, and Gallery Fixes](38-Hydra-Loader-Workflow-and-Gallery-Fixes.md) covers the Hydra `heuristic_max_workers` / `max_workers` local-source patch, automation preset expansion, and Gallery refresh/page-limit fixes.

## v5.8.6

- [Hydra Python Queue Patch and Z3D Removal](37-Hydra-Python-Queue-Patch-and-Z3D-Removal.md) covers the local Hydra 3.5 `MpQueue[str]` / `Queue[str]` compatibility patch and the removal of the unavailable Z3D/Zack3D legacy tagger entry.

## v5.8.5

- [Hydra Windows libvips DLL Loader Fix](36-Hydra-Windows-libvips-DLL-Loader-Fix.md) covers the second-stage Hydra Windows load fix, persistent DLL-directory handles, broader libvips discovery, and `pyvips[binary]` fallback.

## v5.8.4

- [Hydra Runtime Dependency Fix](35-Hydra-Runtime-Dependency-Fix.md) covers the local Hydra 3.5 `pyvips`/`libvips` dependency repair scripts and dependency checker.

- [Hydra UTF-8, Startup Progress, and Gallery Fixes](39-Hydra-UTF8-Startup-Progress-and-Gallery-Fixes.md)

## v5.8.10

- [Agentic Graph Editor Standalone Port and Browser MCPs](40-Agentic-Graph-Editor-Standalone-Port-and-Browser-MCPs.md) covers the standalone graph-editor feature port, expanded graph node palette, canvas pan/zoom/ports/edge deletion, event console, and browser MCP entries.

- **v5.8.11**: fixes tab scroll preservation and makes migration jobs resume the Dashboard startup-maintenance progress indicator after a cancelled first-run tag sync.

## v5.8.11

See [Graph Editor, Browser MCPs, Scroll Persistence, and Startup Resume](41-Graph-Editor-Browser-MCP-Scroll-and-Startup-Resume.md).




## v5.8.14

- Legacy EfficientNetV2-M now uses fixed 448x448 preprocessing before ONNX/PyTorch inference.
- Legacy EVA/timm pickle models now receive nullable compatibility attributes before forward passes.
- Scrollbar restoration is short-lived and polling renders are deferred while the user is actively scrolling.

## v5.8.13

- Startup Maintenance progress now mirrors manual migration and post-migration reconciliation live on the Dashboard.
- Attention Visualizer can create local Grad-CAM/CAM, Hydra CAM/PCA, U-Net cross-attention, and t-SNE/embedding review artifacts.
- Agentic Graph Editor adds local presets, edge metadata, graph-runtime sessions, selected-node runs, runtime inspection, and approval-gated browser/MCP/tool previews.

## v5.8.12

Model prediction tags are normalized through the active tag text mode before they are applied. Alias/implication postprocessing now preserves scores, hover cards show per-model scores plus multi-model averages, and model unload lifecycle circles update immediately across tabs.
- [Legacy Tagger Inference and Scroll Stability Fixes](44-Legacy-Tagger-Inference-and-Scroll-Stability-Fixes.md)


## v5.8.15

- [Dashboard Migration Progress Refresh](45-Dashboard-Migration-Progress-Refresh.md) documents manual Dashboard refresh and live migration-startup progress.

- [v5.8.16 Graph Palette, Prediction Refresh, and EVA Fixes](46-Graph-Palette-Prediction-Refresh-and-EVA-Fixes.md)

- [47 - Graph Canvas Interaction and Migration Finalization](47-Graph-Canvas-Interaction-and-Migration-Finalization.md)


## v5.8.17

- Repaired Agentic Graph Editor panning, zoom, right-click node palette, node context menu, and node-port connection behavior.
- Reduced post-100% startup/migration stalls by capping migration job detail payloads, using lightweight `/api/jobs` list polling, and keeping Dashboard progress visible while optional frontend catalogs hydrate.


## v5.8.18

- [EVA Norm-Pre and Graph Editor Event Handler Fixes](48-EVA-Norm-Pre-and-Graph-Editor-Event-Handler-Fixes.md)


## v5.8.19

- [Migration Local Cache Reuse and Weekly Startup Sync](49-Migration-Local-Cache-Reuse-and-Weekly-Startup-Sync.md)


## v5.8.20

- [Parallel Migration and First-Run Tag Sync](50-Parallel-Migration-and-First-Run-Tag-Sync.md) documents SSD-oriented parallel file transfers during migration, empty-install first-run dictionary bootstrap, weekly startup sync controls, and manual force-update buttons.

## v5.8.21

- [Fast Same-Drive Model Migration](51-Fast-Same-Drive-Model-Migration.md) documents the fast rename path for same-volume model migrations.



## v5.8.22

- [Migration Fast Model Groups and Progress Fix](52-Migration-Fast-Model-Groups-and-Progress-Fix.md)

## v5.8.23 Migration Fix

- [Migration Tag Database Stall Fix](53-Migration-Tag-Database-Stall-Fix.md)
## v5.8.24 Runtime and UI Fixes

- [GPU, Hydra, EVA, and Gallery Refresh Fixes](54-GPU-Hydra-EVA-and-Gallery-Refresh-Fixes.md)
## v5.8.25 Runtime and UI Refresh Fixes

- [EVA Attention Pool and Live Tab Refresh Fixes](55-EVA-Attention-Pool-and-Live-Tab-Refresh-Fixes.md) documents the legacy EVA and frontend repaint fixes.


## v5.8.25 EVA / Live Refresh Fixes

- [EVA Attention-Pool and Live Refresh Fixes](55-EVA-Attention-Pool-and-Live-Refresh-Fixes.md) documents the remaining legacy EVA compatibility shim and current-tab refresh behavior.

## v5.8.26 Scroll and Legacy ONNX/GPU Fixes

- [Scroll Stability and Legacy ONNX/GPU Fixes](56-Scroll-Stability-and-Legacy-ONNX-GPU-Fixes.md)


## New in v5.8.27

- [Multimodal Dataset Builder, LTX/Wan Exports, Training MCPs, and Model-Score Highlighting](57-Multimodal-Dataset-Builder-LTX-Wan-MCP.md)

- [58 — Preprocessing, Scroll Stability, Graph Editor, and LingBot World Models](58-Preprocessing-Scroll-Graph-LingBot-World-Models.md)

- [v5.8.29 Attention Overlay, Graph Chat, and Threshold Update](59-Attention-Overlay-Graph-Chat-Threshold.md)

- [v5.8.30 Graph Immediate Interaction and Chat Fix](60-Graph-Immediate-Interaction-and-Chat-Fix.md)
- [v5.8.32 Migrated Model Detection and No-Redownload Load Fix](62-Migrated-Model-Detection-No-Redownload.md)
- [v5.8.31 Graph Selection, Node Menu, WD/PixAI Loader Fixes](61-Graph-Selection-Menu-WD-PixAI-Fixes.md)


## v5.8.30

- [Graph Immediate Interaction and Chat Fix](60-Graph-Immediate-Interaction-and-Chat-Fix.md)


## v5.8.32

- [v5.8.32 Migrated Model Detection and No-Redownload Load Fix](62-Migrated-Model-Detection-No-Redownload.md)

## v5.8.31

- [Graph Selection, Node Menu, WD/PixAI Loader Fixes](61-Graph-Selection-Menu-WD-PixAI-Fixes.md)
- [v5.8.35 Download Finalize, CUDA-12 ONNX, and Refresh Fix](65-Download-Finalize-CUDA12-ONNX-Refresh.md)

## v5.8.37 Quick Tag Refresh and Alias/Score Sync

- [Quick Tag Refresh and Alias/Score Sync](67-Quick-Tag-Refresh-and-Alias-Score-Sync.md)

## v5.8.38 Live Model Runtime Queues

- [Live Model Runtime Queues](68-Live-Model-Runtime-Queues.md)

## v5.8.40 Gallery, Prediction Scores, Quick Tag, and Workflows

- [Gallery Thumbnails, Prediction Scores, Quick Tag, and Workflows](70-Gallery-Thumbnails-Prediction-Scores-Quick-Tag-Workflows.md)


- **v5.8.42** — Quick Tag multi-select queue reliability, use-loaded placement mode, booru tag reset reports, and faster thumbnail prewarming.

- [Thumbnails, Multiselect, Booru Reset, Integrity Classifiers](73-Thumbnails-Multiselect-Booru-Reset-Integrity.md)

- v5.8.43: Thumbnails, multiselect, booru reset, integrity classifiers
## v5.8.44 Quick Queue Live Rows and Video Integrity Sampling

- [Quick Queue Live Rows, Video Integrity Sampling, and Prediction Scores](74-Quick-Queue-Live-Rows-Video-Integrity-Scores.md)

- [v5.8.47 Memory Guard, Assistant Model Tools, and Tag Pruning](77-Memory-Guard-Assistant-Model-Tools-Tag-Pruning.md)

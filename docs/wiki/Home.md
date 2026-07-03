# Data Curation Tool Modern Wiki

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

## Feature map

| Area | Main docs |
| --- | --- |
| Installation and launch | [Quick Start](01-Quick-Start.md), [Windows](02-Installation-Windows.md), [Linux](03-Installation-Linux.md) |
| Dataset import and review | [Importing Datasets](06-Importing-Datasets.md), [Gallery and Tag Editor](07-Gallery-and-Tag-Editor.md) |
| Models and GPUs | [Models, Downloads, and GPU Placement](08-Models-Downloads-and-GPU-Placement.md) |
| Assistant/orchestrator | [Assistant, Orchestrator, and Chat](09-Assistant-Orchestrator-and-Chat.md) |
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

Each tab is summarized in [Best Practices and Workflows](16-Best-Practices-and-Workflows.md), with deeper pages for the most important workflows.

## Current documentation status

This wiki is a living guide. It is intentionally broader than a small README and should be updated whenever a feature changes, especially around model adapters, downloader defaults, GPU placement behavior, migration rules, assistant/orchestrator features, and troubleshooting steps.

- [Agent Tools](19-Agent-Tools.md) — human-approved function-calling runtime for assistant/orchestrator models.

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

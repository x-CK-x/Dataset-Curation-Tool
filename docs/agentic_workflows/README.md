# Known-Good Agentic Workflow Templates

These workflows are intentionally conservative graph-runtime baselines. Their first objective is reliability, not feature breadth.

The templates are designed to run locally in graph runtime dry-run mode without model downloads, live model calls, shell commands, browser calls, MCP servers, trainer installs, source downloads, ffmpeg, or media files. They are the safe starting point for testing the Agentic Graph Editor before expanding into real dataset automation.

## Templates

1. `guaranteed_graph_runtime_smoke_test`
2. `guaranteed_empty_branch_readiness_workflow`
3. `guaranteed_multimodal_manifest_preview`

The GUI renders these instructions in the **Agentic Workflow READMEs** tab and provides buttons to create each graph and run a runtime smoke test.

## v5.8.34 certified local dry-run templates

The catalog now includes six templates that can be verified through **Agentic Workflow READMEs → Self-Test All Certified Workflows**:

- `guaranteed_graph_runtime_smoke_test`
- `guaranteed_empty_branch_readiness_workflow`
- `guaranteed_multimodal_manifest_preview`
- `certified_tag_normalization_preview`
- `certified_dataset_qa_export_plan`
- `certified_closed_loop_training_improvement_preview`

The self-test uses the same template builder and graph runtime used by the canvas. It executes with live model calls, network access, browser/shell/MCP tools, media mutation, and trainer launch disabled. These templates are certified for that local dry-run contract; integrations added later must be validated separately.

## v5.8.40 advanced certified dry-run templates

- **Advanced tags: multi-model score review** — tagger/classifier score review, threshold policy, alias/implication normalization, and human approval before writes.
- **Advanced captions: image caption-only dataset prep** — caption-first image dataset planning where tags are not applied.
- **Advanced multimodal: LTX/Wan caption/export planning** — video/audio/image structured-caption and export-readiness planning for LTX/Wan-style datasets.
- **Advanced multimodal: audio-video sync caption review** — transcript/sound-event/visual-action sync and caption-QA planning.

Each v5.8.40 template is intended to complete in local dry-run mode before real models, media tools, MCPs, shell commands, or trainer handoffs are connected.

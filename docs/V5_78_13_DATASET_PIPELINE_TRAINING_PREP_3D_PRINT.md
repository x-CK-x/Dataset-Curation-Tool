# v5.78.13 Dataset Pipeline, Training-Prep Interfaces, and 3D-Print Handoff

This release expands the data-curation layer into a repeatable pre-training pipeline. It still does **not** train models directly. Instead, it prepares rule packets, model/VLM prompt packets, branch readiness reports, branch-sidecar rule-application previews, external-trainer manifests, and 3D-print handoff packages that can be reviewed and passed to dedicated tools.

## Dataset Pipeline tab

The new Dataset Pipeline tab is built on the Global Dataset layer:

1. original downloads/imports stay immutable in the global dataset,
2. branch/model datasets keep editable tag/caption sidecars and config manifests,
3. augmentation/upscale outputs are tracked as branch variants,
4. exports produce deterministic handoff manifests for external trainers.

Pipeline stages:

| Stage | Purpose |
| --- | --- |
| Download / source sync | Acquire source-authorized media and register it into the global original layer without duplicates. |
| Initial labeling | Use source tags, metadata, taggers, VLMs, and rule packets to create first-pass labels. |
| Quality filtering | Cull duplicates, low-signal examples, wrong subjects, off-goal items, and bad sidecars. |
| Augment + upscale | Create branch-layer variants only; global originals remain untouched. |
| Additional labeling | Re-label augmented/derived variants and preserve transform lineage. |
| Branch rule application | Dry-run or apply deterministic label cleanup to editable branch sidecars; global originals are not mutated. |
| Final training selection | Freeze branch choices and export a manifest for external trainers. |

## Diffusion target presets

The catalog now includes dataset-prep targets for:

- SeaArt-style service targets
- SDXL
- Illustrious
- NoobAI
- Anima/anime diffusion derivatives
- Krea 2 / K2
- Ideogram 4
- Wan 2.2
- LTX 2.3

These entries are **dataset-prep targets**, not a claim that every base model has an integrated trainer inside this app.

## Adapter and artifact rules

Rule packets can be generated for:

| Goal | Intended use |
| --- | --- |
| Style | Learn medium, palette, lighting, linework, rendering, texture, and composition without binding the style to one subject. |
| Character | Learn identity, body structure, recurring outfit/markings, proportions, and signature details while keeping scenes flexible. |
| Character + style | Preserve both identity and style using separate anchors where appropriate. |
| Concept | Learn objects, actions, effects, materials, poses, relationships, or scene ideas while isolating them from incidental style/identity noise. |

Supported artifact families:

- LoRA
- IC-LoRA
- ControlNet
- Embedding / textual inversion

The rule packet is intended for a local/cloud LLM, VLM, VLLM, or GLM to apply uniformly to branch sidecars.

## Readiness metrics

Branch evaluation checks:

- trigger-token coverage,
- missing captions/tags,
- tag count and caption token count,
- identity/style/concept descriptor coverage,
- video caption metadata for Wan/LTX targets,
- IC-LoRA condition/target relationship notes,
- ControlNet conditioning-map notes,
- items requiring manual review.

## External trainer handoff

The app now creates manifests/config stubs for external tools including:

- Kohya SS / sd-scripts,
- OneTrainer,
- Hugging Face Diffusers training scripts,
- LTX Trainer,
- ComfyUI training/preprocessing nodes,
- generic cloud/API training providers,
- future external webscraper/source-manifest bridges for approved source handoff into Global Dataset ingest.

Training remains external and user-approved.

## 3D-print handoff

A 3D-print package can be generated from a managed or user-selected 3D asset. The package includes:

- source asset copy,
- target-format plan for STL/3MF/OBJ/G-code-oriented workflows,
- repair policy,
- slicer/tool selection,
- MCP/handoff instructions.

Supported slicer/mesh-tool interfaces:

- Blender conversion/repair,
- ZBrush refinement handoff,
- MeshLab repair/conversion,
- PrusaSlicer,
- OrcaSlicer,
- Cura/CuraEngine,
- Bambu Studio,
- Slic3r.

The package does not blindly generate printer-specific G-code. Slicer profile, printer, filament, safety, and support settings must be reviewed by the user.


## Rule application workflow

The Dataset Pipeline tab now exposes a stricter workflow:

1. Build the rule packet for the target model, adapter family, and dataset goal.
2. Evaluate branch readiness and inspect missing-label/manual-review warnings.
3. Build a model/VLM prompt packet when a local or cloud model should propose edits.
4. Run a dry-run label cleanup to preview deterministic sidecar changes.
5. Apply rule cleanup only to branch-local tag/caption files after review.

This workflow is intentionally branch-scoped. Global originals and their original source metadata remain unchanged.

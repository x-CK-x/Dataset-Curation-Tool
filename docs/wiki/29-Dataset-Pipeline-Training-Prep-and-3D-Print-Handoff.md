# Dataset Pipeline, Training Prep, and 3D-Print Handoff

![Operations playbook](assets/images/data_curation_operations_playbook_design.png)

The Dataset Pipeline tab turns the tool into a repeatable pre-training preparation system. It does not run training itself. It prepares the data, rules, model/VLM prompt packets, branch-sidecar cleanup previews, manifests, and external-tool handoff files needed for training tools or cloud services.

## Core idea

The pipeline assumes the Global Dataset layer is active:

| Layer | What it stores | Mutation policy |
| --- | --- | --- |
| Global originals | Unique source media, SHA-256 dedupe, source/post mappings | Do not edit directly |
| Branch datasets | Model-specific config, editable tag/caption copies, include/exclude choices | Safe to edit |
| Variants | Augmented/upscaled/derived media linked to an original and branch | Safe to edit as derived data |
| Exports | Frozen trainer manifests, copied/link sidecars, optional copied media | Reproducible handoff layer |

## Pipeline stages

| Stage | Purpose |
| --- | --- |
| Download / source sync | Download or ingest media once and register it into the global original layer. |
| Initial labeling | Use source tags, metadata, local/cloud models, and rules to create first-pass labels. |
| Quality filtering | Detect bad examples, duplicates, missing labels, and off-goal media. |
| Augment + upscale | Create derived branch variants while leaving originals untouched. |
| Additional labeling | Re-label variants and track lineage. |
| Final selection | Freeze keep/exclude decisions for training. |
| Export / handoff | Write manifests/configs for external training tools. |
| Rule application | Dry-run or apply deterministic cleanup to branch-local tag/caption sidecars. |

## Diffusion target presets

Available target presets include SeaArt-style service targets, SDXL, Illustrious, NoobAI, Anima, Krea 2, Ideogram 4, Wan 2.2, and LTX 2.3.

These presets affect rule wording, caption style, readiness checks, and export metadata. They do not imply that the tool trains those models internally.

## Dataset goals

| Goal | Caption/tag emphasis |
| --- | --- |
| Style | Medium, line quality, palette, lighting, rendering, texture, composition, camera/lens, era/genre. |
| Character | Identity, body structure, proportions, species/body type, recurring outfit, markings, colors, face/eye/hair/fur/skin details. |
| Character + style | Separate character and style anchors where needed, preserving body structure and style vocabulary. |
| Concept | Object/action/effect/material/relationship descriptors isolated from incidental identity or style noise. |

## Adapter families

The rule system supports LoRA, IC-LoRA, ControlNet, and embedding/textual-inversion preparation.

IC-LoRA examples need condition/reference input, target output, and a relationship/task prompt. ControlNet examples need a target image, conditioning image/map, and caption. Embedding examples need captions that keep the special token from absorbing unrelated details.

## Applying rules with models

Use **Build Caption/Tag Rules** to produce a strict model-readable packet. Use **Build Model/VLM Prompt** when a local/cloud LLM, VLM, VLLM, or GLM should review branch items. Use **Dry-Run Label Rules** before writing anything. Use **Apply Rules to Branch** only after review; it edits branch-local sidecars and does not mutate global originals. The model should return keep/remove/add/caption/confidence/review decisions for branch sidecars.

## Readiness checks

Use **Evaluate Branch Readiness** before export. The report checks item count, trigger coverage, missing sidecars, tag/caption length, review warnings, video metadata, ControlNet conditioning notes, and IC-LoRA relationship notes.

## External trainer handoff

Export options currently target external interfaces such as Kohya SS/sd-scripts, OneTrainer, Diffusers scripts, LTX Trainer, ComfyUI training/preprocessing nodes, generic cloud/API training providers, and future source-manifest/webscraper bridges for approved ingest workflows.

Training must still happen in those external tools after review.

## 3D-print handoff

The 3D Print / Slicer Handoff section packages generated/imported 3D assets for Blender, ZBrush, MeshLab, PrusaSlicer, OrcaSlicer, Cura/CuraEngine, Bambu Studio, Slic3r, or another slicer.

The package includes a manifest, source copy, target-format plan, repair policy, and MCP/handoff instructions. Printer-specific G-code should only be created after the user verifies scale, manifold status, printer profile, filament, supports, and safety settings.

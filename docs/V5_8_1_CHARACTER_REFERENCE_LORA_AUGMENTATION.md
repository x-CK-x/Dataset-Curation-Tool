# v5.8.1 — Character Reference, Pruning, LoRA Augmentation, and Regularization Planning

This update adds two related automation layers:

1. **Character Reference**: a zero/one/few-shot image-pruning workflow for finding a target character without training a new model.
2. **LoRA Augmentation / Regularization Planning**: branch-local augmentation presets and regularization guidance for style, character, character+style, concept, IC-LoRA, ControlNet, and embedding/textual-inversion prep.

## Character Reference

The new Character Reference tab is designed for cases where a user has too many images and only wants the subset containing a particular character. The workflow is profile-based:

1. Add a target name.
2. Add one or more positive reference images.
3. Optionally add negative references that are visually similar but not the target.
4. Rank a selected folder, dataset, branch, or current media selection.
5. Review match / uncertain / reject groups.
6. Optionally apply the pruning result to a global-dataset branch.

The default implementation uses deterministic local image features so the feature works without new model weights. The catalog also exposes DINOv2, CLIP/SigLIP, OWLv2 image-guided detection, and Grounding-DINO/SAM/SAM2 proposal contracts for stronger no-new-training backends when those dependencies and weights are installed.

## Character profile memory

Character profiles store compact prototype metadata, not a new trained model. A profile may contain:

- reference image paths
- positive reference paths
- negative reference paths
- prototype embedding summary
- negative prototype summary
- crop strategy
- score threshold

The service can rebuild a profile from ranked runs so accepted high-scoring examples become positives and rejected low-scoring examples become suppressors. This gives an active-learning-like feedback loop without requiring a training job.

## Branch pruning

Character Reference integrates with the Global Dataset layer. When ranking a branch, scores are attached to branch items. A pruning plan can then:

- keep only matches
- exclude rejects
- mark uncertain items for review

This changes branch configuration and sidecar workflow state. It does not delete or mutate global originals.

## LoRA augmentation policies

Dataset Pipeline / Pipeline Prep now exposes augmentation and regularization presets for the common adapter goals:

- character LoRA
- character + style / OC + style LoRA
- style LoRA
- concept/object/action LoRA
- IC-LoRA
- ControlNet
- embedding / textual inversion

The planner distinguishes operations that are usually useful from operations that should be disabled by default. Examples:

- Character branches get headshot/face-detail crops, upper-body crops, and bucket-safe copies.
- OC+style branches get identity crops plus style/texture crops.
- Style branches focus on texture, linework, palette, and composition crops rather than identity-only crops.
- Concept branches use object/concept-centered and context-preserving crops.
- ControlNet branches require paired condition-map alignment after geometric transforms.
- Embedding/textual-inversion branches avoid synthetic expansion and prefer fewer clean examples.

## Regularization guidance

The regularization planner creates manifest-ready guidance rather than silently adding class-prior data. It records:

- when regularization is recommended
- when it should be skipped
- caption rules for class/prior images
- ratio hints
- manifest fields for external trainers

Regularization/prior-preservation images remain separate from training positives so external trainers can map them to their own class/prior-preservation fields.

## Safety and data-layer rules

- Global originals are read-only.
- Augmentation outputs are branch variants.
- Sidecars are copied/edited in the branch layer.
- Strong/stochastic augmentations are not enabled by default.
- Character identity and style-defining details are not intentionally altered unless the user opts into that transform.

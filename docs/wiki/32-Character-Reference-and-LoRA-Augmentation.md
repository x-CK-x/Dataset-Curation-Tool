# Character Reference and LoRA Augmentation

This page covers the v5.8.1 character-reference and LoRA-prep automation features.

## Character Reference tab

Use this when you have a folder, dataset, current selection, or global-dataset branch and only want images containing a specific character.

Basic flow:

1. Open **Character Reference**.
2. Enter the target character name.
3. Add positive reference image paths, one per line.
4. Optionally add visually similar negative reference paths.
5. Choose a scope: current selection, dataset, folder, or global-dataset branch.
6. Build/update the profile.
7. Run rank/prune.
8. Review match, uncertain, and reject results.
9. Apply the pruning decision to a branch only when the result looks correct.

The profile does not train a new model. It stores compact reference/prototype metadata and can use verified positives/negatives to improve future scoring.

## Available character-reference methods

| Method | Purpose | Notes |
|---|---|---|
| Deterministic fallback | Always-available smoke-test matcher | Works without GPU/model downloads; not a final SOTA verifier. |
| DINOv2 embedding | Few-shot visual retrieval | Good for visual prototype matching without fine-tuning. |
| CLIP/SigLIP embedding | Cross-domain image similarity | Useful when text/image semantic alignment matters. |
| OWLv2 image-guided detection | One-shot object/character localization contract | Staged as a model-backed backend when optional deps are installed. |
| Grounding-DINO + SAM/SAM2 | Proposal plus mask/crop verification contract | Useful when the character is not the whole image. |

## Active profile memory

After a rank/prune run, accepted examples can become positive memory and rejected examples can become negative memory. Rebuilding the profile from a run lets the profile become more precise without model training.

## Branch pruning

When a global-dataset branch is selected, the pruning plan can modify branch item configuration:

- **include matches only**
- **exclude rejects**
- **mark uncertain**

This never deletes global originals. It only changes branch-level inclusion/review state.

## LoRA augmentation planner

The Dataset Pipeline tab includes **Plan LoRA Augmentations**, **Create Branch Variants**, and **Regularization Plan** controls.

| Dataset goal | Default useful branch variants | Avoid by default |
|---|---|---|
| Character | headshot crop, upper-body crop, square/bucket copy, optional light denoise/upscale | random color jitter, unverified flips, crops that remove identity anchors |
| Character + style / OC + style | headshot, upper-body/body-structure, style/texture crop, bucket copy | palette-changing transforms, aggressive denoise, flips for asymmetric characters |
| Style | style/texture crop, composition crop, palette/linework reference variants | identity-heavy crops unless portrait style is the target |
| Concept | object/concept crop, context crop, bucket copy | crops that remove the concept or interaction context |
| ControlNet | paired image/condition manifests, condition alignment checks | any crop/resize that does not regenerate/update the condition map |
| Embedding / textual inversion | small clean square/bucket set, optional identity crop | multiplying noisy variants or over-describing the learned token |

## Regularization / prior preservation

Regularization is not automatically applied to every branch. The planner makes it explicit because bad regularization can dilute the exact identity/style/concept the user wants to learn.

Use regularization when it solves a measurable problem, such as:

- subject identity leaking into the whole class
- style binding to one repeated subject
- concept over-applying to unrelated scenes
- a DreamBooth-style trainer requiring prior-preservation class images

Skip or reduce it when:

- the source branch is already diverse
- regularization images are low-quality or off-domain
- the goal is intentionally a fixed OC+style bundle
- the adapter type is very sensitive to noisy expansion, such as textual inversion

Regularization captions must not include the trained trigger token.

## Output locations

Character-reference output is stored under:

```text
outputs/character_reference/
```

Branch-local variants are stored under the selected branch root, usually:

```text
<global_dataset_root>/branches/<branch_name>/variants/
```

Branch sidecars remain under:

```text
<global_dataset_root>/branches/<branch_name>/sidecars/
```

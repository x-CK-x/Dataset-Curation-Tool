# Global Dataset, Branches, and Variants

![Global dataset overview](assets/images/data_curation_operations_playbook_design.png)

The Global Dataset tab is the tool's single-original storage layer. It keeps one original copy of each unique media file and uses database/config mappings to reuse that original across many dataset branches.

## Concept

| Area | Stored here | Edited here |
|---|---|---|
| Global originals | Unique media files, source mappings, canonical tags/captions, asset manifests | No routine training edits |
| Branch datasets | Dataset manifests, editable tag/caption sidecars, variant records | Yes |
| Variants | Augmented/derived media for a branch | Yes, as branch-specific derived data |

## Recommended workflow

1. Enable **Global Dataset**.
2. Download or ingest original media.
3. Create a branch for a model/dataset goal.
4. Link originals into the branch.
5. Edit the branch tag/caption copies.
6. Register augmented media as variants when augmentation produces real media files.

## Why this exists

This prevents repeatedly redownloading or duplicating the same original data while still allowing different model datasets to have different tag/caption edits. The original layer remains clean and reusable.

## API surface

```text
GET  /api/global-dataset/status
GET  /api/global-dataset/assets
POST /api/global-dataset/register-file
POST /api/global-dataset/ingest-folder
POST /api/global-dataset/branches
POST /api/global-dataset/branches/link
POST /api/global-dataset/variants
```

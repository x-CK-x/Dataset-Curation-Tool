# v5.78.12 — Global Dataset Layer, 3D Catalog Expansion, and ZBrush MCP

This update adds a global-original dataset layer and extends the 3D/MCP catalog.

## Global dataset architecture

The new **Global Dataset** tab stores original media once by SHA-256 and tracks source mappings separately. This lets the downloader and manual ingest paths avoid duplicate original storage when the same post/file is encountered again.

The system is split into two layers:

| Layer | Purpose | Mutability |
|---|---|---|
| Global originals | Unique media files, source mappings, canonical tags/captions, manifests | Preserved as original source data |
| Branch datasets | Model-specific dataset configs, editable tag/caption sidecar copies, variants | Editable per training/curation goal |

Branches do not need to duplicate original media. They write lightweight manifests under the branch folder and copy only the tag/caption sidecars that the user edits for that branch. Augmented media is stored as a branch variant and linked back to the global original asset.

## Downloader integration

When enabled, downloaded files are automatically registered into the global dataset. If a later download request references an already-known source post or URL, the downloader attempts to reuse the existing global original by hardlink/copy/symlink policy instead of redownloading the media.

## Added API endpoints

```text
GET  /api/global-dataset/status
PUT  /api/global-dataset/settings
GET  /api/global-dataset/assets
POST /api/global-dataset/assets/search
GET  /api/global-dataset/assets/{asset_id}
POST /api/global-dataset/register-file
POST /api/global-dataset/ingest-folder
GET  /api/global-dataset/branches
POST /api/global-dataset/branches
GET  /api/global-dataset/branches/{branch_id}/items
GET  /api/global-dataset/branch-references
POST /api/global-dataset/branches/link
POST /api/global-dataset/variants
```

## 3D/MCP catalog additions

Added catalog/provider rows for:

- Dream Textures Blender add-on/backend bridge
- QuickMaker Blender AI suite bridge
- Meshy official API text/image-to-3D row
- Blender official MCP add-on/server handoff
- ZBrush Python/MCP sculpt-refinement bridge
- ZBrush MCP tool-control row

The Dream Textures, QuickMaker, Blender MCP, and ZBrush providers create approved handoff manifests. They do not silently execute external creative-tool commands from the web app.

## Runtime settings

New settings fields:

```json
{
  "global_dataset_enabled": true,
  "global_dataset_root": null,
  "global_dataset_originals_dir": "originals",
  "global_dataset_branches_dir": "branches",
  "global_dataset_variant_dir": "variants",
  "global_dataset_ingest_copy_mode": "copy",
  "global_dataset_auto_register_downloads": true,
  "global_dataset_auto_link_downloads_to_branch": false,
  "global_dataset_default_branch": "default"
}
```

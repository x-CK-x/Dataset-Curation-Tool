# Install Migration and Symlinks

<!-- DCT_VISUAL_START -->
![Install migration and symlink visual guide](assets/images/project_folder_layout_migration.png)
<!-- DCT_VISUAL_END -->


The **Install Migration** tab helps move or copy reusable assets from older app installs into a newer build.

## Why migration exists

When testing frequent builds, repeatedly downloading the same models and tag DB exports wastes time and bandwidth.

Migration is intended to reuse:

- Model snapshots.
- Tag DB export files.
- Imported tag dictionary rows.
- Custom model catalogs.
- Custom tags.
- Optional presets/download cache/outputs.

## Basic migration workflow

1. Open **Install Migration**.
2. Add one or more older install roots.
3. Put the newest prior install first when possible.
4. Scan.
5. Review model groups and skipped reasons.
6. Choose copy or move.
7. Run migration.
8. Open **Models** and refresh/rescan.
9. Open **Tag Dictionaries** and refresh status.

## Move vs copy

| Mode | Use when |
| --- | --- |
| Copy | You want to keep old installs intact. |
| Move | You want to consolidate and then delete old installs. |

When moving, verify the new install works before deleting old folders.

## Model migration behavior

Migration should move valid model groups and skip truly incomplete/corrupt groups.

Hard skip examples:

- Zero-byte weight files.
- Folder has only temporary `.part` files.
- Required sharded weight file referenced by an index is missing and no valid weight payload exists.

Support warnings should not block migration when valid weights exist. Examples:

- Missing chat template.
- Missing Florence remote-code helper.
- Missing lightweight processor/config file.

Those can often be repaired by **Re-download / Update** without re-downloading full weights.

## Using symlinks for large model drives

Symlinks let the app see models under `models/` while the actual files live on a larger drive.

### Windows directory symlink

Open Command Prompt as a user with permission to create symlinks, then:

```bat
mkdir D:\DCT_Models
move models\hf D:\DCT_Models\hf
mklink /D models\hf D:\DCT_Models\hf
```

If Developer Mode is enabled, user-level symlink creation is easier. Otherwise Windows may require elevated permissions.

### Linux symlink

```bash
mkdir -p /mnt/bigdrive/DCT_Models
mv models/hf /mnt/bigdrive/DCT_Models/hf
ln -s /mnt/bigdrive/DCT_Models/hf models/hf
```

## Recommended external model layout

Example:

```text
D:\DCT_Assets\
  models\
    hf\
    ultralytics\
    checkpoints\
    custom\
  tag_exports\
```

Then symlink into the project:

```text
DataCurationToolModern\models\hf -> D:\DCT_Assets\models\hf
DataCurationToolModern\runtime\tag_exports -> D:\DCT_Assets\tag_exports
```

## Important symlink cautions

- Do not create a symlink loop.
- Do not point two running app instances at the same writable database.
- It is safer to share model folders than to share `runtime/app.db`.
- Keep backups before moving assets.
- Use refresh/rescan after creating links.

## Cleaning old installs

After migration:

1. Confirm models show as downloaded in the new install.
2. Load/unload a few representative models.
3. Confirm tag dictionary counts/status.
4. Confirm custom models/custom tags.
5. Only then delete old installs.

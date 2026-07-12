# v5.8.21 — Fast Same-Drive Model Migration

This update fixes the slowest migration path: moving large model folders from an older install into the new install.

## Problem

Previous migration builds used a safe chunked copy-and-delete operation even when the user selected **Move** mode and both installs were on the same SSD/drive. For very large model folders, this meant hundreds of GiB were read and written again:

```text
Move models in parallel · 2508/2556 file(s) · 663.77/671.13 GiB
```

That is correct for cross-drive moves, but it is unnecessarily slow for same-volume migrations.

## Fix

Move mode now prefers a filesystem rename/replace path before falling back to copy-and-delete:

1. Create the target parent folder.
2. Try `Path.replace(target)` / `os.replace`.
3. If the source and target are on the same filesystem, the move is metadata-only and effectively instant for large files.
4. If the OS reports a cross-device or blocked rename, fall back to the existing chunked copy-and-delete path.
5. Keep progress reporting alive in both paths.

## UI

Install Migration now includes:

```text
Fast same-drive moves
```

This is enabled by default. It applies only to **Move** mode. Copy mode still copies bytes, and Symlink mode still creates links.

## Settings

New setting:

```json
"migration_fast_same_volume_moves": true
```

The setting is saved with migration startup settings and is reused by startup migration.

## Expected behavior

For same-drive SSD migrations, large model movement should avoid rewriting hundreds of GiB. For cross-drive moves, the app automatically falls back to the prior chunked copy path.

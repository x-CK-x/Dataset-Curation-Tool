# Fast Same-Drive Model Migration

Large model migrations should not rewrite model shards when the old install and new install are on the same SSD or drive.

## What changed

The Install Migration tool now has a **Fast same-drive moves** checkbox. It is enabled by default.

When migration is in **Move** mode, the app tries to move each file with a filesystem rename/replace operation. On the same volume, this is a metadata operation rather than a byte-for-byte copy. If the move crosses drives or the OS refuses the fast rename, the app falls back to the existing chunked copy-and-delete path.

## Recommended settings for SSDs

Use:

```text
Mode: Move files into this install
Parallelize file transfers: enabled
Transfer workers: 4–8
Fast same-drive moves: enabled
Local-only migration: enabled when migrating from a complete previous install
```

## Recommended settings for HDDs or external drives

Use:

```text
Parallelize file transfers: disabled or 1–2 workers
Fast same-drive moves: enabled
```

The fast move option is still safe on HDDs; the worker count is the option that usually needs to be reduced for slower drives.

## Why this matters

A migration job that previously showed progress like:

```text
Move models in parallel · 2508/2556 file(s) · 663.77/671.13 GiB
```

was copying model bytes before deleting the source. On a same-drive migration, that should now complete by renaming files into place whenever possible.

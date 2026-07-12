# Migration Fast Model Groups and Progress Fix

v5.8.22 improves the Install Migration workflow for very large model folders.

## Problem fixed

A migration could sit around 70–71% with a message such as:

```text
Move models in parallel · 2252/2552 file(s) · 644.97/671.16 GiB
```

This was misleading and slow for two reasons:

1. The migration UI compressed the raw file-transfer phase into the first 75% of the overall job.
2. Model folders were expanded into thousands of independent file operations even when the whole model directory could be moved as one complete asset.

## New behavior

- Missing model groups are moved as whole directories when possible.
- Existing complete target model groups are detected and skipped instead of copied again.
- Runtime duplicate checks prevent re-copying a large file if the target file already exists and has the expected size.
- If source duplicate deletion is enabled, already-migrated duplicate model groups are removed from the old install after verification.
- The Jobs row and Dashboard Startup Maintenance card now use a more accurate progress mapping.

## Best practice

For fastest migration on SSDs:

- Use **Move** mode when the old and new installs are on the same drive.
- Keep **Fast same-drive moves** enabled.
- Keep **Local-only migration** enabled if the old install already has tag exports/models.
- Use parallel workers for cross-drive copies, but same-drive moves should complete mostly by filesystem rename.

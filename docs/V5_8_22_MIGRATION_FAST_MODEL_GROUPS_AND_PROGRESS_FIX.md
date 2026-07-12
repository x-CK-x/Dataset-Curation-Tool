# v5.8.22 — Migration Fast Model Groups and Progress Fix

This update fixes a migration behavior where model migration could appear stuck around 70% while large model assets were already mostly present in the new install.

## What changed

- Model folders can now be migrated as complete atomic model groups instead of always expanding every model into thousands of per-file operations.
- In move mode, a complete missing model group is planned as one `move_dir_fast` operation.
- If a target model group already exists and contains the same reusable files by relative path and size, migration now short-circuits it as a duplicate group.
- If `delete_source_duplicates` is enabled, duplicate source model groups are removed after the target is verified.
- Transfer execution re-checks targets at runtime before copying/moving a file. If the target file is already complete, the tool does not rewrite the file again.
- Migration progress is no longer compressed into only the first 75% of the migration job. File migration now maps into roughly the first 90%, with the final 10% reserved for catalog/database/tag reconciliation.

## Why this matters

Large model folders can contain hundreds of GiB of shards, config files, tokenizer files, safetensors, GGUF files, and cache metadata. Moving these assets one file at a time is slow and can make the UI look stuck even when the target install already has the data. This version prefers filesystem-level directory moves and duplicate-group short-circuiting so same-drive migrations finish much faster.

## Notes

Fast directory moves are only instant when the old and new install locations are on the same filesystem/volume and the target model group does not already exist. Cross-drive migrations still require byte copying.

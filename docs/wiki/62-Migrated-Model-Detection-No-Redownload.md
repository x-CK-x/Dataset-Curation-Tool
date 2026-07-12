# v5.8.32 — Migrated Model Detection and No-Redownload Load Fix

v5.8.32 fixes model migration reconciliation so migrated models are usable without forcing another large download.

## What was wrong

A model could be detected as downloaded because files existed in the migrated install folder, but the later load path could still pass a stale repo id or unresolved path into a Hugging Face/Transformers loader. That could cause a second download when the user clicked **Load Into Memory**.

## What changed

- The registry resolves migrated local model payloads before any remote repo id is used.
- Hugging Face cache containers such as `models--org--repo/snapshots/<revision>` resolve to the actual snapshot directory.
- Load/chat calls set `local_files_only=True` when a local payload is found.
- Missing downloadable local models now fail with an actionable local-only error instead of downloading implicitly.
- The Models tab includes **Rescan / Reconcile Migrated Models** for post-migration detection without network access.

## Recommended use after migrating

1. Open **Models**.
2. Click **Rescan / Reconcile Migrated Models**.
3. Confirm the model rows show as downloaded.
4. Click **Load Into Memory**.

If a row does not become downloaded, add the older install's `models` folder as an external model root or move the model folder into one of the supported local layouts.

## Catalog stability guard

Candidate model folders are now de-duplicated with a normalized path identity key instead of repeatedly resolving every non-existent alias. This prevents the Models tab from getting stuck while checking many possible migrated Hugging Face/cache layouts.

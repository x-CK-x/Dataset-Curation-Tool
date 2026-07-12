# v5.8.23 — Migration Tag-Database Stall Fix

This update fixes a migration/startup-maintenance hang where the Dashboard could sit at roughly 88% with a message such as:

```text
Importing 196 row(s) from migrated tag table tag_export_files
```

## Cause

The migration tag-database import could emit progress while the same migration connection still held a SQLite write transaction. The progress callback writes to the `jobs` table through another connection, so the UI could appear stalled while the progress write waited for the migration transaction to release the database.

The table shown in the stall, `tag_export_files`, is also metadata from the previous install. Its `local_path` values point at the old install and should be rebuilt from the migrated `runtime/tag_exports/<profile>/` files instead of imported directly.

## Fixes

- The import no longer holds the app-wide database lock for the full tag-table migration.
- The import now commits before calling external progress callbacks.
- The import commits after every row chunk to keep SQLite locks short.
- `tag_export_files` is skipped during database-row migration and rebuilt from migrated local cache files.
- The redundant legacy `tag_dictionary` mirror is skipped when the modern normalized dictionary tables are present.
- Jobs/Dashboard progress can update live while tag rows are imported.

## Expected behavior

On retry, migration should skip stale export-file metadata, rebuild local export-file status from the migrated cache, and continue past the prior 88% stall.

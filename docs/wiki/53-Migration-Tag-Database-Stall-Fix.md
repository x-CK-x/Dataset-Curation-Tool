# Migration Tag-Database Stall Fix

This page covers the v5.8.23 fix for migrations that appeared stuck during startup maintenance after model migration completed.

## Symptom

The Dashboard showed a running startup-maintenance job that stayed on a message like:

```text
Importing 196 row(s) from migrated tag table tag_export_files
```

The percentage might stay near 88% for a long time even though the main model-folder migration already appeared complete.

## What changed

The migration importer now treats `tag_export_files` as rebuildable cache metadata instead of importing stale rows from the old install. Those rows contain old local paths and are regenerated from the files that were migrated under `runtime/tag_exports/<profile>/`.

The importer also commits before progress callbacks and after every table chunk. That prevents the migration import from blocking the job-progress update that feeds the Dashboard indicator.

## Result

A retry migration should move past this phase quickly. The Dictionary card and Tag Dictionaries tab should still recover local export information through cache reconciliation.

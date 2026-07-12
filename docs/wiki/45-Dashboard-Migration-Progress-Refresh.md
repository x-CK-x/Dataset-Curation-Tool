# Dashboard Migration Progress Refresh

The Dashboard has a manual refresh control for startup and migration maintenance status.

## Why this exists

Manual install migration can happen after first-run startup. If the first-run tag download was cancelled, migration effectively becomes part of the initialization path because the tool still needs to reconcile models, tag exports, tag database rows, and cache state before the current install is fully ready.

## Controls

- **Dashboard → Refresh Dashboard Now** refreshes summary counts, recent jobs, dictionary status, and startup-maintenance status.
- **Startup Maintenance Progress → Refresh Dashboard** refreshes the same live maintenance status directly from the progress card.
- **Open Job** opens the associated Jobs detail row when a startup or migration job is attached.

## Live migration updates

The migration worker now reports progress during these phases:

| Phase | What the user sees |
| --- | --- |
| Preparing | previous install count and source ordering |
| Scanning | source path being scanned and migration plan creation |
| File migration | active file, percent copied, and approximate file size |
| Tag database import | active migrated table and copied row counts |
| Reconciliation | custom model reload, model asset reconciliation, tag-export cache reconciliation |
| Post-migration sync | tag dictionary sync progress if cache is still missing or stale |

## Expected behavior

The Dashboard card should become live as soon as migration is queued. If it does not appear because the Dashboard was already rendered with stale state, press **Refresh Dashboard Now**. Future automatic polling uses no-cache requests, so the progress state should continue updating after that.

# v5.8.15 Dashboard Migration Progress Refresh

v5.8.15 focuses on making manual install migration visible from the Dashboard immediately, instead of only showing the final completion record after a long migration has already finished.

## Changes

- Added a **Refresh Dashboard Now** button to the Dashboard.
- Added a secondary **Refresh Dashboard** button directly inside the Startup Maintenance card.
- The startup-status endpoint now returns no-cache headers so the browser does not reuse stale progress state.
- The frontend now requests startup status with cache-busting when live migration/startup maintenance is active.
- Manual migration now creates an optimistic Dashboard startup-maintenance state as soon as the migration job is queued.
- Asset migration now emits progress while scanning previous installs, building the migration plan, copying large files, and importing migrated tag database tables.
- Large copied/moved files use a chunked copy path so the Job row and Dashboard Startup Maintenance circle receive heartbeat updates instead of appearing idle during multi-GB transfers.
- Migrated tag-database imports now report progress per table and in row chunks for large tables.

## User workflow

1. Start migration from **Install Migration**.
2. Switch to **Dashboard**.
3. Press **Refresh Dashboard Now** if the Dashboard was already open or if the migration job started before the page was refreshed.
4. Watch **Startup Maintenance Progress** for phase, percent, elapsed time, ETA, job id, and recent steps.

## Notes

Some operating-system operations can still block inside the filesystem or SQLite engine for short periods, but the tool now emits progress before and between long phases so the user sees what is happening instead of a silent page.

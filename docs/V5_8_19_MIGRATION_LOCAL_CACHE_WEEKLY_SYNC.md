# v5.8.19 — Migration Local Cache Reuse and Weekly Startup Sync Gate

This update prevents the app from repeatedly downloading tag/export material during startup and migration when an older installation already contains the reusable cache/database rows.

## Changes

- Added a local-only migration flag that is enabled by default.
- Manual migration and startup migration now skip post-migration internet tag refreshes when local-only mode is enabled.
- Migration can import already-copied `runtime/tag_exports/<profile>/` files directly into the current tag dictionary without a network request.
- Startup tag-dictionary sync is now gated by `tag_db_startup_sync_interval_hours`, defaulting to 168 hours / 7 days.
- The default tag export cache staleness window is now 168 hours / 7 days.
- Older installs that still have the previous 336-hour default are migrated down to the new weekly default when settings load.
- Added UI controls for:
  - local-only migration / skip internet refresh,
  - tag export stale-after hours,
  - startup network-check interval hours.

## Behavior

When migrating from a previous install, the preferred path is:

1. copy/move/symlink models and runtime assets,
2. import migrated tag database rows,
3. reconcile copied tag export files,
4. import cached local tag exports if the dictionary is still empty/incomplete,
5. skip network refresh unless the user disables local-only migration.

For normal startup, the app still checks dictionary state, but automatic network sync attempts are limited to once per configured interval. The default is once per week.

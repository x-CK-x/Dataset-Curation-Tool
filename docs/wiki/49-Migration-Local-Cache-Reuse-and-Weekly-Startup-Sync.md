# Migration Local Cache Reuse and Weekly Startup Sync

The install migration workflow now prefers reusable material from older installs instead of re-downloading it from the internet.

## Local-only migration

The **Install Migration** tab includes a local-only option:

> Local-only migration: do NOT download internet refreshes after migration

Leave this enabled when the older install already has models, tag export files, imported tag database rows, custom tag files, custom model registries, presets, downloads, or outputs that should be reused.

## What gets reused

Migration can reuse:

- model folders and checkpoints,
- cached tag export files under `runtime/tag_exports/`,
- already-imported tag dictionary database rows,
- custom tags,
- custom model registry rows,
- optional presets/downloads/outputs.

If tag export files are copied but the current database has no imported dictionary rows yet, the app can parse those local export files directly. This avoids an immediate internet refresh.

## Weekly startup sync gate

Startup tag sync no longer tries the network on every launch. The default interval is:

```text
168 hours = 7 days
```

The setting is exposed in **Settings → Tag DB Exports Startup Sync** as:

- `Tag DB export stale after hours`
- `Startup network check interval hours`

## Manual override

A user can still force a fresh dictionary sync from the Tag Dictionaries tab. The weekly gate only applies to automatic startup refresh behavior.

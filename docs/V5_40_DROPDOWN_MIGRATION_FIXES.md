# v5.40 Dropdown Stability and Previous-Install Asset Migration

## Dropdown / select stability fix

The app's automatic 3-second polling refresh now treats open `<select>` controls as active editing controls, the same way v5.39 handled text inputs and textareas. Automatic renders are deferred while the user is choosing a model, tag profile, category, downloader option, runtime option, or other dropdown value. This prevents the dropdown from being destroyed/recreated by polling before the user can select an option.

## New Install Migration tab

The new **Install Migration** tab is intended to reduce repeated setup work when testing new builds. It accepts one or more previous install folders and can move or copy reusable assets into the current install layout.

Supported reusable assets:

- `models/` → current `models/`
- `runtime/tag_exports/` → current `runtime/tag_exports/`
- imported tag dictionary database rows from `runtime/app.db`
- `runtime/custom_tags.json`
- optional `runtime/presets/`
- optional `runtime/downloads/`
- optional `outputs/`

The migration processes newer installs first by default. When multiple old installs contain the same relative model/export file, the first/newest source wins and older conflicting copies are skipped. Older installs can still contribute unique model folders or tag export files that did not exist in newer installs.

## Moving vs copying

Manual migration defaults to **move**, because the goal is to let old installs be deleted after assets are transferred. A copy mode is also available when a safer non-destructive test is preferred.

Recommended first pass:

1. Add all previous install folders.
2. Click **Scan Sources**.
3. Click **Queue Dry-run**.
4. Review the job details.
5. Run the real move/copy operation.

## Startup migration

Startup migration runs before startup tag DB-export sync. This lets the app reuse prior cached tag export files and imported dictionary rows before it decides whether a network sync is necessary.

The Install Migration tab can save startup settings. Advanced launch overrides are also supported:

```bat
set DCT_PREVIOUS_INSTALLS=C:\path\to\old_install_1;C:\path\to\old_install_2
set DCT_MIGRATE_ON_STARTUP=1
set DCT_SKIP_STARTUP_TAG_SYNC=1
run.bat
```

`DCT_SKIP_STARTUP_TAG_SYNC=1` prevents a network tag DB sync during that launch while still allowing startup asset migration to run.

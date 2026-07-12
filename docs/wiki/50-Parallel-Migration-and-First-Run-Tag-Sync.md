# Parallel Migration and First-Run Tag Sync

v5.8.20 improves migration speed and fixes first-run tag dictionary bootstrap behavior.

## Parallel migration transfers

The Install Migration tab now has:

| Control | Default | Purpose |
|---|---:|---|
| Parallelize file transfers | enabled | Copies/moves independent files concurrently. |
| transfer workers | 4 | Number of migration file-transfer workers. |
| Local-only migration | enabled | Reuses migrated cache/database rows and skips post-migration internet refreshes. |

For SSDs, four workers should usually be faster than one worker. For HDDs, network shares, or unstable external drives, disable parallel transfers or set workers to `1`.

## First-run bootstrap behavior

A new install with no migrated dictionary rows should bootstrap its active/default tag dictionary automatically. The weekly startup gate no longer blocks a missing/empty dictionary just because an earlier failed check wrote a recent-check marker.

After the dictionary exists, startup network checks are gated by the configured interval, defaulting to once every seven days.

## Manual update controls

Use **Settings → Tag DB Exports Startup Sync → Update Tag Dictionary Now** to force an immediate network update for the selected/default profile.

Use **Tag Dictionaries → Update Now / Force Refresh** to force an immediate update for the active profile.

## Recommended settings

For most users:

- Keep startup auto-sync enabled.
- Leave the interval at `168` hours.
- Leave `Sync only if dictionary is empty` off if you want weekly refreshes.
- Enable `Sync only if dictionary is empty` or disable startup auto-sync if you want to prevent automatic update checks after the first bootstrap.

# v5.8.20 Parallel Migration and First-Run Tag Sync Fixes

This update addresses two startup/migration bottlenecks.

## Parallel migration file transfers

Install Migration now exposes SSD-oriented parallel file transfers. The option is enabled by default and uses four workers unless the user changes it.

Controls added to **Install Migration**:

- `Parallelize file transfers`
- `transfer workers`

Behavior:

- Enabled + 4 workers by default.
- Disable the checkbox to return to one transfer at a time.
- Copy/move migration uses worker threads for independent file operations.
- Symlink mode remains lightweight and does not need transfer workers.
- Dashboard/Jobs progress aggregates completed bytes and completed file count across workers.

Use fewer workers for HDDs, fragile USB drives, network shares, or drives that become slower under parallel I/O.

## First-run tag dictionary bootstrap

Startup tag dictionary sync now distinguishes between a non-empty dictionary that was checked recently and a truly empty first-run install.

If the selected/default tag profile has no imported rows, startup can bootstrap immediately even if a previous failed/partial startup sync wrote a recent-check marker. After the dictionary exists, normal weekly gating applies.

## Weekly update controls

Settings now treat startup tag dictionary sync as a weekly refresh by default, not an every-launch download. Users can still disable it entirely or force an update manually.

Controls:

- **Auto-sync tag DB exports on startup when needed**: enable/disable automatic weekly startup checks.
- **Sync only if dictionary is empty**: optional stricter mode for users who do not want periodic refreshes after first bootstrap.
- **Startup network check interval hours**: default `168` hours.
- **Update Tag Dictionary Now**: forces an immediate update for the selected/default profile.

The Tag Dictionaries tab also has **Update Now / Force Refresh** for the active profile.

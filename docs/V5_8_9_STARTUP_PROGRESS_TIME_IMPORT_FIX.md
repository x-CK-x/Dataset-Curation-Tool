# v5.8.9 — Startup Progress Time Import Fix

This release fixes a startup initialization crash introduced by the live startup progress/ETA card.

## Fixed

- Added the missing `time` import used by the deferred startup initialization job.
- Kept the Dashboard startup progress indicator active for tag-mode migration, asset reconciliation, optional model preload, and tag dictionary sync.
- Replaced the hardcoded startup-sync user-agent version with the package `__version__`.

## Validation

- Python compile checks for `app.py`, the system router, and startup progress service.
- Frontend syntax check for `static/app.js`.
- Regression coverage for the missing import and versioned startup user-agent.

# Hydra UTF-8, Startup Progress, and Gallery Fixes

## Hydra 3.5 local inference

Hydra's local repo-native inference writes a wide CSV table to stdout. Some tag labels contain Unicode symbols. On Windows, stdout can default to a legacy code page such as CP1252, which can fail before the application can parse predictions.

The Hydra adapter now runs the subprocess with UTF-8 settings and patches the downloaded `inference.py` to reconfigure stdout/stderr as UTF-8.

Expected local patch marker:

```text
models/hf/RedRocket--Hydra/.dct_hydra_compat_patch_v3.json
```

The earlier compatibility patches remain active for queue annotations and loader keyword drift.

## Startup progress on Dashboard

The Dashboard includes a white circular startup-maintenance progress indicator. It reports elapsed time, ETA, current phase, and recent startup steps.

The status endpoint is:

```text
GET /api/system/startup-status
```

Startup maintenance includes tag migration, asset migration, model reconciliation, tag export reconciliation, assistant preload queueing, and tag dictionary startup-sync checks.

## Gallery refresh and page limits

Explicit Gallery actions now force a visual refresh instead of waiting for a later tab switch:

- Search / Refresh
- Reload Page
- Refresh JSON/Sidecars + Reload
- Prev / Next page controls

The UI clamps the page number before and after loading, and the backend returns the clamped final page.

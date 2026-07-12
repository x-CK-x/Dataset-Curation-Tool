# v5.8.8 — Hydra UTF-8 Inference, Startup Progress, and Gallery Refresh Fixes

This release fixes the next Hydra 3.5 local inference failure and adds a live startup-maintenance indicator to the Dashboard.

## Hydra 3.5 UTF-8 subprocess fix

Hydra now reaches model inference, but on Windows the repo-native `inference.py` can write a very wide CSV header to stdout that includes Unicode tag labels such as gender symbols. If the child process inherits a CP1252 console encoding, Python can raise `UnicodeEncodeError` before the Data Curation Tool can parse the prediction table.

The adapter now:

- sets `PYTHONUTF8=1` for the Hydra child process;
- sets `PYTHONIOENCODING=utf-8` for the Hydra child process;
- decodes Hydra stdout/stderr with UTF-8 and replacement fallback;
- applies a narrow source patch to the downloaded `inference.py` to reconfigure stdout/stderr as UTF-8 on startup;
- keeps the earlier queue annotation and loader-API compatibility patches.

The patch marker is written to the downloaded Hydra repo as:

```text
.dct_hydra_compat_patch_v3.json
```

## Dashboard startup-maintenance progress

Startup maintenance now runs as a background maintenance thread instead of hiding long startup work behind an unresponsive first page load.

The Dashboard now shows a white circular progress indicator with:

- percent complete;
- current phase;
- status;
- current message;
- elapsed time;
- ETA when enough progress information is available;
- recent startup steps;
- failure details if startup maintenance fails.

The new API endpoint is:

```text
GET /api/system/startup-status
```

The startup tracker covers the known long startup phases:

1. tag text mode migration;
2. optional agent-tool smoke test;
3. optional voice preload queueing;
4. previous-install asset migration;
5. local model asset reconciliation;
6. tag export cache reconciliation;
7. assistant auto-load queueing;
8. startup tag dictionary sync policy and queueing.

## Gallery/navigation refresh fixes

The Gallery page controls now force visible refreshes after explicit user actions so pagination, reload, and sidecar refresh do not wait for a tab switch. The frontend also clamps the requested page before and after refresh, and the backend already clamps the final page value.


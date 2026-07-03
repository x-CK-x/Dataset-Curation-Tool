# v5.46 Job Cancellation and Retry Repair

This patch focuses on the Jobs tab and long-running download-style jobs.

## Fixed checked-job cancellation

The Jobs table now stores checked job IDs in persistent frontend state instead of a temporary table-local set. This prevents normal polling refreshes from visually preserving a checked box while erasing the selected ID internally.

The Jobs tab now supports:

- Stop Checked Jobs for queued or running jobs.
- Stop Queued/Running Downloads for model downloads, normal downloads, annotation-model downloads, and startup tag-dictionary/db-export sync jobs.
- Select Visible and Deselect Jobs helper actions.

## Startup tag DB export cancellation

Startup tag dictionary sync jobs use the `tag_dictionary_startup_sync` job type. These jobs are now treated as download-like jobs for cancellation and queue isolation. This means the download-stop controls can stop startup DB-export downloads instead of only stopping jobs whose type literally contains `download`.

The tag-export importer also checks cancellation during export-file streaming and between candidate files so a cancelled startup sync can exit cleanly instead of continuing through the entire export sequence.

## Download queue isolation

A dedicated generic download queue lane was added in addition to the existing model-download, model-load, and inference lanes. This keeps normal app work from being monopolized by long-running downloads or tag-export syncs.

Environment controls:

```text
DCT_DOWNLOAD_WORKERS=1
DCT_MODEL_DOWNLOAD_WORKERS=1
DCT_MODEL_LOAD_WORKERS=1
DCT_MODEL_INFERENCE_WORKERS=<n>
```

## Retry failed or cancelled downloads

A new retry endpoint was added:

```text
POST /api/jobs/retry
```

Supported retry types:

- normal downloader jobs: `download`
- model downloads: `model_download*`
- annotation model downloads: `annotation_model_download*`
- tag dictionary / DB-export jobs: `tag_dictionary*`, `db_export*`

The Jobs UI exposes:

- row-level **Retry from scratch** on failed/cancelled retryable jobs
- **Retry Checked Failed Downloads** for bulk repair

Retries are requeued as new jobs and default to `force_download=true` so failed downloads can be repaired individually from scratch.

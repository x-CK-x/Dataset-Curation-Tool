# v5.8.44 — Quick Queue Live Rows, Prediction Score Recovery, and Video Integrity Sampling

v5.8.44 is a focused reliability patch for the Tag Editor Quick Tag queue, persisted/visible prediction-score feedback, thumbnail throughput, and the Nightshade/Glaze integrity-classifier workflow.

## Quick Tag queue behavior

The Quick Tag multi-model queue now keeps all selected models visible as soon as a queue action is pressed.  The UI creates local placeholder job rows immediately for download, load, unload, and inference submissions, then replaces each placeholder with its real backend job ID when the backend returns it.

The **Submit queue requests in parallel** checkbox now means only this:

- enabled: submit all selected model requests at once;
- disabled: submit the selected model requests one by one;
- in both modes: every selected row is visible in the Quick Tag Model Queue immediately.

The live `/api/jobs` poller now preserves temporary client-side placeholder rows.  This prevents a slow backend response from replacing the queue with the server list and making multi-model Quick Tag queues appear to collapse to a single row.

## Prediction-score recovery and hover bars

Completed model inference jobs now patch per-media/model/tag score data directly from the job result before the full media refresh finishes.  This restores the Tag Editor hover prediction bars even when the slower tag-score cache reload races the active UI.

The backend also recovers probabilities from raw adapter output when normalization converts a scored prediction into a bare string tag.  Each queued model now applies only tags whose recovered score is at or above that model run's threshold.  If an adapter truly emits only already-thresholded strings and no recoverable probabilities, those strings are treated as accepted labels with score `1.0`.

## Nightshade / Glaze video support

The integrity-classifier workflow now accepts video assets.  Video checks sample frames using user-controlled options:

- enable/disable video sampling;
- highest-quality, balanced, fast-preview, or custom preset;
- sampling FPS;
- maximum sampled frames;
- output frame format: PNG, JPEG, or WebP;
- compression/quality percentage.

OpenCV is used first for frame sampling.  If OpenCV cannot open the video, the service falls back to `ffmpeg` when available.  Frame-level scores are aggregated per label using max score plus mean score and best-frame metadata.

## Gallery thumbnail path

The thumbnail path remains non-blocking and now has an OpenCV resize path.  CUDA resize is attempted when OpenCV CUDA support exists; otherwise OpenCV CPU resize is used before falling back to the PIL path.

## Validation

The v5.8.44 package was validated with Python compilation, frontend JavaScript syntax checking, shell-script syntax checking, selected regression tests, and ZIP integrity checking.  Live Windows browser timing, real RTX GPU memory movement, real booru/network behavior, and real custom Nightshade/Glaze model inference could not be tested in this environment.

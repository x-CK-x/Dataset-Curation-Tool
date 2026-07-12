# 66 — Import/Gallery Responsiveness and PixAI NCHW Fix

v5.8.36 fixes a set of import/gallery workflow blockers:

- passive polling no longer rebuilds heavy media tabs every few seconds;
- Import folder picker uses a child-process Tk dialog path with immediate UI feedback;
- import queueing avoids a full frontend refresh before opening Jobs;
- exact duplicate skipping now checks all active media by SHA-256;
- the default all-datasets Gallery view hides exact duplicate SHA rows where possible;
- Gallery media page conversion batches tag/caption lookups;
- quick tag/rating model dropdowns visually distinguish loaded, downloaded, and missing models;
- PixAI Tagger v0.9 now uses a detected NCHW ONNX input layout instead of the WD NHWC path.

The PixAI layout fix is isolated inside the WD/PixAI adapter and does not alter the already-working Thouph, JTP, Hydra, or other tagger paths.

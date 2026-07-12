# EVA Attention Pool and Live Tab Refresh Fixes

v5.8.25 addresses two regressions:

- Legacy EVA taggers could fail under newer `timm` with missing optional attributes such as `attn_pool`.
- Model/Gallery/Jobs/Error Log tabs could appear stale because normal button clicks triggered a multi-second render hold.

The frontend now allows immediate tab-local repaint after data refreshes while still avoiding shell replacement during active scrolling or active text/select editing.


The model-status endpoint also avoids frequent large-folder rescans, which reduces delay when watching model load/unload state or refreshing logs.

# v5.8.17 Graph Canvas Parity and Migration Finalization Speedups

v5.8.17 focuses on two reported usability failures: the Agentic Graph Editor looked correct but did not behave like the standalone graph editor, and migration/startup maintenance could appear stalled after visible progress reached 100%.

## Agentic Graph Editor interaction fixes

The in-app graph editor keeps the current dark/neon grid and smooth node styling, but now restores the core direct-manipulation behavior from the standalone graph editor:

- click-drag empty canvas/background to pan the graph world;
- use the mouse wheel over the canvas to zoom in/out around the cursor;
- right-click empty canvas to open a categorized node-type palette instead of creating a generic node;
- use **Open Node Palette** when browser/context-menu behavior is blocked;
- drag nodes by any non-control area of the card;
- drag from output ports to input ports to create edges;
- click an output port and then an input port for click-to-connect workflows;
- right-click nodes for node-specific actions;
- delete edges using edge handles.

The node dropdown, right-click menu, and palette cards now share the same node palette fallback. If the backend catalog is still loading, the editor still exposes standalone-style node contracts such as text/image/audio/video input, bundle/context, model call, supervisor controller, external tool, MCP tool, condition, fanout, join, browser search/open, and output artifact.

## Migration/startup finalization speedups

Migration could previously look stuck after 100% because the expensive part was not always the file copy itself. Large migrations can produce thousands of file-operation records; serializing that full result into the Jobs table and repeatedly polling it through `/api/jobs` made the UI look frozen after visible progress completed.

Changes:

- migration result file details are capped to a bounded sample;
- counters such as `files_total`, `files_omitted`, `files_truncated`, and `files_result_limit` preserve the summary;
- the full plan remains available through migration scan before running;
- `/api/jobs` list polling avoids decoding full `result_json` payloads;
- individual job detail endpoints still provide full result payloads when explicitly opened;
- migration reconciliation records the active tag-profile reconciliation result;
- startup-maintenance progress now has a final compact-result phase so the Dashboard explains what is happening after raw copy/move work finishes.

## Expected result

The graph editor should now feel like an actual graph workspace rather than a static visual editor. Migration should also finish the post-100% stage faster and should be less likely to make the app appear stalled while it serializes or polls large historical job payloads.

# v5.26 External Applications and Spatial Workflows

## Local application handoff

The Gallery now provides an **Open Selected In** selector for Topaz Photo AI, Topaz Gigapixel, Topaz DeNoise, Topaz Sharpen, Topaz Mask, Krita, and ComfyUI. The action calls a synchronous launch endpoint so executable discovery or process-launch failures are shown immediately.

Discovery checks saved paths first, then bounded searches under the user home directory, Desktop, Documents, Downloads, project-adjacent directories, Program Files, and common portable layouts. A deeper scan is opt-in.

Selected images are copied into:

```text
outputs/external_handoffs/<application>/<timestamp>/input
```

A `handoff_manifest.json` records the original media IDs and paths. For ComfyUI, selected copies are additionally placed under its `input/data_curation_tool/<timestamp>` directory.

## Separated spatial tools

The former combined annotation page is retained only as a compatibility alias. The visible workflows are now:

- **Detection & Boxes**: detection-model download/load/status, model bbox preview/save, manual bbox drawing, labels, and transfer of a bbox into the segmentation prompt.
- **Segmentation & Masks**: SAM/SAM-HQ/SAM2/YOLO-seg download/load/status, actual mask overlay preview, manual polygon masks, bbox prompts, multi-mask storage, and Krita mask round-tripping.
- **Pose & 3D**: 2D joints, 3D joints/bones, animation-pose metadata, pose-model hooks, and Blender bridge controls.

Dedicated APIs make the task boundaries explicit for later agentic orchestration:

```text
GET  /api/spatial/detection/models
POST /api/spatial/detection/propose
GET  /api/spatial/detection/state/{media_id}

GET  /api/spatial/segmentation/models
POST /api/spatial/segmentation/propose
GET  /api/spatial/segmentation/state/{media_id}
GET  /api/spatial/mask-preview
```

Detection endpoints strip mask data and save only true boxes. Segmentation endpoints require a real mask file or polygon and refuse bbox-only model results. Neither path generates synthetic fallback annotations.

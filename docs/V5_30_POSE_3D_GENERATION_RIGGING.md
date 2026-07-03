# v5.30 Pose, 3D Generation, Rigging, and Blender Workflow

v5.30 turns pose annotations into visible, editable skeletons and adds a managed 3D asset workflow. It is cumulative with the v5.29 SAM setup and positive/negative point-prompt work.

## Pose model coverage

The **Pose & 3D** tab now lists multiple runtime families rather than only YOLO:

| Family | Included model choices | Output |
|---|---|---|
| Ultralytics | YOLO11 pose sizes and custom YOLO pose checkpoints | Human 2D keypoints |
| MediaPipe Tasks | Pose Landmarker Lite, Full, and Heavy | 33 image landmarks plus 33 world-space landmarks |
| MMPose 2D | RTMPose Human, ViTPose Base, RTMPose WholeBody, RTMPose Animal | Human, whole-body, or animal 2D keypoints |
| MMPose 3D | MotionBERT Human 3D and InterNet Hand 3D | Human3.6M-style human 3D or 3D hand keypoints |
| Custom MMPose | Local config and optional checkpoint | Model-defined 2D or 3D pose |

Install one family from the UI or use:

```bat
install_pose_models.bat ultralytics
install_pose_models.bat mediapipe
install_pose_models.bat mmpose
install_pose_models.bat all
```

```bash
./install_pose_models.sh ultralytics
./install_pose_models.sh mediapipe
./install_pose_models.sh mmpose
./install_pose_models.sh all
```

MMPose dependencies are installed through OpenMIM because MMEngine, MMCV, MMDetection, PyTorch, and CUDA compatibility must be resolved together.

## Visible and editable skeleton topology

Pose records now preserve named joints and explicit bone edges. Supported built-in templates are:

- COCO 17.
- OpenPose 18.
- MediaPipe BlazePose 33.
- Human3.6M 17.
- Custom topology.

The image overlay renders bones before joints so the edge graph remains visible. Editing controls include:

- Move/select joint.
- Add joint.
- Connect two joints with a bone.
- Delete a joint and reindex surviving edges.
- Delete a bone independently.
- Rename a joint.
- Apply or replace a skeleton template.
- Ghost previously saved pose layers for comparison.

Dragging a joint updates every incident bone on each pointer-move event. In 3D mode, the image overlay updates the joint's projected image coordinates and its corresponding world x/y coordinates.

## Interactive 3D skeleton viewer

The 3D viewer renders the same saved joint/edge graph with depth-aware projection. It supports:

- Dragging a joint in the current camera plane.
- Editing the selected joint's z coordinate with a depth slider.
- Orbiting by dragging empty space.
- Wheel zoom.
- Front, side, and reset views.
- Continuous bone redraw while editing.

Saved pose metadata remains compatible with prior pose records:

```json
{
  "keypoints_2d": [],
  "keypoints_3d": [],
  "edges": [[0, 1], [1, 2]],
  "skeleton_template": "h36m17",
  "image_width": 1920,
  "image_height": 1080
}
```

## 3D Generation Studio

The new **3D Studio** tab exposes queued adapters for:

| Provider | Input | Integration |
|---|---|---|
| TripoSR | Image | Official local `run.py` entry point |
| Stable Fast 3D | Image | Official local `run.py` entry point |
| TRELLIS Image-to-3D | Image | Bundled wrapper around the official pipeline and GLB exporter |
| TRELLIS Text-to-3D | Text | Bundled wrapper around the official text-conditioned pipeline |
| Hunyuan3D 2.x | Image | Official local FastAPI `/generate` endpoint |
| Meshy | Image | Official asynchronous Image-to-3D task API |
| Generic REST | Image/text | Configurable JSON request, polling, and result-path adapter |

Use **Validate / Dry-run** before a real execution. The dry run writes an exact command or request plan into the job directory without loading a model or spending cloud API credit.

Generated and imported files are cataloged under:

```text
outputs/3d_assets/generated/
outputs/3d_assets/rigged/
outputs/3d_assets/imported/
```

Supported managed asset formats include GLB, GLTF, FBX, OBJ, PLY, STL, USD variants, USDZ, and VRM.

## Automatic rigging

Two rigging paths are available:

### UniRig

The adapter runs the official three-stage sequence:

1. Skeleton prediction.
2. Skinning-weight prediction.
3. Skeleton/skin/mesh merge and export.

On Windows, the adapter can invoke UniRig through WSL and translates Windows input/output paths with `wslpath` before calling its shell scripts.

### Blender pose-driven rigging

The bundled Blender script:

1. Imports the selected mesh.
2. Loads a saved editable DCT 3D pose, or creates a basic fallback humanoid skeleton when no pose was selected.
3. Creates armature bones from the saved edge graph.
4. Parents the mesh with automatic weights when enabled.
5. Exports GLB/GLTF or FBX.

A generated rig should still be inspected in Blender for bone roll, joint orientation, deformation groups, weight paint, IK constraints, and production animation controls.

## Internal API

The application exposes these local endpoints:

```text
GET  /api/three-d/providers
GET  /api/three-d/assets
GET  /api/three-d/assets/file?path=...
POST /api/three-d/assets/import
POST /api/three-d/generate
POST /api/three-d/rig
POST /api/three-d/open-in-blender

GET  /api/reference/annotations/pose-templates
POST /api/reference/annotations/install-pose-deps

GET  /api/blender/pose/{media_id}
GET  /api/blender/assets
GET  /api/blender/latest-asset
```

Generation and rigging calls return a job ID. Progress, errors, command output, dry-run plans, and resulting asset records are available through the existing Jobs API/UI.

## Blender bridge v0.3

Install `integrations/blender_dataset_bridge.zip` through Blender's Add-ons interface. The bridge can:

- Fetch a DCT pose and create an armature.
- Send the selected Blender armature pose back to DCT.
- Import a specified or latest managed DCT asset.
- Queue 3D generation.
- Queue automatic rigging.
- Open results for additional Blender editing.

The standalone scripts used by the backend are in `integrations/blender_scripts/`.

## Validation boundary

The application adapters, API contracts, dry-run plans, pose normalization, editable topology, managed asset library, and Blender bridge package are testable without large model weights. Actual inference still requires each provider's official repository, checkpoints, compatible CUDA/PyTorch environment, and—where applicable—an API key. Large 3D checkpoints and Blender GPU jobs were not executed as part of the lightweight repository regression suite.

# v5.32 Metadata, ComfyUI Bridge, 3D Viewport, Blender, and Animation Dataset Workflows

## Metadata extraction capability retained under neutral names

The application includes the powerful metadata extraction capabilities from the uploaded metadata toolkit, but the old source node prefixes and node names are intentionally not exposed in the DCT user interface, API routes, docs, workflow names, or bundled ComfyUI node package.

Supported extraction surfaces include generated images, videos, LoRA safetensors, A1111-style PNG parameters, ComfyUI prompt/workflow metadata, NovelAI-style metadata, Fooocus/Civitai/Invoke-style JSON comments, EXIF/PIL fields, WebP metadata exposed by Pillow, and ffprobe-backed video metadata. The Media Tools tab can inspect nested JSON schemas, select fields, concatenate them in user-defined order, and apply derived tags/captions.

## ComfyUI bridge

The optional custom-node package is:

```text
integrations/data_curation_tool_comfyui_nodes.zip
```

Install it into:

```text
ComfyUI/custom_nodes/data_curation_tool_comfyui_nodes/
```

The bridge uses endpoints under:

```text
/api/comfy
```

Main bridge workflows:

- Create a DCT media handoff manifest for selected media.
- Load a handoff manifest inside ComfyUI.
- Send ComfyUI output media/masks/metadata back to DCT.
- Extract metadata from ComfyUI outputs through DCT's metadata service.
- Send prompt strings, captions, tag strings, LoRA metadata, and JSON payloads back into DCT.

## 3D viewport

The 3D Viewport tab can load:

```text
.obj
.blend
.fbx
.glb/.gltf
.ply
.stl
.usd/.usda/.usdc/.usdz
```

OBJ files can be parsed directly. Other formats are converted to a DCT viewport JSON payload through Blender background mode. The viewer exposes:

- Shaded solid mode.
- Wireframe / topology mode.
- UV topology mode.
- Normal-vector mode.
- Rig-bones mode.
- Rendered/material preview mode.

The viewport payload preserves mesh vertices, faces, normals, UV triangles, material names, armature bones, bone labels, and bone groups. This lets users inspect generated inputs/outputs, rigging results, and custom armatures without leaving the tool.

## Custom non-humanoid skeletons

Pose & 3D now includes a Custom Skeleton Templates section. Users can define arbitrary node names and edge records:

```text
from,to,label,group
root,tail_01,tail base,tail
tail_01,tail_02,tail mid,tail
root,left_wing_01,left wing root,wing
```

These templates are persisted to:

```text
runtime/custom_skeleton_templates.json
```

They are included in the normal pose template selector and exported through annotation metadata for Blender and training datasets.

## Extended Blender support

The Blender bridge is now v0.4 and adds:

- Send selected armature pose back to DCT.
- Fetch a DCT pose as a Blender armature.
- Save a selected Blender armature as a DCT custom skeleton template.
- Import the latest DCT asset.
- Prepare a DCT 3D viewport payload from a Blender asset.
- Queue DCT-side 3D generation and rigging jobs.

## Additional model and workflow catalog rows

The catalog includes additional local/provider workflow rows for:

- InstantMesh.
- Wonder3D / multi-view reconstruction.
- Zero123++ multi-view prior.
- SV3D / Stable Video 3D-style multi-view workflows.
- Hunyuan3D 2.5-style local API workflows.
- SPAR3D-style high-fidelity reconstruction contracts.
- Rodin/Hyper3D API workflows.
- Mesh topology/UV/normal inspector.
- Non-humanoid custom skeleton contracts.
- Animation concept dataset tools.

Some are runnable through existing generic provider contracts, while others are explicit catalog/training-dataset contracts until their exact runtime adapters are added per provider.

## Training data for animation concepts and movements

Use the Pose & 3D tab to create or import 2D/3D skeletons, add edge labels/groups, and save per-frame pose annotations. Use Media Tools to extract frames from videos, then annotate sequences as animation-pose records. Export manifests should include:

- media_id or frame path
- frame index / timestamp
- skeleton template key
- keypoints_2d
- keypoints_3d
- labeled edges
- edge groups
- subject/object identity label
- movement/action concept label
- source model/manual provenance
- confidence and revision history

These records can be consumed by future 2D-to-3D, image-to-rig, motion retargeting, and character animation training pipelines.

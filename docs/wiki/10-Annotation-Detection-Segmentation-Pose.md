# Detection, Segmentation, Pose, and 3D

<!-- DCT_VISUAL_START -->
![Detection, segmentation, pose, and 3D visual guide](assets/images/annotation_detection_segmentation_pose_3d.png)
<!-- DCT_VISUAL_END -->


The spatial annotation tabs help create, edit, and manage structured labels beyond plain tags.

## Detection & Boxes

Use this tab for bounding boxes.

Common tasks:

- Run detection models.
- Draw boxes manually.
- Edit box coordinates.
- Label each box.
- Promote model previews into persistent annotations.
- Export detection training data.

## Segmentation & Masks

Use this tab for masks and polygons.

Common tasks:

- Run segmentation models.
- Use SAM/SAM-HQ-style prompts.
- Add positive/negative points.
- Draw manual masks.
- Combine masks.
- Edit, hide, lock, duplicate, and rename layers.
- Export masks for downstream training.

## Pose & 3D

Use this tab for 2D and 3D pose workflows.

Common tasks:

- Run pose detectors.
- Edit joints/keypoints.
- Visualize connected bones.
- Create or adjust pose labels.
- Use 3D pose helpers when configured.

## 3D Studio and 3D Viewport

Use these tabs for 3D generation, rigging, viewing, and asset workflows when optional integrations are installed.

Potential workflows:

- Generate or import 3D assets.
- Preview GLB/FBX/OBJ-style outputs.
- Bridge with Blender or other tools.
- Use pose or rigging adapters.

## Annotation Editor

Some builds include a general annotation editor or annotation-related controls across the spatial tabs. Use it for manual bbox/polygon/mask records and training-set bridge workflows.

## Installing model dependencies

Optional scripts:

Windows:

```bat
install_annotation_models.bat
install_sam_runtime.bat
install_pose_models.bat
```

Linux:

```bash
./install_annotation_models.sh
./install_sam_runtime.sh
./install_pose_models.sh
```

## Model compatibility

Different model families output different spatial data:

| Model type | Expected output |
| --- | --- |
| Detector | Boxes and labels. |
| Segmenter | Masks/polygons and labels. |
| Pose model | Keypoints/joints and skeletons. |
| Multitask model | One or more of boxes, captions, OCR, or other structured outputs. |

Do not expect a mask-only model to produce boxes unless an adapter explicitly supports it.

## Best practices

- Keep model preview and saved annotation layers separate.
- Promote only the layers you actually want to keep.
- Label every object/mask if you may train later.
- Avoid overwriting manual annotations with model previews.
- Use the Jobs tab for errors and full logs.

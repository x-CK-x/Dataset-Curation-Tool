"""Blender background script: import mesh, create pose-driven armature, bind, export.

Invocation:
  blender --background --python dct_auto_rig.py -- \
    --input model.glb --output rigged.glb --pose-json pose.json --automatic-weights
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args_after_double_dash() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pose-json", default="")
    parser.add_argument("--automatic-weights", action="store_true")
    parser.add_argument("--armature-name", default="DCT_Armature")
    return parser.parse_args(args_after_double_dash())


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_asset(path: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    ext = path.suffix.lower()
    if ext in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    elif ext == ".obj":
        if hasattr(bpy.ops.wm, "obj_import"):
            bpy.ops.wm.obj_import(filepath=str(path))
        else:
            bpy.ops.import_scene.obj(filepath=str(path))
    elif ext == ".ply":
        if hasattr(bpy.ops.wm, "ply_import"):
            bpy.ops.wm.ply_import(filepath=str(path))
        else:
            bpy.ops.import_mesh.ply(filepath=str(path))
    elif ext == ".stl":
        if hasattr(bpy.ops.wm, "stl_import"):
            bpy.ops.wm.stl_import(filepath=str(path))
        else:
            bpy.ops.import_mesh.stl(filepath=str(path))
    elif ext in {".usd", ".usda", ".usdc", ".usdz"}:
        bpy.ops.wm.usd_import(filepath=str(path))
    else:
        raise ValueError(f"Unsupported input format: {ext}")
    created = [obj for obj in bpy.data.objects if obj not in before]
    return [obj for obj in created if obj.type == "MESH"]


def mesh_bounds(meshes: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    coords: list[Vector] = []
    for obj in meshes:
        coords.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not coords:
        return Vector((-1, -1, 0)), Vector((1, 1, 2))
    return Vector(tuple(min(v[i] for v in coords) for i in range(3))), Vector(tuple(max(v[i] for v in coords) for i in range(3)))


def load_pose(path: str) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("metadata"), dict):
        data = data["metadata"]
    return data if isinstance(data, dict) else {}


def fallback_humanoid(bounds_min: Vector, bounds_max: Vector) -> tuple[list[dict], list[list]]:
    center = (bounds_min + bounds_max) * 0.5
    size = bounds_max - bounds_min
    h = max(size.z, 1e-3)
    w = max(size.x, h * 0.25)
    y = center.y
    points = [
        {"name": "pelvis", "x": center.x, "y": y, "z": bounds_min.z + h * 0.48},
        {"name": "spine", "x": center.x, "y": y, "z": bounds_min.z + h * 0.65},
        {"name": "neck", "x": center.x, "y": y, "z": bounds_min.z + h * 0.82},
        {"name": "head", "x": center.x, "y": y, "z": bounds_min.z + h * 0.96},
        {"name": "left_shoulder", "x": center.x - w * 0.28, "y": y, "z": bounds_min.z + h * 0.79},
        {"name": "left_elbow", "x": center.x - w * 0.55, "y": y, "z": bounds_min.z + h * 0.65},
        {"name": "left_wrist", "x": center.x - w * 0.78, "y": y, "z": bounds_min.z + h * 0.54},
        {"name": "right_shoulder", "x": center.x + w * 0.28, "y": y, "z": bounds_min.z + h * 0.79},
        {"name": "right_elbow", "x": center.x + w * 0.55, "y": y, "z": bounds_min.z + h * 0.65},
        {"name": "right_wrist", "x": center.x + w * 0.78, "y": y, "z": bounds_min.z + h * 0.54},
        {"name": "left_hip", "x": center.x - w * 0.16, "y": y, "z": bounds_min.z + h * 0.46},
        {"name": "left_knee", "x": center.x - w * 0.18, "y": y, "z": bounds_min.z + h * 0.25},
        {"name": "left_ankle", "x": center.x - w * 0.18, "y": y, "z": bounds_min.z + h * 0.04},
        {"name": "right_hip", "x": center.x + w * 0.16, "y": y, "z": bounds_min.z + h * 0.46},
        {"name": "right_knee", "x": center.x + w * 0.18, "y": y, "z": bounds_min.z + h * 0.25},
        {"name": "right_ankle", "x": center.x + w * 0.18, "y": y, "z": bounds_min.z + h * 0.04},
    ]
    edges = [[0, 1], [1, 2], [2, 3], [2, 4], [4, 5], [5, 6], [2, 7], [7, 8], [8, 9], [0, 10], [10, 11], [11, 12], [0, 13], [13, 14], [14, 15]]
    return points, edges


def normalized_points(raw: list[dict], bounds_min: Vector, bounds_max: Vector, pose: dict) -> list[dict]:
    if not raw:
        return []
    coords = [(float(p.get("x", 0)), float(p.get("y", 0)), float(p.get("z", p.get("depth", 0)))) for p in raw]
    space = str(pose.get("coordinate_space") or "").lower()
    image_w = float(pose.get("image_width") or pose.get("width") or 0)
    image_h = float(pose.get("image_height") or pose.get("height") or 0)
    max_abs = max((abs(v) for c in coords for v in c), default=0)
    normalized = space in {"normalized", "image_normalized"} or (max_abs <= 2.5 and space not in {"world", "blender"})
    result: list[dict] = []
    size = bounds_max - bounds_min
    center = (bounds_min + bounds_max) * 0.5
    for i, point in enumerate(raw):
        x, y, z = coords[i]
        image_x = point.get("image_x")
        image_y = point.get("image_y")
        has_image_projection = image_w > 0 and image_h > 0 and image_x is not None and image_y is not None
        if has_image_projection:
            # DCT keeps world coordinates and the corresponding image projection
            # together.  Use image_x/image_y to align the armature with the mesh
            # silhouette; x/y here are world values and must not be divided by
            # image dimensions.
            bx = bounds_min.x + (float(image_x) / image_w) * max(size.x, 1e-3)
            bz = bounds_max.z - (float(image_y) / image_h) * max(size.z, 1e-3)
            by = center.y + z * max(size.y, max(size.x, size.z) * 0.1)
        elif normalized:
            # DCT image/world pose convention: x right, y up or image-down, z depth.
            bx = center.x + x * max(size.x, size.z * 0.35)
            bz = center.z + y * max(size.z, 1e-3)
            by = center.y + z * max(size.y, size.z * 0.25)
        else:
            # Treat as Blender/world coordinates; image-space projection may be supplied separately.
            bx, by, bz = x, z, y
        result.append({"name": str(point.get("name") or point.get("label") or f"joint_{i}"), "co": Vector((bx, by, bz))})
    return result


def edge_indices(edge: list, points: list[dict]) -> tuple[int, int] | None:
    if not isinstance(edge, (list, tuple)) or len(edge) < 2:
        return None
    lookup = {p["name"]: i for i, p in enumerate(points)}
    out = []
    for value in edge[:2]:
        if isinstance(value, int):
            out.append(value)
        elif isinstance(value, str) and value.isdigit():
            out.append(int(value))
        else:
            out.append(lookup.get(str(value), -1))
    if min(out) < 0 or max(out) >= len(points) or out[0] == out[1]:
        return None
    return out[0], out[1]


def create_armature(name: str, points: list[dict], edges: list[list]) -> bpy.types.Object:
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    incoming: dict[int, bpy.types.EditBone] = {}
    valid_edges = [pair for edge in edges if (pair := edge_indices(edge, points))]
    if not valid_edges and len(points) > 1:
        valid_edges = [(i - 1, i) for i in range(1, len(points))]
    for index, (a, b) in enumerate(valid_edges):
        head, tail = points[a]["co"], points[b]["co"]
        if (tail - head).length < 1e-5:
            tail = head + Vector((0, 0, 0.02))
        bone = arm_data.edit_bones.new(f"{points[a]['name']}__{points[b]['name']}")
        bone.head = head
        bone.tail = tail
        bone.use_connect = False
        if a in incoming:
            bone.parent = incoming[a]
        incoming[b] = bone
    if not valid_edges and points:
        bone = arm_data.edit_bones.new(points[0]["name"])
        bone.head = points[0]["co"]
        bone.tail = points[0]["co"] + Vector((0, 0, 0.1))
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def bind(meshes: list[bpy.types.Object], armature: bpy.types.Object, automatic: bool) -> None:
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in meshes:
        obj.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO" if automatic else "ARMATURE_NAME")
    except Exception as exc:
        print(f"Automatic weights failed ({exc}); falling back to armature parent without generated weights.")
        for obj in meshes:
            obj.parent = armature
            modifier = obj.modifiers.new(name="DCT_Armature", type="ARMATURE")
            modifier.object = armature


def export_asset(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    if ext in {".glb", ".gltf"}:
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB" if ext == ".glb" else "GLTF_SEPARATE", export_skins=True, export_animations=True)
    elif ext == ".fbx":
        bpy.ops.export_scene.fbx(filepath=str(path), add_leaf_bones=False, use_armature_deform_only=True)
    else:
        raise ValueError("Output must be .glb, .gltf, or .fbx")


def main() -> None:
    args = parse_args()
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    clear_scene()
    meshes = import_asset(source)
    if not meshes:
        raise RuntimeError("The imported asset did not contain a mesh object.")
    bounds_min, bounds_max = mesh_bounds(meshes)
    pose = load_pose(args.pose_json)
    raw = pose.get("keypoints_3d") or pose.get("joints") or []
    edges = pose.get("edges") or pose.get("bones") or []
    points = normalized_points(raw, bounds_min, bounds_max, pose)
    if not points:
        raw, edges = fallback_humanoid(bounds_min, bounds_max)
        points = [{"name": p["name"], "co": Vector((p["x"], p["y"], p["z"]))} for p in raw]
    armature = create_armature(args.armature_name, points, edges)
    bind(meshes, armature, args.automatic_weights)
    export_asset(output)
    print(json.dumps({"output": str(output), "mesh_count": len(meshes), "joint_count": len(points), "edge_count": len(edges)}))


if __name__ == "__main__":
    main()

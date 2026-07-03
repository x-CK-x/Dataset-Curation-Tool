"""Blender helper: export a compact JSON payload for the DCT browser 3D viewport."""
from __future__ import annotations
import argparse, json, math, os, sys
from pathlib import Path

import bpy
from mathutils import Vector


def import_or_open(path: Path):
    ext = path.suffix.lower()
    if ext == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
        return
    bpy.ops.object.delete()
    if ext in {".gltf", ".glb"}:
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path))
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path)) if hasattr(bpy.ops.wm, "obj_import") else bpy.ops.import_scene.obj(filepath=str(path))
    elif ext == ".ply":
        bpy.ops.wm.ply_import(filepath=str(path)) if hasattr(bpy.ops.wm, "ply_import") else bpy.ops.import_mesh.ply(filepath=str(path))
    elif ext == ".stl":
        bpy.ops.wm.stl_import(filepath=str(path)) if hasattr(bpy.ops.wm, "stl_import") else bpy.ops.import_mesh.stl(filepath=str(path))
    elif ext in {".usd", ".usda", ".usdc", ".usdz"}:
        bpy.ops.wm.usd_import(filepath=str(path))
    elif ext == ".dae":
        bpy.ops.wm.collada_import(filepath=str(path))
    elif ext == ".abc":
        bpy.ops.wm.alembic_import(filepath=str(path))
    elif ext == ".bvh":
        bpy.ops.import_anim.bvh(filepath=str(path))
    elif ext == ".x3d":
        bpy.ops.import_scene.x3d(filepath=str(path))
    else:
        raise RuntimeError(f"Unsupported input extension for Blender import: {ext}")


def mesh_payload(obj, max_vertices=200000, max_faces=200000):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    # Blender 5 removed an older explicit normal recalculation API. Evaluated meshes expose
    # polygon/loop-triangle normals after update/calc_loop_triangles(). Keep
    # this exporter compatible with Blender 3.x/4.x/5.x by avoiding the
    # removed method and falling back to mesh.update() when available.
    try:
        mesh.update(calc_edges=True, calc_edges_loose=True)
    except TypeError:
        try:
            mesh.update()
        except Exception:
            pass
    except Exception:
        pass
    mesh.calc_loop_triangles()
    vertices = []
    world = obj.matrix_world
    for v in mesh.vertices[:max_vertices]:
        co = world @ v.co
        vertices.append([round(co.x, 6), round(co.y, 6), round(co.z, 6)])
    faces = []
    normals = []
    uvs = []
    uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
    for tri in mesh.loop_triangles[:max_faces]:
        if any(i >= len(vertices) for i in tri.vertices):
            continue
        faces.append([int(i) for i in tri.vertices])
        n = tri.normal
        normals.append([round(n.x, 6), round(n.y, 6), round(n.z, 6)])
        if uv_layer:
            uv_face = []
            for loop_index in tri.loops:
                uv = uv_layer[loop_index].uv
                uv_face.append([round(float(uv.x), 6), round(float(uv.y), 6)])
            uvs.append(uv_face)
    mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
    try:
        eval_obj.to_mesh_clear()
    except Exception:
        pass
    return {"name": obj.name, "vertices": vertices, "faces": faces, "normals": normals, "uvs": uvs, "materials": mat_names}


def armature_payload(obj):
    bones = []
    edges = []
    world = obj.matrix_world
    for idx, bone in enumerate(obj.data.bones):
        head = world @ bone.head_local
        tail = world @ bone.tail_local
        bones.append({
            "index": idx,
            "name": bone.name,
            "group": bone.name.split(".")[0].split("_")[0],
            "head": [round(head.x, 6), round(head.y, 6), round(head.z, 6)],
            "tail": [round(tail.x, 6), round(tail.y, 6), round(tail.z, 6)],
            "parent": bone.parent.name if bone.parent else "",
        })
    name_to_idx = {b["name"]: b["index"] for b in bones}
    for b in bones:
        if b["parent"] in name_to_idx:
            edges.append({"from": name_to_idx[b["parent"]], "to": b["index"], "label": b["name"], "group": b["group"]})
    return {"name": obj.name, "bones": bones, "edges": edges}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--render-preview", default="")
    parser.add_argument("--max-vertices", type=int, default=200000)
    parser.add_argument("--max-faces", type=int, default=200000)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    source = Path(args.input).expanduser().resolve()
    import_or_open(source)
    meshes = []
    armatures = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            meshes.append(mesh_payload(obj, args.max_vertices, args.max_faces))
        elif obj.type == "ARMATURE":
            armatures.append(armature_payload(obj))
    payload = {
        "source_path": str(source),
        "source_format": source.suffix.lower().lstrip('.'),
        "exported_at": __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        "coordinate_system": "Blender world coordinates",
        "meshes": meshes,
        "armatures": armatures,
        "objects": [{"name": o.name, "type": o.type} for o in bpy.context.scene.objects],
        "truncated": any(len(m.get('vertices', [])) >= args.max_vertices or len(m.get('faces', [])) >= args.max_faces for m in meshes),
    }
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == "__main__":
    main()

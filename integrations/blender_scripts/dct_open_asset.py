"""Open/import a DCT-managed 3D asset into the current Blender scene."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import bpy


def parse_args():
    values = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(); p.add_argument('--input', required=True); return p.parse_args(values)


def main():
    path = Path(parse_args().input).expanduser().resolve(); ext = path.suffix.lower()
    if ext in {'.glb','.gltf'}: bpy.ops.import_scene.gltf(filepath=str(path))
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=str(path))
    elif ext == '.obj':
        (bpy.ops.wm.obj_import if hasattr(bpy.ops.wm, 'obj_import') else bpy.ops.import_scene.obj)(filepath=str(path))
    elif ext == '.ply':
        (bpy.ops.wm.ply_import if hasattr(bpy.ops.wm, 'ply_import') else bpy.ops.import_mesh.ply)(filepath=str(path))
    elif ext == '.stl':
        (bpy.ops.wm.stl_import if hasattr(bpy.ops.wm, 'stl_import') else bpy.ops.import_mesh.stl)(filepath=str(path))
    elif ext in {'.usd','.usda','.usdc','.usdz'}: bpy.ops.wm.usd_import(filepath=str(path))
    else: raise ValueError(f'Unsupported format: {ext}')

if __name__ == '__main__': main()

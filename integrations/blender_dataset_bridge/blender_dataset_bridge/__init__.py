bl_info = {
    "name": "Data Curation Tool Blender Bridge",
    "author": "Data Curation Tool",
    "version": (0, 4, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > DCT Bridge",
    "description": "Round-trip DCT poses, import generated 3D assets, and queue generation/rigging jobs.",
    "category": "Import-Export",
}

import json
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import bpy
from mathutils import Vector


def request_json(base_url, route, method='GET', payload=None, timeout=60):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = urllib.request.Request(
        base_url.rstrip('/') + route,
        data=data,
        headers={'Content-Type': 'application/json'} if data is not None else {},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8', 'ignore') or '{}')


def armature_pose_payload(obj):
    keypoints = []
    edges = []
    if not obj or obj.type != 'ARMATURE':
        return keypoints, edges
    point_by_coordinate = {}

    def point(name, value):
        key = tuple(round(float(v), 7) for v in value)
        if key in point_by_coordinate:
            return point_by_coordinate[key]
        final_name = name
        names = {item['name'] for item in keypoints}
        suffix = 2
        while final_name in names:
            final_name = f'{name}_{suffix}'; suffix += 1
        point_by_coordinate[key] = final_name
        keypoints.append({'name': final_name, 'x': float(value.x), 'y': float(value.y), 'z': float(value.z)})
        return final_name

    for bone in obj.pose.bones:
        head = obj.matrix_world @ bone.head
        tail = obj.matrix_world @ bone.tail
        head_name = point(f'{bone.name}:head', head)
        tail_name = point(f'{bone.name}:tail', tail)
        edges.append([head_name, tail_name])
    return keypoints, edges


def edge_pair(edge, points):
    lookup = {str(point.get('name', i)): i for i, point in enumerate(points)}
    if not isinstance(edge, (list, tuple)) or len(edge) < 2:
        return None
    values = []
    for value in edge[:2]:
        if isinstance(value, int): values.append(value)
        elif isinstance(value, str) and value.isdigit(): values.append(int(value))
        else: values.append(lookup.get(str(value), -1))
    return tuple(values) if min(values) >= 0 and max(values) < len(points) and values[0] != values[1] else None


def create_armature_from_pose(payload, name='DCT_Imported_Pose'):
    points = payload.get('keypoints_3d') or payload.get('metadata', {}).get('keypoints_3d') or []
    edges = payload.get('edges') or payload.get('metadata', {}).get('edges') or []
    if not points:
        raise ValueError('The selected DCT annotation has no 3D keypoints.')
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    incoming = {}
    valid = [pair for edge in edges if (pair := edge_pair(edge, points))]
    if not valid and len(points) > 1:
        valid = [(i - 1, i) for i in range(1, len(points))]
    for a, b in valid:
        pa, pb = points[a], points[b]
        head = Vector((float(pa.get('x', 0)), float(pa.get('y', 0)), float(pa.get('z', 0))))
        tail = Vector((float(pb.get('x', 0)), float(pb.get('y', 0)), float(pb.get('z', 0))))
        if (tail - head).length < 1e-6:
            tail.z += 0.01
        bone = arm_data.edit_bones.new(f"{pa.get('name', a)}__{pb.get('name', b)}")
        bone.head, bone.tail = head, tail
        if a in incoming:
            bone.parent = incoming[a]
        incoming[b] = bone
    if not valid:
        point = points[0]
        bone = arm_data.edit_bones.new(str(point.get('name') or 'joint'))
        bone.head = Vector((float(point.get('x', 0)), float(point.get('y', 0)), float(point.get('z', 0))))
        bone.tail = bone.head + Vector((0, 0, 0.1))
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj


def import_asset(path):
    path = Path(path).expanduser().resolve(); ext = path.suffix.lower()
    if ext in {'.glb', '.gltf'}: bpy.ops.import_scene.gltf(filepath=str(path))
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=str(path))
    elif ext == '.obj':
        (bpy.ops.wm.obj_import if hasattr(bpy.ops.wm, 'obj_import') else bpy.ops.import_scene.obj)(filepath=str(path))
    elif ext == '.ply':
        (bpy.ops.wm.ply_import if hasattr(bpy.ops.wm, 'ply_import') else bpy.ops.import_mesh.ply)(filepath=str(path))
    elif ext == '.stl':
        (bpy.ops.wm.stl_import if hasattr(bpy.ops.wm, 'stl_import') else bpy.ops.import_mesh.stl)(filepath=str(path))
    elif ext in {'.usd', '.usda', '.usdc', '.usdz'}: bpy.ops.wm.usd_import(filepath=str(path))
    else: raise ValueError(f'Unsupported asset format: {ext}')


class DCTBridgeSettings(bpy.types.PropertyGroup):
    base_url: bpy.props.StringProperty(name='App URL', default='http://127.0.0.1:7865')
    media_id: bpy.props.IntProperty(name='Media ID', default=0, min=0)
    annotation_id: bpy.props.IntProperty(name='Annotation ID (optional)', default=0, min=0)
    label: bpy.props.StringProperty(name='Label', default='pose3d')
    target_name: bpy.props.StringProperty(name='Target', default='')
    asset_path: bpy.props.StringProperty(name='3D Asset Path', subtype='FILE_PATH', default='')
    generation_provider: bpy.props.EnumProperty(name='Generator', items=[
        ('triposr_local', 'TripoSR local', ''), ('stable_fast_3d_local', 'Stable Fast 3D local', ''),
        ('trellis_image_local', 'TRELLIS image local', ''), ('trellis_text_local', 'TRELLIS text local', ''), ('hunyuan3d_local_api', 'Hunyuan3D local API', ''),
        ('meshy_image_api', 'Meshy API', ''), ('generic_image_to_3d_api', 'Generic REST API', '')])
    source_image_path: bpy.props.StringProperty(name='Source Image', subtype='FILE_PATH', default='')
    prompt: bpy.props.StringProperty(name='Prompt', default='')
    repo_path: bpy.props.StringProperty(name='Generation Provider Repo', subtype='DIR_PATH', default='')
    rig_repo_path: bpy.props.StringProperty(name='Rigging Provider Repo', subtype='DIR_PATH', default='')
    shell_executable: bpy.props.StringProperty(name='Rig Shell / WSL Executable', default='')
    endpoint: bpy.props.StringProperty(name='API Endpoint', default='')
    api_key: bpy.props.StringProperty(name='API Key', subtype='PASSWORD', default='')
    rig_provider: bpy.props.EnumProperty(name='Rigger', items=[('unirig_local', 'UniRig local', ''), ('blender_pose_rig', 'Blender pose-driven rig', '')])
    blender_executable: bpy.props.StringProperty(name='Blender Executable', subtype='FILE_PATH', default='')


class DCT_OT_send_pose(bpy.types.Operator):
    bl_idname = 'dct_bridge.send_pose'; bl_label = 'Send Selected Armature Pose'
    def execute(self, context):
        s = context.scene.dct_bridge_settings; obj = context.object
        if not obj or obj.type != 'ARMATURE': self.report({'ERROR'}, 'Select an Armature object first.'); return {'CANCELLED'}
        if s.media_id <= 0: self.report({'ERROR'}, 'Set Media ID first.'); return {'CANCELLED'}
        keypoints, edges = armature_pose_payload(obj)
        payload = {'media_id': s.media_id, 'label': s.label or 'pose3d', 'target_name': s.target_name, 'rig_name': obj.name, 'keypoints_3d': keypoints, 'edges': edges}
        try: result = request_json(s.base_url, '/api/blender/import-pose', 'POST', payload)
        except Exception as exc: self.report({'ERROR'}, f'Bridge request failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f"Saved annotation {result.get('annotation_id') or result.get('id')}: {len(keypoints)} joints / {len(edges)} bones")
        return {'FINISHED'}


class DCT_OT_fetch_pose(bpy.types.Operator):
    bl_idname = 'dct_bridge.fetch_pose'; bl_label = 'Create Armature from DCT Pose'
    def execute(self, context):
        s = context.scene.dct_bridge_settings
        if s.media_id <= 0: self.report({'ERROR'}, 'Set Media ID first.'); return {'CANCELLED'}
        route = f'/api/blender/pose/{s.media_id}'
        if s.annotation_id: route += '?' + urllib.parse.urlencode({'annotation_id': s.annotation_id})
        try:
            payload = request_json(s.base_url, route)
            armature = create_armature_from_pose(payload, f"DCT_Pose_{payload.get('annotation_id') or s.media_id}")
        except Exception as exc: self.report({'ERROR'}, f'Pose import failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f'Created armature {armature.name}')
        return {'FINISHED'}


class DCT_OT_import_asset(bpy.types.Operator):
    bl_idname = 'dct_bridge.import_asset'; bl_label = 'Import 3D Asset Path'
    def execute(self, context):
        s = context.scene.dct_bridge_settings
        try: import_asset(s.asset_path)
        except Exception as exc: self.report({'ERROR'}, str(exc)); return {'CANCELLED'}
        self.report({'INFO'}, f'Imported {s.asset_path}'); return {'FINISHED'}


class DCT_OT_import_latest_asset(bpy.types.Operator):
    bl_idname = 'dct_bridge.import_latest_asset'; bl_label = 'Import Latest DCT Asset'
    def execute(self, context):
        s = context.scene.dct_bridge_settings
        try:
            asset = request_json(s.base_url, '/api/blender/latest-asset')
            path = asset.get('path')
            if not path or not Path(path).exists():
                url = s.base_url.rstrip('/') + (asset.get('download_url') or '')
                suffix = '.' + str(asset.get('format') or 'glb')
                temp = Path(tempfile.gettempdir()) / f'dct_latest_asset{suffix}'
                urllib.request.urlretrieve(url, temp); path = str(temp)
            import_asset(path); s.asset_path = path
        except Exception as exc: self.report({'ERROR'}, f'Latest asset import failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f"Imported {asset.get('name') or path}"); return {'FINISHED'}


class DCT_OT_queue_generation(bpy.types.Operator):
    bl_idname = 'dct_bridge.queue_generation'; bl_label = 'Queue 3D Generation in DCT'
    def execute(self, context):
        s = context.scene.dct_bridge_settings
        payload = {'provider': s.generation_provider, 'input_path': s.source_image_path, 'prompt': s.prompt, 'repo_path': s.repo_path, 'endpoint': s.endpoint, 'api_key': s.api_key, 'output_format': 'glb', 'options': {}}
        try: result = request_json(s.base_url, '/api/three-d/generate', 'POST', payload)
        except Exception as exc: self.report({'ERROR'}, f'Generation queue failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f"Queued DCT generation job {result.get('job_id')}"); return {'FINISHED'}


class DCT_OT_queue_rig(bpy.types.Operator):
    bl_idname = 'dct_bridge.queue_rig'; bl_label = 'Queue Automatic Rigging in DCT'
    def execute(self, context):
        s = context.scene.dct_bridge_settings
        payload = {'provider': s.rig_provider, 'asset_path': s.asset_path, 'repo_path': s.rig_repo_path, 'shell_executable': s.shell_executable, 'blender_executable': s.blender_executable, 'media_id': s.media_id or None, 'annotation_id': s.annotation_id or None, 'output_format': 'glb', 'automatic_weights': True, 'options': {}}
        try: result = request_json(s.base_url, '/api/three-d/rig', 'POST', payload)
        except Exception as exc: self.report({'ERROR'}, f'Rig queue failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f"Queued DCT rigging job {result.get('job_id')}"); return {'FINISHED'}



class DCT_OT_send_custom_skeleton(bpy.types.Operator):
    bl_idname = 'dct_bridge.send_custom_skeleton'; bl_label = 'Save Selected Armature as Custom Skeleton Template'
    def execute(self, context):
        s = context.scene.dct_bridge_settings; obj = context.object
        if not obj or obj.type != 'ARMATURE': self.report({'ERROR'}, 'Select an Armature object first.'); return {'CANCELLED'}
        points, raw_edges = armature_pose_payload(obj)
        names = [p.get('name') for p in points]
        edges = []
        lookup = {name: i for i, name in enumerate(names)}
        for edge in raw_edges:
            if len(edge) < 2: continue
            a, b = edge[0], edge[1]
            edges.append({'from': lookup.get(a, a), 'to': lookup.get(b, b), 'label': f'{a}->{b}', 'group': str(a).split(':')[0].split('_')[0] or 'rig'})
        payload = {'key': obj.name.lower().replace(' ', '_'), 'label': obj.name, 'dimension': '3d', 'names': names, 'edges': edges, 'groups': [{'key': 'rig', 'label': 'Rig'}], 'notes': 'Imported from Blender armature'}
        try: result = request_json(s.base_url, '/api/reference/annotations/custom-skeletons', 'POST', payload)
        except Exception as exc: self.report({'ERROR'}, f'Custom skeleton save failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f"Saved custom skeleton {result.get('template', {}).get('key', obj.name)} with {len(names)} joints")
        return {'FINISHED'}

class DCT_OT_prepare_viewport_payload(bpy.types.Operator):
    bl_idname = 'dct_bridge.prepare_viewport_payload'; bl_label = 'Prepare DCT 3D Viewport Payload'
    def execute(self, context):
        s = context.scene.dct_bridge_settings
        asset = s.asset_path or bpy.data.filepath
        if not asset: self.report({'ERROR'}, 'Set Asset Path or save the current .blend first.'); return {'CANCELLED'}
        payload = {'asset_path': asset, 'blender_executable': s.blender_executable or '', 'include_payload': False, 'force_blender': True}
        try: result = request_json(s.base_url, '/api/three-d/viewport/prepare', 'POST', payload)
        except Exception as exc: self.report({'ERROR'}, f'Viewport payload export failed: {exc}'); return {'CANCELLED'}
        self.report({'INFO'}, f"Prepared viewport payload: {result.get('mesh_count')} mesh(es), {result.get('armature_count')} armature(s)")
        return {'FINISHED'}

class DCT_PT_bridge_panel(bpy.types.Panel):
    bl_label = 'DCT Bridge'; bl_idname = 'DCT_PT_bridge_panel'; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'DCT Bridge'
    def draw(self, context):
        l = self.layout; s = context.scene.dct_bridge_settings
        l.prop(s, 'base_url'); l.prop(s, 'media_id'); l.prop(s, 'annotation_id')
        pose = l.box(); pose.label(text='Editable Pose Round-trip'); pose.prop(s, 'label'); pose.prop(s, 'target_name'); pose.operator('dct_bridge.fetch_pose'); pose.operator('dct_bridge.send_pose'); pose.operator('dct_bridge.send_custom_skeleton')
        assets = l.box(); assets.label(text='Generated / Rigged Assets'); assets.prop(s, 'asset_path'); assets.operator('dct_bridge.import_asset'); assets.operator('dct_bridge.import_latest_asset'); assets.operator('dct_bridge.prepare_viewport_payload')
        gen = l.box(); gen.label(text='3D Generation'); gen.prop(s, 'generation_provider'); gen.prop(s, 'source_image_path'); gen.prop(s, 'prompt'); gen.prop(s, 'repo_path'); gen.prop(s, 'endpoint'); gen.prop(s, 'api_key'); gen.operator('dct_bridge.queue_generation')
        rig = l.box(); rig.label(text='Automatic Rigging'); rig.prop(s, 'rig_provider'); rig.prop(s, 'rig_repo_path'); rig.prop(s, 'shell_executable'); rig.prop(s, 'blender_executable'); rig.operator('dct_bridge.queue_rig')


classes = (DCTBridgeSettings, DCT_OT_send_pose, DCT_OT_fetch_pose, DCT_OT_send_custom_skeleton, DCT_OT_import_asset, DCT_OT_import_latest_asset, DCT_OT_prepare_viewport_payload, DCT_OT_queue_generation, DCT_OT_queue_rig, DCT_PT_bridge_panel)

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.dct_bridge_settings = bpy.props.PointerProperty(type=DCTBridgeSettings)

def unregister():
    if hasattr(bpy.types.Scene, 'dct_bridge_settings'): del bpy.types.Scene.dct_bridge_settings
    for cls in reversed(classes): bpy.utils.unregister_class(cls)

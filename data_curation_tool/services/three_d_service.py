from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin

import requests

from ..paths import AppPaths
from .media_service import MediaService
from .reference_service import ReferenceService

Progress = Callable[[float, str], None]

ASSET_EXTENSIONS = {".glb", ".gltf", ".fbx", ".obj", ".ply", ".stl", ".usd", ".usda", ".usdc", ".usdz", ".vrm", ".blend", ".dae", ".abc", ".bvh", ".x3d"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


class ThreeDService:
    """Local/cloud 3D generation, rigging, asset catalog, and Blender bridge.

    The service deliberately uses explicit provider adapters rather than an arbitrary
    shell-command field.  That keeps queued jobs inspectable and avoids turning a
    local web UI into a general command-execution endpoint.
    """

    def __init__(self, paths: AppPaths, media: MediaService, reference: ReferenceService):
        self.paths = paths
        self.media = media
        self.reference = reference
        self.assets_root = paths.outputs / "3d_assets"
        self.generation_root = self.assets_root / "generated"
        self.rig_root = self.assets_root / "rigged"
        self.import_root = self.assets_root / "imported"
        self.viewport_root = self.assets_root / "viewer_payloads"
        for folder in (self.assets_root, self.generation_root, self.rig_root, self.import_root, self.viewport_root):
            folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generation_providers() -> list[dict[str, Any]]:
        providers = [
            {
                "key": "triposr_local",
                "label": "TripoSR (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["obj", "glb"],
                "repo_url": "https://github.com/VAST-AI-Research/TripoSR",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 6,
                "supports_texture": True,
                "description": "Fast single-image reconstruction using the official run.py entry point.",
            },
            {
                "key": "stable_fast_3d_local",
                "label": "Stable Fast 3D / SF3D (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["glb"],
                "repo_url": "https://github.com/Stability-AI/stable-fast-3d",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 6,
                "supports_texture": True,
                "description": "Single-image GLB reconstruction with UVs/material prediction.",
            },
            {
                "key": "trellis_image_local",
                "label": "TRELLIS Image-to-3D (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["glb"],
                "repo_url": "https://github.com/microsoft/TRELLIS",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 16,
                "supports_texture": True,
                "description": "High-quality image-conditioned 3D generation and GLB export.",
            },
            {
                "key": "trellis_text_local",
                "label": "TRELLIS Text-to-3D (local repository)",
                "mode": "local_repo",
                "inputs": ["text"],
                "outputs": ["glb"],
                "repo_url": "https://github.com/microsoft/TRELLIS",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 16,
                "supports_texture": True,
                "description": "Text-conditioned TRELLIS pipeline; image-conditioned generation is usually preferred.",
            },
            {
                "key": "hunyuan3d_local_api",
                "label": "Hunyuan3D 2.x local API",
                "mode": "rest_api",
                "inputs": ["image"],
                "outputs": ["glb", "obj"],
                "default_endpoint": "http://127.0.0.1:8081/generate",
                "repo_url": "https://github.com/Tencent-Hunyuan/Hunyuan3D-2",
                "repo_required": False,
                "api_key_required": False,
                "supports_texture": True,
                "description": "Calls the official local FastAPI server with a base64 image request.",
            },
            {
                "key": "meshy_image_api",
                "label": "Meshy Image-to-3D API",
                "mode": "cloud_api",
                "inputs": ["image"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl"],
                "default_endpoint": "https://api.meshy.ai/openapi/v1/image-to-3d",
                "api_key_required": True,
                "supports_texture": True,
                "supports_rig_pose": True,
                "description": "Official asynchronous image-to-3D task API with downloadable model formats.",
            },

            {
                "key": "instantmesh_local",
                "label": "InstantMesh Image-to-3D (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["obj", "glb"],
                "repo_url": "https://github.com/TencentARC/InstantMesh",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 10,
                "supports_texture": True,
                "description": "Fast image-to-mesh generation through sparse-view reconstruction; useful for dataset bootstrapping and character asset drafts.",
            },
            {
                "key": "wonder3d_local",
                "label": "Wonder3D / Multi-view Reconstruction (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["obj", "glb"],
                "repo_url": "https://github.com/xxlong0/Wonder3D",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 10,
                "supports_texture": True,
                "description": "Multi-view normal/color generation workflow for textured mesh reconstruction.",
            },
            {
                "key": "zero123plus_local",
                "label": "Zero123++ Multi-view Prior (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["multi_view_images", "obj", "glb"],
                "repo_url": "https://github.com/SUDO-AI-3D/zero123plus",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 8,
                "supports_texture": False,
                "description": "Generates 3D-consistent views that can feed downstream mesh reconstruction.",
            },
            {
                "key": "sv3d_local",
                "label": "Stable Video 3D / SV3D (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["multi_view_video", "obj", "glb"],
                "repo_url": "https://github.com/Stability-AI/generative-models",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 12,
                "supports_texture": True,
                "description": "Stable Video 3D-style multi-view prior for textured 3D reconstruction workflows.",
            },
            {
                "key": "hunyuan3d_25_local_api",
                "label": "Hunyuan3D 2.5 local/API provider",
                "mode": "rest_api",
                "inputs": ["image", "text"],
                "outputs": ["glb", "fbx", "obj"],
                "default_endpoint": "http://127.0.0.1:8081/generate",
                "repo_url": "https://github.com/Tencent-Hunyuan/Hunyuan3D-2",
                "repo_required": False,
                "api_key_required": False,
                "vram_gb": 24,
                "supports_texture": True,
                "description": "Hunyuan3D 2.5-style high-detail shape and texture generation adapter contract; local API compatible with the bundled Hunyuan3D server pattern.",
            },
            {
                "key": "sparc3d_local",
                "label": "SPAR3D high-fidelity reconstruction (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["obj", "glb"],
                "repo_url": "https://github.com/gradient-spaces/Sparc3D",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 16,
                "supports_texture": True,
                "description": "High-fidelity reconstruction contract for locally installed SPAR3D-style providers.",
            },
            {
                "key": "rodin3d_api",
                "label": "Rodin / Hyper3D API",
                "mode": "cloud_api",
                "inputs": ["image", "text"],
                "outputs": ["glb", "fbx", "obj", "usdz"],
                "api_key_required": True,
                "supports_texture": True,
                "description": "Configurable API adapter for cloud 3D generation services returning downloadable character/object assets.",
            },
            {
                "key": "generic_image_to_3d_api",
                "label": "Generic REST Image-to-3D API",
                "mode": "rest_api",
                "inputs": ["image", "text"],
                "outputs": ["provider-defined"],
                "api_key_required": False,
                "description": "Configurable JSON REST adapter for a self-hosted or third-party endpoint.",
            },
        
        ]
        providers.extend([
            {
                "key": "trellis2_image_local",
                "label": "TRELLIS.2 4B Image-to-3D / PBR (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["glb", "gltf", "obj", "ply", "pbr_materials"],
                "repo_url": "https://github.com/microsoft/TRELLIS",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 24,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "SOTA single-image PBR asset provider contract for TRELLIS.2-style local installs. Uses the TRELLIS runner path until an upstream TRELLIS.2 CLI is configured.",
            },
            {
                "key": "hunyuan3d_21_local_api",
                "label": "Hunyuan3D 2.1 PBR local API",
                "mode": "rest_api",
                "inputs": ["image", "text", "multi_image"],
                "outputs": ["glb", "fbx", "obj", "ply", "stl"],
                "default_endpoint": "http://127.0.0.1:8081/generate",
                "repo_url": "https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1",
                "repo_required": False,
                "api_key_required": False,
                "vram_gb": 24,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "Hunyuan3D 2.1-compatible local/API adapter with image, text, and optional multi-view image fields.",
            },
            {
                "key": "hunyuan3d_text_local_api",
                "label": "Hunyuan3D text-to-3D local/API",
                "mode": "rest_api",
                "inputs": ["text"],
                "outputs": ["glb", "obj", "fbx"],
                "default_endpoint": "http://127.0.0.1:8081/generate",
                "repo_url": "https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1",
                "repo_required": False,
                "api_key_required": False,
                "vram_gb": 24,
                "supports_texture": True,
                "description": "Text-only Hunyuan3D-compatible adapter; useful when the first asset draft is generated from a prompt rather than an image.",
            },
            {
                "key": "unique3d_local",
                "label": "Unique3D Image-to-3D (local repository)",
                "mode": "local_repo",
                "inputs": ["image"],
                "outputs": ["obj", "glb", "ply"],
                "repo_url": "https://github.com/AiuniAI/Unique3D",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 12,
                "supports_texture": True,
                "description": "Fast single-image mesh generation provider contract. Set entry_script/command_options if your local checkout exposes a nonstandard CLI.",
            },
            {
                "key": "meshy_text_api",
                "label": "Meshy Text-to-3D API",
                "mode": "cloud_api",
                "inputs": ["text"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl"],
                "default_endpoint": "https://api.meshy.ai/openapi/v2/text-to-3d",
                "api_key_required": True,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "Meshy v2 text-to-3D task adapter with preview/refine polling and downloadable target formats.",
            },
            {
                "key": "meshy_multi_image_api",
                "label": "Meshy Multi-Image-to-3D API",
                "mode": "cloud_api",
                "inputs": ["multi_image", "text"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl"],
                "default_endpoint": "https://api.meshy.ai/openapi/v1/multi-image-to-3d",
                "api_key_required": True,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "Configurable Meshy multi-image adapter. Provide newline/comma-separated multi_image_paths or selected media + supplemental images.",
            },
            {
                "key": "tripo_text_api",
                "label": "Tripo Text-to-3D API",
                "mode": "cloud_api",
                "inputs": ["text"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl"],
                "api_key_required": True,
                "supports_texture": True,
                "supports_animation": True,
                "description": "Generic Tripo-compatible text-to-3D adapter. Set endpoint, API key, response URL path, and polling path per your Tripo API account.",
            },
            {
                "key": "tripo_image_api",
                "label": "Tripo Image-to-3D API",
                "mode": "cloud_api",
                "inputs": ["image", "text"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl"],
                "api_key_required": True,
                "supports_texture": True,
                "supports_animation": True,
                "description": "Generic Tripo-compatible image-to-3D adapter. Supports image and optional prompt/negative prompt fields.",
            },
            {
                "key": "tripo_multi_image_api",
                "label": "Tripo Multi-Image-to-3D API",
                "mode": "cloud_api",
                "inputs": ["multi_image", "text"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl"],
                "api_key_required": True,
                "supports_texture": True,
                "supports_animation": True,
                "description": "Generic Tripo-compatible multi-view adapter using image_paths/images JSON fields.",
            },
            {
                "key": "rodin_text_api",
                "label": "Rodin / Hyper3D Text-to-3D API",
                "mode": "cloud_api",
                "inputs": ["text"],
                "outputs": ["glb", "fbx", "obj", "usdz"],
                "api_key_required": True,
                "supports_texture": True,
                "description": "Rodin/Hyper3D text-to-3D adapter contract. Configure endpoint/polling paths for the active Rodin API route.",
            },
            {
                "key": "rodin_multi_image_api",
                "label": "Rodin / Hyper3D Multi-Image-to-3D API",
                "mode": "cloud_api",
                "inputs": ["multi_image", "text"],
                "outputs": ["glb", "fbx", "obj", "usdz"],
                "api_key_required": True,
                "supports_texture": True,
                "description": "Rodin/Hyper3D multi-image adapter contract for production-ready meshes from several reference views.",
            },

            {
                "key": "tripo_p1_smart_mesh_api",
                "label": "Tripo P1.0 Smart Mesh / P1 API (cloud)",
                "mode": "cloud_api",
                "inputs": ["text", "image", "multi_image"],
                "outputs": ["glb", "fbx", "obj", "usdz", "stl", "3mf"],
                "api_key_required": True,
                "supports_texture": True,
                "supports_pbr": True,
                "supports_animation": True,
                "availability": "hosted_saas_api",
                "open_source": False,
                "local_runtime": False,
                "api_model_ids": ["Tripo-P1.0", "P1", "p1-smart-mesh"],
                "description": "Tripo P1.0 / Smart Mesh is exposed as a hosted/API provider row. Configure endpoint/API key; do not assume local open weights.",
            },
            {
                "key": "hunyuan3d_31_cloud_api",
                "label": "Hunyuan3D 3.1 / Tencent Cloud 3D API (cloud)",
                "mode": "cloud_api",
                "inputs": ["text", "image", "multi_image"],
                "outputs": ["glb", "fbx", "obj", "ply", "stl"],
                "api_key_required": True,
                "supports_texture": True,
                "supports_pbr": True,
                "availability": "hosted_saas_api",
                "open_source": False,
                "local_runtime": False,
                "api_model_ids": ["Hunyuan3D-3.1", "Hunyuan-3D-Global-v3", "hunyuan3d_31"],
                "description": "Hunyuan3D 3.1 is represented as a cloud/API contract. Use Hunyuan3D 2.x/2.1 rows for local/open-source workflows.",
            },
            {
                "key": "rodin_hyper3d_api",
                "label": "Rodin / Hyper3D Production API (cloud)",
                "mode": "cloud_api",
                "inputs": ["text", "image", "multi_image"],
                "outputs": ["glb", "fbx", "obj", "usdz"],
                "api_key_required": True,
                "supports_texture": True,
                "supports_pbr": True,
                "availability": "hosted_saas_api",
                "open_source": False,
                "local_runtime": False,
                "description": "Hosted Rodin/Hyper3D provider row for production text/image/multiview 3D generation and downloadable assets.",
            },
            {
                "key": "comfyui_3d_workflow_api",
                "label": "ComfyUI 3D Workflow / Partner Nodes",
                "mode": "rest_api",
                "inputs": ["image", "text", "multi_image", "video"],
                "outputs": ["workflow_outputs", "glb", "obj", "video", "image_sequence"],
                "default_endpoint": "http://127.0.0.1:8188/prompt",
                "api_key_required": False,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "Queues a ComfyUI workflow JSON that may call local 3D nodes or cloud partner nodes such as Tripo/Rodin.",
            },
            {
                "key": "nerfstudio_video_to_3d_local",
                "label": "Nerfstudio / Gaussian Splat Video-to-3D local pipeline",
                "mode": "local_repo",
                "inputs": ["video", "image_sequence"],
                "outputs": ["ply", "glb", "splat", "obj"],
                "repo_url": "https://github.com/nerfstudio-project/nerfstudio",
                "repo_required": True,
                "api_key_required": False,
                "vram_gb": 12,
                "supports_texture": True,
                "description": "Video/turntable-to-3D provider contract for local photogrammetry/NeRF/Gaussian-splat pipelines. Use command_options to point at the exact training/export CLI.",
            },
            {
                "key": "dream_textures_blender_bridge",
                "label": "Dream Textures Blender Add-on / Backend Bridge",
                "mode": "blender_addon",
                "inputs": ["text", "image"],
                "outputs": ["texture", "material", "image", "blend"],
                "repo_url": "https://github.com/carson-katri/dream-textures",
                "api_key_required": False,
                "vram_gb": 8,
                "supports_texture": True,
                "description": "Creates a Blender handoff manifest for Dream Textures texture/material workflows; use Blender/MCP or the Dream Textures backend API to execute generation.",
            },
            {
                "key": "quickmaker_blender_bridge",
                "label": "QuickMaker Blender AI Suite Bridge",
                "mode": "blender_addon",
                "inputs": ["text", "image", "multi_image", "video"],
                "outputs": ["image", "video", "texture", "glb", "fbx", "obj", "blend"],
                "api_key_required": False,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "Creates a Blender handoff manifest for QuickMaker account/add-on workflows covering 2D, video, texture, and 3D assets.",
            },
            {
                "key": "blender_mcp_addon",
                "label": "Blender MCP Add-on / Server Handoff",
                "mode": "mcp_handoff",
                "inputs": ["text", "image", "multi_image", "video"],
                "outputs": ["blend", "glb", "fbx", "obj", "render"],
                "api_key_required": False,
                "supports_texture": True,
                "supports_pbr": True,
                "description": "Creates an approved MCP handoff manifest for scene creation, mesh cleanup, retopology, rendering, and export inside Blender.",
            },
            {
                "key": "zbrush_mcp_bridge",
                "label": "ZBrush MCP/Python Sculpt Refinement Bridge",
                "mode": "mcp_handoff",
                "inputs": ["text", "image", "asset"],
                "outputs": ["obj", "fbx", "ztl", "blend", "normal_maps"],
                "api_key_required": False,
                "supports_texture": False,
                "description": "Creates an approved ZBrush handoff manifest for sculpt review, GoZ-style import/export, high-resolution mesh cleanup, and normal/detail-map workflows.",
            },
            {
                "key": "generic_text_to_3d_api",
                "label": "Generic REST Text-to-3D API",
                "mode": "rest_api",
                "inputs": ["text"],
                "outputs": ["provider-defined"],
                "api_key_required": False,
                "description": "Provider-neutral text-to-3D JSON adapter with configurable endpoint, request body, polling, and response URL path.",
            },
            {
                "key": "generic_multi_image_to_3d_api",
                "label": "Generic REST Multi-Image-to-3D API",
                "mode": "rest_api",
                "inputs": ["multi_image", "text"],
                "outputs": ["provider-defined"],
                "api_key_required": False,
                "description": "Provider-neutral multi-image/multi-view-to-3D adapter with image_paths/images field configuration.",
            },
            {
                "key": "generic_video_to_3d_api",
                "label": "Generic REST Video-to-3D API",
                "mode": "rest_api",
                "inputs": ["video", "text"],
                "outputs": ["provider-defined"],
                "api_key_required": False,
                "description": "Provider-neutral video-to-3D/turntable-to-3D adapter. Use video_field/video_as_data_uri plus polling/response URL path settings.",
            },
        ])
        # Preserve stable UI order while removing accidental duplicate keys from older catalogs.
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for row in providers:
            key = str(row.get("key") or "")
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped


    @staticmethod
    def rigging_providers() -> list[dict[str, Any]]:
        return [
            {
                "key": "unirig_local",
                "label": "UniRig automatic skeleton + skinning (local repository)",
                "mode": "local_repo",
                "inputs": ["obj", "fbx", "glb", "vrm"],
                "outputs": ["fbx", "glb"],
                "repo_url": "https://github.com/VAST-AI-Research/UniRig",
                "repo_required": True,
                "vram_gb": None,
                "description": "Predicts a skeleton, predicts skinning weights, and merges them into a rigged asset.",
            },
            {
                "key": "blender_pose_rig",
                "label": "Blender pose-driven armature + automatic weights",
                "mode": "blender",
                "inputs": ["obj", "fbx", "glb", "gltf", "ply", "stl", "usd", "usdz"],
                "outputs": ["glb", "fbx"],
                "repo_required": False,
                "description": "Builds an armature from an editable DCT pose annotation and binds the mesh with Blender automatic weights.",
            },
        ]

    @staticmethod
    def print_providers() -> list[dict[str, Any]]:
        return [
            {
                "key": "prusaslicer",
                "label": "PrusaSlicer CLI",
                "mode": "slicer_cli",
                "inputs": ["stl", "obj", "3mf", "amf"],
                "outputs": ["gcode", "stl", "3mf", "obj", "amf"],
                "default_executable": "prusa-slicer-console.exe" if os.name == "nt" else "prusa-slicer",
                "command_notes": "Uses --export-gcode/--export-stl/--export-3mf/--export-obj/--export-amf with optional --load profile.ini.",
                "mcp_tool": "prusaslicer",
            },
            {
                "key": "orcaslicer",
                "label": "OrcaSlicer CLI",
                "mode": "slicer_cli",
                "inputs": ["stl", "obj", "3mf"],
                "outputs": ["gcode", "3mf", "stl"],
                "default_executable": "OrcaSlicer.exe" if os.name == "nt" else "orca-slicer",
                "command_notes": "Builds a PrusaSlicer-compatible command contract where supported by the installed OrcaSlicer build.",
                "mcp_tool": "orcaslicer",
            },
            {
                "key": "bambu_studio",
                "label": "Bambu Studio handoff",
                "mode": "slicer_project_handoff",
                "inputs": ["3mf", "stl", "obj"],
                "outputs": ["3mf", "gcode", "project"],
                "default_executable": "BambuStudio.exe" if os.name == "nt" else "bambu-studio",
                "command_notes": "Prefer project/profile handoff; exact CLI behavior may depend on the installed build.",
                "mcp_tool": "bambu_studio",
            },
            {
                "key": "curaengine",
                "label": "CuraEngine CLI",
                "mode": "slicer_engine_cli",
                "inputs": ["stl"],
                "outputs": ["gcode"],
                "default_executable": "CuraEngine.exe" if os.name == "nt" else "CuraEngine",
                "command_notes": "Uses CuraEngine slice -l input.stl -o output.gcode and optional -j machine/extruder definition JSON.",
                "mcp_tool": "curaengine",
            },
            {
                "key": "slic3r",
                "label": "Slic3r CLI",
                "mode": "slicer_cli",
                "inputs": ["stl", "obj", "3mf", "amf"],
                "outputs": ["gcode", "stl", "3mf", "obj", "amf"],
                "default_executable": "slic3r.exe" if os.name == "nt" else "slic3r",
                "command_notes": "Uses Slic3r-style --export-gcode/--export-stl/--export-3mf/--export-obj/--export-amf where supported.",
                "mcp_tool": "slic3r",
            },
        ]

    def provider_catalog(self) -> dict[str, Any]:
        return {"generation": self.generation_providers(), "rigging": self.rigging_providers(), "print": self.print_providers()}

    def _print_provider_by_key(self, provider: str) -> dict[str, Any]:
        for row in self.print_providers():
            if row.get("key") == provider:
                return row
        return {}

    def prepare_print_handoff(self, payload: dict[str, Any]) -> dict[str, Any]:
        provider = str(payload.get("provider") or "prusaslicer").strip().lower()
        meta = self._print_provider_by_key(provider)
        if not meta:
            raise ValueError(f"Unknown 3D print/slicer provider: {provider!r}")
        asset = self._resolve_asset_input(payload)
        fmt = str(payload.get("output_format") or "gcode").lower().lstrip(".")
        profile_path = str(payload.get("profile_path") or payload.get("config_path") or "").strip()
        exe = str(payload.get("executable_path") or payload.get("slicer_executable") or meta.get("default_executable") or provider).strip()
        output_dir = Path(payload.get("output_dir") or (self.assets_root / "print_handoffs")).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(payload.get("output_path") or "").strip()
        if not output_path:
            output_path = str(output_dir / f"{asset.stem}.{('gcode' if fmt == 'gcode' else fmt)}")
        extra_args = payload.get("extra_args") or []
        if isinstance(extra_args, str):
            extra_args = shlex.split(extra_args) if extra_args.strip() else []
        command = self._slicer_command(provider, exe, asset, Path(output_path), fmt, profile_path=profile_path, extra_args=[str(x) for x in extra_args])
        manifest = {
            "version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "provider_meta": meta,
            "input_asset": str(asset),
            "output_path": output_path,
            "output_format": fmt,
            "profile_path": profile_path,
            "command": command,
            "command_string": " ".join(shlex.quote(str(x)) for x in command),
            "mcp_tool": meta.get("mcp_tool"),
            "manual_review_required": True,
            "note": "This creates a slicer/MCP handoff manifest. Review printer/profile/material settings before running or sending G-code to any printer.",
        }
        manifest_path = output_dir / f"print_handoff_{asset.stem}_{provider}_{uuid.uuid4().hex[:8]}.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        result = {"ok": True, "manifest_path": str(manifest_path), "manifest": manifest, "dry_run": bool(payload.get("dry_run", True))}
        if payload.get("run"):
            if not payload.get("user_approved"):
                raise ValueError("Running slicer commands requires user_approved=true. Use dry-run/manifest first.")
            proc = subprocess.run(command, capture_output=True, text=True, timeout=max(30, int(payload.get("timeout_seconds") or 3600)))
            result["run"] = {"returncode": proc.returncode, "stdout": proc.stdout[-20000:], "stderr": proc.stderr[-20000:], "ok": proc.returncode == 0}
        return result

    def _slicer_command(self, provider: str, executable: str, asset: Path, output: Path, fmt: str, *, profile_path: str = "", extra_args: list[str] | None = None) -> list[str]:
        low = str(provider or "").lower().replace("_", "-")
        extra_args = list(extra_args or [])
        if low in {"prusaslicer", "orcaslicer", "orca-slicer", "slic3r", "bambu-studio", "bambu"}:
            flag = {"gcode": "--export-gcode", "stl": "--export-stl", "3mf": "--export-3mf", "obj": "--export-obj", "amf": "--export-amf"}.get(fmt, "--export-gcode")
            cmd = [executable]
            if profile_path:
                cmd += ["--load", profile_path]
            cmd += [flag, "--output", str(output), str(asset)]
            return cmd + extra_args
        if low in {"curaengine", "cura-engine", "cura"}:
            cmd = [executable, "slice", "-l", str(asset), "-o", str(output)]
            if profile_path:
                cmd += ["-j", profile_path]
            return cmd + extra_args
        return [executable, str(asset), *extra_args]

    def _safe_job_dir(self, root: Path, provider: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_provider = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in provider).strip("_") or "job"
        job_dir = root / f"{stamp}_{safe_provider}_{uuid.uuid4().hex[:8]}"
        job_dir.mkdir(parents=True, exist_ok=False)
        return job_dir

    @staticmethod
    def _redact(payload: dict[str, Any]) -> dict[str, Any]:
        out = dict(payload)
        for key in list(out):
            if any(token in key.lower() for token in ("api_key", "token", "authorization", "secret")) and out.get(key):
                out[key] = "***"
        headers = dict(out.get("headers") or {})
        for key in list(headers):
            if key.lower() in {"authorization", "x-api-key", "api-key"}:
                headers[key] = "***"
        if headers:
            out["headers"] = headers
        return out

    def _write_request(self, job_dir: Path, payload: dict[str, Any]) -> None:
        (job_dir / "request.json").write_text(json.dumps(self._redact(payload), ensure_ascii=False, indent=2), encoding="utf-8")

    def _resolve_image(self, payload: dict[str, Any], *, required: bool = True) -> Path | None:
        media_id = payload.get("media_id")
        value = str(payload.get("input_path") or "").strip()
        if media_id:
            item = self.media.get(int(media_id))
            if not item:
                raise ValueError(f"Unknown media_id={media_id}")
            value = item.path
        if not value:
            if required:
                raise ValueError("Choose a source image/media item or provide input_path.")
            return None
        path = Path(value).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(str(path))
        if required and path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError(f"Expected an image input, got {path.suffix or 'no extension'}.")
        return path

    @staticmethod
    def _split_paths(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            raw = []
            for item in value:
                raw.extend(ThreeDService._split_paths(item))
            return raw
        text = str(value or "").strip()
        if not text:
            return []
        # Newlines are preferred because Windows paths can contain spaces; commas and semicolons
        # are also accepted for compact UI entry.
        parts = re.split(r"[\r\n,;]+", text)
        return [p.strip().strip('"').strip("'") for p in parts if p.strip()]

    def _resolve_multi_images(self, payload: dict[str, Any]) -> list[Path]:
        paths: list[Path] = []
        for field in ("multi_image_paths", "image_paths", "reference_image_paths"):
            for raw in self._split_paths(payload.get(field)):
                path = Path(raw).expanduser().resolve()
                if not path.exists() or not path.is_file():
                    raise FileNotFoundError(str(path))
                if path.suffix.lower() not in IMAGE_EXTENSIONS:
                    raise ValueError(f"Expected image input for multi-image provider, got {path.suffix or 'no extension'}: {path}")
                if path not in paths:
                    paths.append(path)
        image = self._resolve_image(payload, required=False)
        if image and image.suffix.lower() in IMAGE_EXTENSIONS and image not in paths:
            paths.insert(0, image)
        return paths

    def _resolve_video(self, payload: dict[str, Any]) -> Path | None:
        value = str(payload.get("video_path") or "").strip()
        if not value:
            path = self._resolve_image(payload, required=False)
            if path and path.suffix.lower() in VIDEO_EXTENSIONS:
                return path
            return None
        path = Path(value).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(str(path))
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError(f"Expected a video input, got {path.suffix or 'no extension'}.")
        return path

    @staticmethod
    def _provider_by_key(provider: str) -> dict[str, Any]:
        for row in ThreeDService.generation_providers():
            if row.get("key") == provider:
                return row
        return {}

    def _resolve_asset_input(self, payload: dict[str, Any]) -> Path:
        value = str(payload.get("asset_path") or payload.get("input_path") or "").strip()
        if not value:
            raise ValueError("Select a 3D asset first.")
        path = Path(value).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(str(path))
        if path.suffix.lower() not in ASSET_EXTENSIONS:
            raise ValueError(f"Unsupported 3D asset format: {path.suffix}")
        return path

    @staticmethod
    def _python(payload: dict[str, Any]) -> str:
        return str(payload.get("python_executable") or sys.executable)

    def _resolve_blender_executable(self, value: str | None = None) -> str:
        """Return a real Blender executable path, avoiding Windows launchers.

        Blender's Start-menu/launcher executable can return before a background
        Python job actually runs, which produces the confusing "completed but no
        viewport payload" symptom.  This resolver prefers blender.exe next to
        or beneath the provided path and strips quotes pasted from Windows file
        dialogs.
        """
        raw = str(value or os.environ.get("DCT_BLENDER_EXECUTABLE") or "").strip().strip('\"').strip("'")
        candidates: list[Path] = []
        if raw:
            path = Path(raw).expanduser()
            if path.is_dir():
                candidates.extend([path / "blender.exe", path / "blender"])
                candidates.extend(sorted(path.rglob("blender.exe"), key=lambda p: len(str(p))))
            else:
                name = path.name.lower()
                if name in {"blender-launcher.exe", "blender launcher.exe", "blender-launcher"}:
                    candidates.extend([path.with_name("blender.exe"), path.parent / "blender.exe"])
                    candidates.extend(sorted(path.parent.rglob("blender.exe"), key=lambda p: len(str(p))))
                else:
                    candidates.append(path)
        # Common Windows installation locations.  Kept harmless on Linux/macOS.
        if os.name == "nt":
            for root in [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), str(Path.home())]:
                if root:
                    base = Path(root)
                    candidates.extend(sorted(base.glob("Blender Foundation/Blender*/blender.exe")))
                    candidates.extend(sorted(base.glob("**/Blender*/blender.exe"))[:20])
        for candidate in candidates:
            try:
                if candidate.exists() and candidate.is_file():
                    return str(candidate.resolve())
            except OSError:
                continue
        if raw:
            lowered = Path(raw).name.lower()
            if lowered in {"blender-launcher.exe", "blender launcher.exe", "blender-launcher"}:
                raise FileNotFoundError(
                    f"{raw} is a Blender launcher, not the background-capable blender executable. "
                    "Select blender.exe from the same Blender install folder, for example "
                    r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe."
                )
            return raw
        return "blender"

    @staticmethod
    def _repo(payload: dict[str, Any], entry: str = "run.py") -> Path:
        value = str(payload.get("repo_path") or "").strip()
        if not value:
            raise ValueError("Set repo_path to the cloned provider repository.")
        repo = Path(value).expanduser().resolve()
        if not repo.is_dir():
            raise FileNotFoundError(str(repo))
        if entry and not (repo / entry).exists():
            raise FileNotFoundError(f"Expected {entry} inside repository: {repo}")
        return repo

    @staticmethod
    def _run(command: list[str], *, cwd: Path, timeout: int, progress: Progress, env: dict[str, str] | None = None) -> dict[str, Any]:
        progress(0.15, "Starting provider process")
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            text=True,
            capture_output=True,
            timeout=max(30, int(timeout)),
            check=False,
        )
        result = {
            "command": command,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-20000:],
            "stderr": (proc.stderr or "")[-20000:],
        }
        if proc.returncode != 0:
            raise RuntimeError(f"Provider process failed with exit code {proc.returncode}.\n{result['stderr'] or result['stdout']}")
        progress(0.82, "Provider process completed; locating output assets")
        return result

    @staticmethod
    def _asset_candidates(folder: Path) -> list[Path]:
        return sorted(
            (p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in ASSET_EXTENSIONS),
            key=lambda p: (p.stat().st_mtime_ns, p.stat().st_size),
            reverse=True,
        )

    @staticmethod
    def _copy_asset(source: Path, job_dir: Path, preferred_name: str = "") -> Path:
        source = source.resolve()
        try:
            source.relative_to(job_dir.resolve())
            return source
        except Exception:
            pass
        name = preferred_name or source.name
        dest = job_dir / name
        if dest.exists():
            dest = job_dir / f"{dest.stem}_{uuid.uuid4().hex[:6]}{dest.suffix}"
        shutil.copy2(source, dest)
        return dest

    @staticmethod
    def _data_uri(path: Path) -> str:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    @staticmethod
    def _download(url: str, destination: Path, headers: dict[str, str] | None = None, timeout: int = 600) -> Path:
        with requests.get(url, headers=headers or {}, stream=True, timeout=(30, max(60, timeout))) as response:
            response.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as handle:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        return destination

    @staticmethod
    def _json_path(value: Any, path: str) -> Any:
        current = value
        for token in [part for part in str(path or "").split(".") if part]:
            if isinstance(current, list):
                current = current[int(token)]
            elif isinstance(current, dict):
                current = current.get(token)
            else:
                return None
        return current

    def _finalize(self, job_dir: Path, provider: str, payload: dict[str, Any], assets: list[Path], details: dict[str, Any] | None = None) -> dict[str, Any]:
        unique: list[Path] = []
        seen: set[str] = set()
        for asset in assets:
            if not asset.exists() or asset.suffix.lower() not in ASSET_EXTENSIONS:
                continue
            resolved = str(asset.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            unique.append(asset.resolve())
        metadata = {
            "provider": provider,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "request": self._redact(payload),
            "details": details or {},
            "assets": [str(path) for path in unique],
        }
        (job_dir / "result.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        for asset in unique:
            sidecar = asset.with_suffix(asset.suffix + ".dct.json")
            sidecar.write_text(json.dumps(metadata | {"primary_asset": str(asset)}, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "provider": provider,
            "job_dir": str(job_dir),
            "assets": [self.asset_record(path) for path in unique],
            "count": len(unique),
            "details": details or {},
        }

    def generate(self, payload: dict[str, Any], progress: Progress) -> dict[str, Any]:
        provider = str(payload.get("provider") or "").strip()
        provider_meta = self._provider_by_key(provider)
        known = {row["key"] for row in self.generation_providers()}
        if provider not in known:
            raise ValueError(f"Unknown 3D generation provider: {provider!r}")
        job_dir = self._safe_job_dir(self.generation_root, provider)
        self._write_request(job_dir, payload)
        prompt = str(payload.get("prompt") or "").strip()
        inputs = set(str(x).lower() for x in (provider_meta.get("inputs") or []))
        text_only = inputs == {"text"}
        image_required = ("image" in inputs and "text" not in inputs and not text_only and "multi_image" not in inputs and "video" not in inputs)
        image = self._resolve_image(payload, required=image_required)
        multi_images = self._resolve_multi_images(payload) if "multi_image" in inputs else []
        video = self._resolve_video(payload) if "video" in inputs or "image_sequence" in inputs else None
        asset_input = str(payload.get("asset_path") or payload.get("input_asset_path") or "").strip()
        if "text" in inputs and not prompt and not image and not multi_images and not video and not asset_input:
            raise ValueError(f"{provider_meta.get('label') or provider} requires a prompt or source media/asset input.")
        if "multi_image" in inputs and not multi_images and not prompt:
            raise ValueError(f"{provider_meta.get('label') or provider} requires multi_image_paths/image_paths or a prompt.")
        if "video" in inputs and not video and not prompt and not image:
            raise ValueError(f"{provider_meta.get('label') or provider} requires video_path or a prompt/source image.")
        if provider in {"trellis_text_local", "meshy_text_api", "generic_text_to_3d_api", "tripo_text_api", "rodin_text_api", "hunyuan3d_text_local_api"} and not prompt:
            raise ValueError(f"{provider_meta.get('label') or provider} requires a prompt.")
        timeout = int(payload.get("timeout_seconds") or 1800)
        if payload.get("dry_run"):
            plan = self._generation_plan(provider, payload, image, job_dir, multi_images=multi_images, video=video)
            (job_dir / "dry_run_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
            progress(1.0, "Dry-run plan created; no model was executed")
            return {"ok": True, "dry_run": True, "provider": provider, "job_dir": str(job_dir), "plan": plan, "assets": [], "count": 0}

        progress(0.04, "Preparing 3D generation input")
        details: dict[str, Any] = {}
        assets: list[Path] = []
        if provider in {"triposr_local", "stable_fast_3d_local"}:
            assert image is not None
            repo = self._repo(payload)
            command = [self._python(payload), str(repo / "run.py"), str(image), "--output-dir", str(job_dir)]
            texture_resolution = payload.get("texture_resolution")
            if texture_resolution:
                command += ["--texture-resolution", str(int(texture_resolution))]
            if provider == "triposr_local" and bool(payload.get("bake_texture")):
                command.append("--bake-texture")
            if provider == "stable_fast_3d_local" and payload.get("remesh_option"):
                command += ["--remesh_option", str(payload.get("remesh_option"))]
            details = self._run(command, cwd=repo, timeout=timeout, progress=progress)
            assets = self._asset_candidates(job_dir)
        elif provider in {"trellis_image_local", "trellis_text_local", "trellis2_image_local"}:
            repo = self._repo(payload, entry="")
            runner = self.paths.root / "scripts" / "three_d" / "trellis_runner.py"
            if not runner.exists():
                raise FileNotFoundError(f"Bundled TRELLIS runner not found: {runner}")
            command = [self._python(payload), str(runner), "--repo", str(repo), "--output", str(job_dir / "trellis.glb")]
            if image:
                command += ["--image", str(image)]
            if prompt:
                command += ["--prompt", prompt]
            if payload.get("seed") is not None:
                command += ["--seed", str(int(payload.get("seed") or 0))]
            if payload.get("simplify") is not None:
                command += ["--simplify", str(float(payload.get("simplify")))]
            if payload.get("texture_size") is not None:
                command += ["--texture-size", str(int(payload.get("texture_size")))]
            env = dict(os.environ)
            env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
            details = self._run(command, cwd=repo, timeout=timeout, progress=progress, env=env)
            assets = self._asset_candidates(job_dir)
        elif provider in {"hunyuan3d_local_api", "hunyuan3d_25_local_api"}:
            assert image is not None
            assets, details = self._generate_hunyuan(payload, image, job_dir, timeout, progress)
        elif provider in {"hunyuan3d_21_local_api", "hunyuan3d_text_local_api"}:
            assets, details = self._generate_generic(payload, image, prompt, job_dir, timeout, progress, images=multi_images, video=video)
        elif provider == "meshy_image_api":
            assert image is not None
            assets, details = self._generate_meshy(payload, image, job_dir, timeout, progress)
        elif provider == "meshy_text_api":
            assets, details = self._generate_meshy_text(payload, prompt, job_dir, timeout, progress)
        elif provider in {
            "generic_image_to_3d_api", "generic_text_to_3d_api", "generic_multi_image_to_3d_api", "generic_video_to_3d_api",
            "rodin3d_api", "rodin_text_api", "rodin_multi_image_api", "rodin_hyper3d_api",
            "tripo_text_api", "tripo_image_api", "tripo_multi_image_api", "tripo_p1_smart_mesh_api",
            "hunyuan3d_31_cloud_api", "meshy_multi_image_api", "comfyui_3d_workflow_api",
        }:
            assets, details = self._generate_generic(payload, image, prompt, job_dir, timeout, progress, images=multi_images, video=video)
        elif provider in {"dream_textures_blender_bridge", "quickmaker_blender_bridge", "blender_mcp_addon", "zbrush_mcp_bridge"}:
            details = self._generate_external_tool_handoff(provider, payload, image, prompt, job_dir, progress, images=multi_images, video=video)
            assets = []
        elif provider in {"instantmesh_local", "wonder3d_local", "zero123plus_local", "sv3d_local", "sparc3d_local", "unique3d_local", "nerfstudio_video_to_3d_local"}:
            if image is None and multi_images:
                image = multi_images[0]
            if image is None and video is None:
                raise ValueError(f"{provider_meta.get('label') or provider} requires an image/video path.")
            assets, details = self._generate_generic_local_repo(payload, image or video, prompt, job_dir, timeout, progress)
        if not assets:
            if details.get("handoff_manifest"):
                progress(1.0, "External tool handoff manifest created")
                return {"ok": True, "provider": provider, "job_dir": str(job_dir), "handoff": True, "handoff_manifest": details.get("handoff_manifest"), "assets": [], "count": 0, "details": details}
            raise RuntimeError(f"{provider} completed but produced no supported 3D asset file.")
        progress(0.96, f"Cataloging {len(assets)} generated asset(s)")
        result = self._finalize(job_dir, provider, payload, assets, details)
        progress(1.0, "3D generation complete")
        return result

    def _generation_plan(self, provider: str, payload: dict[str, Any], image: Path | None, job_dir: Path, *, multi_images: list[Path] | None = None, video: Path | None = None) -> dict[str, Any]:
        multi_images = multi_images or []
        plan: dict[str, Any] = {"provider": provider, "input": str(image) if image else None, "multi_images": [str(p) for p in multi_images], "video": str(video) if video else None, "output_dir": str(job_dir)}
        if provider in {"triposr_local", "stable_fast_3d_local"}:
            repo = Path(str(payload.get("repo_path") or "<repo_path>"))
            command = [self._python(payload), str(repo / "run.py"), str(image or "<image>"), "--output-dir", str(job_dir)]
            if payload.get("texture_resolution"):
                command += ["--texture-resolution", str(int(payload["texture_resolution"]))]
            if provider == "triposr_local" and bool(payload.get("bake_texture")):
                command.append("--bake-texture")
            if provider == "stable_fast_3d_local" and payload.get("remesh_option"):
                command += ["--remesh_option", str(payload["remesh_option"])]
            plan["command"] = command
        elif provider.startswith("trellis_") or provider.startswith("trellis2_"):
            command = [self._python(payload), str(self.paths.root / "scripts/three_d/trellis_runner.py"), "--repo", str(payload.get("repo_path") or "<repo_path>"), "--output", str(job_dir / "trellis.glb")]
            if image:
                command += ["--image", str(image)]
            prompt = str(payload.get("prompt") or "").strip()
            if prompt:
                command += ["--prompt", prompt]
            if payload.get("seed") is not None:
                command += ["--seed", str(int(payload.get("seed") or 0))]
            if payload.get("simplify") is not None:
                command += ["--simplify", str(float(payload["simplify"]))]
            if payload.get("texture_size") is not None:
                command += ["--texture-size", str(int(payload["texture_size"]))]
            plan["command"] = command
        elif provider in {"hunyuan3d_local_api", "hunyuan3d_25_local_api", "hunyuan3d_21_local_api", "hunyuan3d_text_local_api"}:
            plan["request"] = {
                "method": "POST",
                "endpoint": payload.get("endpoint") or "http://127.0.0.1:8081/generate",
                "body_fields": ["image", "texture", "seed", "octree_resolution", "num_inference_steps", "guidance_scale", "face_count", "type"],
                "note": "The Hunyuan3D local API performs background removal internally and runs generation out-of-process; the app downloads/records its returned asset.",
            }
        elif provider in {"instantmesh_local", "wonder3d_local", "zero123plus_local", "sv3d_local", "sparc3d_local", "unique3d_local", "nerfstudio_video_to_3d_local"}:
            repo = Path(str(payload.get("repo_path") or "<repo_path>"))
            entry = payload.get("entry_script") or payload.get("options", {}).get("entry_script") or "<entry_script>"
            plan["command"] = [self._python(payload), str(repo / str(entry)), "--input", str(image or "<image>"), "--output-dir", str(job_dir)]
            plan["note"] = "Repository adapters differ. Set entry_script or command_options if the default CLI names do not match the local repository."
        elif provider in {"dream_textures_blender_bridge", "quickmaker_blender_bridge", "blender_mcp_addon", "zbrush_mcp_bridge"}:
            plan["handoff"] = {
                "target_tool": "zbrush" if provider == "zbrush_mcp_bridge" else "blender",
                "manifest": str(job_dir / "external_tool_handoff.json"),
                "note": "This provider creates an MCP/add-on handoff manifest. Execute the generated instructions from the MCP Tools/Blender/ZBrush workflow after user approval.",
            }
        elif provider in {"meshy_image_api", "meshy_text_api", "meshy_multi_image_api"}:
            default_endpoint = "https://api.meshy.ai/openapi/v2/text-to-3d" if provider == "meshy_text_api" else ("https://api.meshy.ai/openapi/v1/multi-image-to-3d" if provider == "meshy_multi_image_api" else "https://api.meshy.ai/openapi/v1/image-to-3d")
            plan["request"] = {"method": "POST", "endpoint": payload.get("endpoint") or default_endpoint, "asynchronous": True, "target_formats": payload.get("target_formats") or [payload.get("output_format") or "glb"]}
        else:
            fields = ["prompt"]
            if image:
                fields.append("image")
            if multi_images:
                fields.append("images")
            if video:
                fields.append("video")
            plan["request"] = {"method": payload.get("method") or "POST", "endpoint": payload.get("endpoint") or "<endpoint>", "body_fields": fields, "response_url_path": payload.get("response_url_path") or ""}
        return plan

    def _generate_external_tool_handoff(self, provider: str, payload: dict[str, Any], image: Path | None, prompt: str, job_dir: Path, progress: Progress, *, images: list[Path] | None = None, video: Path | None = None) -> dict[str, Any]:
        progress(0.35, "Writing external tool/MCP handoff manifest")
        target_tool = "zbrush" if provider == "zbrush_mcp_bridge" else "blender"
        manifest = {
            "provider": provider,
            "target_tool": target_tool,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "input_image": str(image) if image else None,
            "multi_images": [str(p) for p in (images or [])],
            "video": str(video) if video else None,
            "asset_path": payload.get("asset_path") or payload.get("input_asset_path") or "",
            "requested_outputs": payload.get("target_formats") or payload.get("output_format") or [],
            "instructions": payload.get("instructions") or payload.get("tool_instructions") or "",
            "approval_note": "This manifest is for user-approved external tool execution. It does not run Blender/ZBrush commands by itself.",
            "next_steps": [
                "Open MCP Tools and confirm the target tool is detected/enabled.",
                "Open the generated manifest in the target tool workflow or hand it to the local/cloud model via approved MCP tool use.",
                "Save any generated/refined asset back into the listed output_dir so the 3D Assets catalog can pick it up.",
            ],
            "output_dir": str(job_dir),
        }
        path = job_dir / "external_tool_handoff.json"
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"handoff_manifest": str(path), "target_tool": target_tool, "manifest": manifest}

    def _generate_hunyuan(self, payload: dict[str, Any], image: Path, job_dir: Path, timeout: int, progress: Progress) -> tuple[list[Path], dict[str, Any]]:
        endpoint = str(payload.get("endpoint") or "http://127.0.0.1:8081/generate").rstrip("/")
        request_body = {
            "image": base64.b64encode(image.read_bytes()).decode("ascii"),
            "texture": bool(payload.get("texture", True)),
            "seed": int(payload.get("seed") or 1234),
            "octree_resolution": int(payload.get("octree_resolution") or 256),
            "num_inference_steps": int(payload.get("num_inference_steps") or 5),
            "guidance_scale": float(payload.get("guidance_scale") or 5.0),
            "num_chunks": int(payload.get("num_chunks") or 8000),
            "face_count": int(payload.get("face_count") or 40000),
            "type": str(payload.get("output_format") or "glb").lower(),
        }
        progress(0.18, "Calling Hunyuan3D local API")
        response = requests.post(endpoint, json=request_body, timeout=(30, timeout))
        response.raise_for_status()
        fmt = request_body["type"] if request_body["type"] in {"glb", "obj", "ply", "stl"} else "glb"
        destination = job_dir / f"hunyuan3d.{fmt}"
        content_type = response.headers.get("content-type", "")
        details: dict[str, Any] = {"endpoint": endpoint, "status_code": response.status_code, "content_type": content_type}
        if "application/json" not in content_type:
            destination.write_bytes(response.content)
            return [destination], details
        data = response.json()
        details["response"] = self._redact(data if isinstance(data, dict) else {"value": data})
        assets = self._extract_api_assets(data, job_dir, fmt, timeout)
        return assets, details

    def _generate_meshy(self, payload: dict[str, Any], image: Path, job_dir: Path, timeout: int, progress: Progress) -> tuple[list[Path], dict[str, Any]]:
        api_key = str(payload.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("Meshy requires api_key.")
        endpoint = str(payload.get("endpoint") or "https://api.meshy.ai/openapi/v1/image-to-3d").rstrip("/")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        target_formats = payload.get("target_formats") or [str(payload.get("output_format") or "glb")]
        body: dict[str, Any] = {
            "image_url": self._data_uri(image),
            "enable_pbr": bool(payload.get("enable_pbr", True)),
            "should_remesh": bool(payload.get("should_remesh", True)),
            "should_texture": bool(payload.get("texture", True)),
            "target_formats": target_formats,
        }
        if payload.get("ai_model"):
            body["ai_model"] = payload["ai_model"]
        if payload.get("topology"):
            body["topology"] = payload["topology"]
        if payload.get("target_polycount"):
            body["target_polycount"] = int(payload["target_polycount"])
        if payload.get("pose_mode"):
            body["pose_mode"] = payload["pose_mode"]
        progress(0.12, "Submitting Meshy Image-to-3D task")
        response = requests.post(endpoint, headers=headers, json=body, timeout=(30, 120))
        response.raise_for_status()
        created = response.json()
        task_id = created.get("result") or created.get("id") or created.get("task_id")
        if isinstance(task_id, dict):
            task_id = task_id.get("id") or task_id.get("task_id")
        if not task_id:
            raise RuntimeError(f"Meshy did not return a task id: {created}")
        status_endpoint = f"{endpoint}/{task_id}"
        deadline = time.monotonic() + timeout
        interval = max(1.0, float(payload.get("poll_interval_seconds") or 5.0))
        last: dict[str, Any] = created
        while time.monotonic() < deadline:
            poll = requests.get(status_endpoint, headers=headers, timeout=(30, 120))
            poll.raise_for_status()
            last = poll.json()
            status = str(last.get("status") or last.get("result", {}).get("status") or "").upper()
            progress_value = last.get("progress") or last.get("result", {}).get("progress") or 0
            try:
                fraction = float(progress_value) / (100.0 if float(progress_value) > 1 else 1.0)
            except Exception:
                fraction = 0.0
            progress(0.18 + min(0.62, max(0.0, fraction) * 0.62), f"Meshy task {status or 'processing'}")
            if status in {"SUCCEEDED", "SUCCESS", "COMPLETED", "COMPLETE"}:
                break
            if status in {"FAILED", "CANCELED", "CANCELLED", "EXPIRED"}:
                raise RuntimeError(f"Meshy task {task_id} ended with status {status}: {last}")
            time.sleep(interval)
        else:
            raise TimeoutError(f"Meshy task {task_id} did not finish within {timeout} seconds.")
        result = last.get("result") if isinstance(last.get("result"), dict) else last
        model_urls = result.get("model_urls") or last.get("model_urls") or {}
        if not isinstance(model_urls, dict):
            model_urls = {}
        assets: list[Path] = []
        for fmt in target_formats:
            url = model_urls.get(str(fmt).lower())
            if not url:
                continue
            assets.append(self._download(str(url), job_dir / f"meshy_{task_id}.{str(fmt).lower()}", timeout=timeout))
        if not assets:
            for fmt, url in model_urls.items():
                if url and str(fmt).lower() in {ext.lstrip(".") for ext in ASSET_EXTENSIONS}:
                    assets.append(self._download(str(url), job_dir / f"meshy_{task_id}.{str(fmt).lower()}", timeout=timeout))
        return assets, {"endpoint": endpoint, "task_id": str(task_id), "status_response": self._redact(last)}

    def _generate_meshy_text(self, payload: dict[str, Any], prompt: str, job_dir: Path, timeout: int, progress: Progress) -> tuple[list[Path], dict[str, Any]]:
        api_key = str(payload.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("Meshy text-to-3D requires api_key.")
        if not prompt:
            raise ValueError("Meshy text-to-3D requires a prompt.")
        endpoint = str(payload.get("endpoint") or "https://api.meshy.ai/openapi/v2/text-to-3d").rstrip("/")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        target_formats = payload.get("target_formats") or [str(payload.get("output_format") or "glb")]
        body: dict[str, Any] = {
            "mode": str(payload.get("mode") or "preview"),
            "prompt": prompt,
            "negative_prompt": str(payload.get("negative_prompt") or ""),
            "enable_pbr": bool(payload.get("enable_pbr", True)),
            "target_formats": target_formats,
        }
        for key in ("art_style", "ai_model", "seed", "topology", "target_polycount", "symmetry_mode"):
            if payload.get(key) not in (None, ""):
                body[key] = payload.get(key)
        progress(0.12, "Submitting Meshy Text-to-3D task")
        response = requests.post(endpoint, headers=headers, json=body, timeout=(30, 120))
        response.raise_for_status()
        created = response.json()
        task_id = created.get("result") or created.get("id") or created.get("task_id")
        if isinstance(task_id, dict):
            task_id = task_id.get("id") or task_id.get("task_id")
        if not task_id:
            raise RuntimeError(f"Meshy text-to-3D did not return a task id: {created}")
        status_endpoint = f"{endpoint}/{task_id}"
        deadline = time.monotonic() + timeout
        interval = max(1.0, float(payload.get("poll_interval_seconds") or 5.0))
        last: dict[str, Any] = created
        while time.monotonic() < deadline:
            poll = requests.get(status_endpoint, headers=headers, timeout=(30, 120))
            poll.raise_for_status()
            last = poll.json()
            status = str(last.get("status") or last.get("result", {}).get("status") or "").upper()
            progress_value = last.get("progress") or last.get("result", {}).get("progress") or 0
            try:
                fraction = float(progress_value) / (100.0 if float(progress_value) > 1 else 1.0)
            except Exception:
                fraction = 0.0
            progress(0.18 + min(0.62, max(0.0, fraction) * 0.62), f"Meshy text task {status or 'processing'}")
            if status in {"SUCCEEDED", "SUCCESS", "COMPLETED", "COMPLETE"}:
                break
            if status in {"FAILED", "CANCELED", "CANCELLED", "EXPIRED"}:
                raise RuntimeError(f"Meshy text task {task_id} ended with status {status}: {last}")
            time.sleep(interval)
        else:
            raise TimeoutError(f"Meshy text task {task_id} did not finish within {timeout} seconds.")
        result = last.get("result") if isinstance(last.get("result"), dict) else last
        model_urls = result.get("model_urls") or last.get("model_urls") or {}
        if not isinstance(model_urls, dict):
            model_urls = {}
        assets: list[Path] = []
        for fmt in target_formats:
            url = model_urls.get(str(fmt).lower())
            if url:
                assets.append(self._download(str(url), job_dir / f"meshy_text_{task_id}.{str(fmt).lower()}", timeout=timeout))
        if not assets:
            assets = self._extract_api_assets(result, job_dir, str(payload.get("output_format") or "glb"), timeout, payload)
        return assets, {"endpoint": endpoint, "task_id": str(task_id), "status_response": self._redact(last)}

    def _generate_generic(self, payload: dict[str, Any], image: Path | None, prompt: str, job_dir: Path, timeout: int, progress: Progress, *, images: list[Path] | None = None, video: Path | None = None) -> tuple[list[Path], dict[str, Any]]:
        endpoint = str(payload.get("endpoint") or "").strip()
        if not endpoint:
            raise ValueError("Generic REST provider requires endpoint.")
        method = str(payload.get("method") or "POST").upper()
        if method not in {"POST", "PUT"}:
            raise ValueError("Generic REST method must be POST or PUT.")
        headers = {str(k): str(v) for k, v in dict(payload.get("headers") or {}).items()}
        api_key = str(payload.get("api_key") or "").strip()
        if api_key and not any(key.lower() in {"authorization", "x-api-key", "api-key"} for key in headers):
            scheme = str(payload.get("auth_scheme") or "Bearer").strip()
            headers["Authorization"] = f"{scheme} {api_key}".strip()
        body = dict(payload.get("request_body") or {})
        image_field = str(payload.get("image_field") or "image")
        images_field = str(payload.get("images_field") or payload.get("multi_image_field") or "images")
        video_field = str(payload.get("video_field") or "video")
        prompt_field = str(payload.get("prompt_field") or "prompt")
        if image:
            body[image_field] = self._data_uri(image) if bool(payload.get("image_as_data_uri", True)) else base64.b64encode(image.read_bytes()).decode("ascii")
        image_list = list(images or [])
        if image_list:
            if bool(payload.get("images_as_paths", False)):
                body[images_field] = [str(p) for p in image_list]
            else:
                body[images_field] = [self._data_uri(p) if bool(payload.get("image_as_data_uri", True)) else base64.b64encode(p.read_bytes()).decode("ascii") for p in image_list]
        if video:
            body[video_field] = self._data_uri(video) if bool(payload.get("video_as_data_uri", True)) else base64.b64encode(video.read_bytes()).decode("ascii")
        if prompt:
            body[prompt_field] = prompt
        for key in ("negative_prompt", "seed", "output_format", "target_formats", "texture", "enable_pbr", "model_id", "api_model_id", "ai_model", "token_profile", "model_context_shrinker", "context_shrinker_model", "provider", "provider_route", "workflow_id", "workflow_json"):
            if key in payload and payload.get(key) not in (None, "") and key not in body:
                body[key] = payload.get(key)
        progress(0.18, "Calling configured 3D REST API")
        response = requests.request(method, endpoint, headers=headers, json=body, timeout=(30, timeout))
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        output_format = str(payload.get("output_format") or "glb").lower().lstrip(".")
        if "application/json" not in content_type:
            output = job_dir / f"generic_result.{output_format}"
            output.write_bytes(response.content)
            return [output], {"endpoint": endpoint, "status_code": response.status_code, "content_type": content_type}
        data = response.json()
        poll_url_path = str(payload.get("poll_url_path") or "")
        status_path = str(payload.get("status_path") or "status")
        result = data
        if poll_url_path:
            poll_value = self._json_path(data, poll_url_path)
            if not poll_value:
                raise RuntimeError(f"poll_url_path {poll_url_path!r} was not found in the API response.")
            poll_url = urljoin(endpoint, str(poll_value))
            deadline = time.monotonic() + timeout
            interval = max(1.0, float(payload.get("poll_interval_seconds") or 5.0))
            success_values = {str(v).lower() for v in (payload.get("success_statuses") or ["succeeded", "success", "completed", "complete"])}
            failure_values = {str(v).lower() for v in (payload.get("failure_statuses") or ["failed", "error", "canceled", "cancelled"])}
            while time.monotonic() < deadline:
                poll = requests.get(poll_url, headers=headers, timeout=(30, 120))
                poll.raise_for_status()
                result = poll.json()
                status = str(self._json_path(result, status_path) or "").lower()
                progress(0.25, f"Generic API task {status or 'processing'}")
                if status in success_values:
                    break
                if status in failure_values:
                    raise RuntimeError(f"Generic API task failed: {result}")
                time.sleep(interval)
            else:
                raise TimeoutError(f"Generic API task did not finish within {timeout} seconds.")
        assets = self._extract_api_assets(result, job_dir, output_format, timeout, payload)
        return assets, {"endpoint": endpoint, "status_code": response.status_code, "response": self._redact(result if isinstance(result, dict) else {"value": result})}

    def _extract_api_assets(self, data: Any, job_dir: Path, output_format: str, timeout: int, payload: dict[str, Any] | None = None) -> list[Path]:
        payload = payload or {}
        values: list[tuple[str, Any]] = []
        configured = str(payload.get("response_url_path") or "")
        if configured:
            values.append((output_format, self._json_path(data, configured)))
        for path, fmt in (
            ("model_url", output_format), ("url", output_format), ("result_url", output_format),
            ("model_urls.glb", "glb"), ("model_urls.fbx", "fbx"), ("model_urls.obj", "obj"),
            ("model_urls.usdz", "usdz"), ("model_urls.stl", "stl"),
            ("result.model_url", output_format), ("result.url", output_format),
            ("result.model_urls.glb", "glb"), ("result.model_urls.fbx", "fbx"),
            ("result.model_urls.obj", "obj"), ("result.model_urls.usdz", "usdz"),
            ("data.model_url", output_format), ("data.url", output_format),
            ("model", output_format), ("result.model", output_format), ("data.model", output_format),
        ):
            values.append((fmt, self._json_path(data, path)))
        assets: list[Path] = []
        seen: set[str] = set()
        for fmt, value in values:
            if not value or not isinstance(value, str) or value in seen:
                continue
            seen.add(value)
            fmt = str(fmt or output_format).lower().lstrip(".")
            destination = job_dir / f"api_result_{len(assets) + 1}.{fmt}"
            if value.startswith(("http://", "https://")):
                assets.append(self._download(value, destination, timeout=timeout))
            elif value.startswith("data:") and ";base64," in value:
                destination.write_bytes(base64.b64decode(value.split(";base64,", 1)[1]))
                assets.append(destination)
            else:
                try:
                    decoded = base64.b64decode(value, validate=True)
                    if decoded:
                        destination.write_bytes(decoded)
                        assets.append(destination)
                except Exception:
                    path = Path(value).expanduser()
                    if path.exists() and path.suffix.lower() in ASSET_EXTENSIONS:
                        assets.append(self._copy_asset(path, job_dir))
        return assets

    def rig(self, payload: dict[str, Any], progress: Progress) -> dict[str, Any]:
        provider = str(payload.get("provider") or "").strip()
        known = {row["key"] for row in self.rigging_providers()}
        if provider not in known:
            raise ValueError(f"Unknown rigging provider: {provider!r}")
        source = self._resolve_asset_input(payload)
        job_dir = self._safe_job_dir(self.rig_root, provider)
        self._write_request(job_dir, payload | {"asset_path": str(source)})
        timeout = int(payload.get("timeout_seconds") or 3600)
        if payload.get("dry_run"):
            plan = self._rig_plan(provider, payload, source, job_dir)
            (job_dir / "dry_run_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
            progress(1.0, "Dry-run rigging plan created")
            return {"ok": True, "dry_run": True, "provider": provider, "job_dir": str(job_dir), "plan": plan, "assets": [], "count": 0}
        if provider == "unirig_local":
            assets, details = self._rig_unirig(payload, source, job_dir, timeout, progress)
        else:
            assets, details = self._rig_blender(payload, source, job_dir, timeout, progress)
        if not assets:
            raise RuntimeError(f"{provider} completed but produced no rigged 3D asset.")
        result = self._finalize(job_dir, provider, payload | {"source_asset": str(source)}, assets, details)
        progress(1.0, "Rigging complete")
        return result

    def _rig_plan(self, provider: str, payload: dict[str, Any], source: Path, job_dir: Path) -> dict[str, Any]:
        if provider == "unirig_local":
            repo = Path(str(payload.get("repo_path") or "<UniRig repo>"))
            return {
                "provider": provider,
                "steps": [
                    ["bash", str(repo / "launch/inference/generate_skeleton.sh"), "--input", str(source), "--output", str(job_dir / "skeleton.fbx")],
                    ["bash", str(repo / "launch/inference/generate_skin.sh"), "--input", str(job_dir / "skeleton.fbx"), "--output", str(job_dir / "skin.fbx")],
                    ["bash", str(repo / "launch/inference/merge.sh"), "--source", str(job_dir / "skin.fbx"), "--target", str(source), "--output", str(job_dir / "rigged.glb")],
                ],
            }
        return {
            "provider": provider,
            "command": [str(payload.get("blender_executable") or "blender"), "--background", "--python", str(self.paths.root / "integrations/blender_scripts/dct_auto_rig.py"), "--", "--input", str(source), "--output", str(job_dir / "rigged.glb")],
        }

    def _rig_unirig(self, payload: dict[str, Any], source: Path, job_dir: Path, timeout: int, progress: Progress) -> tuple[list[Path], dict[str, Any]]:
        repo = self._repo(payload, entry="launch/inference/generate_skeleton.sh")
        shell = str(payload.get("shell_executable") or ("bash" if os.name != "nt" else "wsl"))
        use_wsl = os.name == "nt" and Path(shell).name.lower().startswith("wsl")

        def wsl_path(value: str | Path) -> str:
            """Translate a Windows path before passing it to a WSL-hosted UniRig script."""
            raw = str(value)
            proc = subprocess.run(
                [shell, "wslpath", "-a", "-u", raw],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            converted = proc.stdout.strip()
            if proc.returncode != 0 or not converted:
                raise RuntimeError(f"Could not translate Windows path for WSL: {raw}\n{proc.stdout[-2000:]}")
            return converted

        def cmd(script: Path, *args: str) -> list[str]:
            if use_wsl:
                converted: list[str] = []
                for index, value in enumerate(args):
                    previous = args[index - 1] if index else ""
                    if previous in {"--input", "--output", "--source", "--target"}:
                        converted.append(wsl_path(value))
                    else:
                        converted.append(value)
                return [shell, "bash", wsl_path(script), *converted]
            return [shell, str(script), *args]

        skeleton = job_dir / "skeleton.fbx"
        skin = job_dir / "skin.fbx"
        output_format = str(payload.get("output_format") or "glb").lower().lstrip(".")
        rigged = job_dir / f"rigged.{output_format}"
        logs: list[dict[str, Any]] = []
        skeleton_args = ["--input", str(source), "--output", str(skeleton)]
        if payload.get("seed") is not None:
            skeleton_args += ["--seed", str(int(payload.get("seed") or 0))]
        progress(0.08, "UniRig: predicting skeleton")
        logs.append(self._run(cmd(repo / "launch/inference/generate_skeleton.sh", *skeleton_args), cwd=repo, timeout=timeout, progress=lambda v, m: progress(0.08 + v * 0.25, m)))
        if not bool(payload.get("skeleton_only", False)):
            progress(0.38, "UniRig: predicting skinning weights")
            logs.append(self._run(cmd(repo / "launch/inference/generate_skin.sh", "--input", str(skeleton), "--output", str(skin)), cwd=repo, timeout=timeout, progress=lambda v, m: progress(0.38 + v * 0.25, m)))
            progress(0.68, "UniRig: merging rig and source mesh")
            logs.append(self._run(cmd(repo / "launch/inference/merge.sh", "--source", str(skin), "--target", str(source), "--output", str(rigged)), cwd=repo, timeout=timeout, progress=lambda v, m: progress(0.68 + v * 0.22, m)))
            assets = [rigged] if rigged.exists() else self._asset_candidates(job_dir)
        else:
            assets = [skeleton] if skeleton.exists() else self._asset_candidates(job_dir)
        return assets, {"repo": str(repo), "steps": logs, "skeleton_only": bool(payload.get("skeleton_only", False))}

    def _pose_payload(self, payload: dict[str, Any], job_dir: Path) -> Path | None:
        annotation_id = payload.get("annotation_id")
        media_id = payload.get("media_id")
        annotation: dict[str, Any] | None = None
        if annotation_id:
            annotation = self.reference.get_annotation(int(annotation_id))
        elif media_id:
            rows = self.reference.list_annotations(media_id=int(media_id), limit=500)
            poses = [row for row in rows if str(row.get("annotation_type") or "").lower() in {"pose3d", "animation_pose", "pose2d"}]
            annotation = poses[-1] if poses else None
        explicit = payload.get("pose")
        if explicit:
            data = explicit
        elif annotation:
            data = annotation.get("metadata") or {}
        else:
            return None
        path = job_dir / "pose.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _rig_blender(self, payload: dict[str, Any], source: Path, job_dir: Path, timeout: int, progress: Progress) -> tuple[list[Path], dict[str, Any]]:
        blender = self._resolve_blender_executable(str(payload.get("blender_executable") or ""))
        script = self.paths.root / "integrations" / "blender_scripts" / "dct_auto_rig.py"
        if not script.exists():
            raise FileNotFoundError(f"Bundled Blender auto-rig script not found: {script}")
        output_format = str(payload.get("output_format") or "glb").lower().lstrip(".")
        if output_format not in {"glb", "gltf", "fbx"}:
            output_format = "glb"
        output = job_dir / f"rigged.{output_format}"
        pose = self._pose_payload(payload, job_dir)
        command = [blender, "--background", "--python", str(script), "--", "--input", str(source), "--output", str(output)]
        if pose:
            command += ["--pose-json", str(pose)]
        if bool(payload.get("automatic_weights", True)):
            command.append("--automatic-weights")
        if payload.get("armature_name"):
            command += ["--armature-name", str(payload["armature_name"])]
        details = self._run(command, cwd=self.paths.root, timeout=timeout, progress=progress)
        assets = [output] if output.exists() else self._asset_candidates(job_dir)
        return assets, details | {"pose_json": str(pose) if pose else None}

    def import_asset(self, source_path: str, *, copy: bool = True, label: str = "") -> dict[str, Any]:
        source = Path(source_path).expanduser().resolve()
        if not source.exists() or not source.is_file() or source.suffix.lower() not in ASSET_EXTENSIONS:
            raise ValueError("Select an existing supported 3D asset file.")
        if copy:
            dest = self.import_root / source.name
            if dest.exists():
                dest = self.import_root / f"{source.stem}_{uuid.uuid4().hex[:6]}{source.suffix}"
            shutil.copy2(source, dest)
        else:
            dest = source
        meta = {"provider": "import", "label": label, "source_path": str(source), "created_at": datetime.now(timezone.utc).isoformat()}
        dest.with_suffix(dest.suffix + ".dct.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return self.asset_record(dest)

    def asset_record(self, path: Path) -> dict[str, Any]:
        path = path.resolve()
        sidecar = path.with_suffix(path.suffix + ".dct.json")
        metadata: dict[str, Any] = {}
        if sidecar.exists():
            try:
                metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            except Exception:
                metadata = {}
        stat = path.stat()
        try:
            relative = str(path.relative_to(self.assets_root.resolve())).replace("\\", "/")
        except Exception:
            relative = ""
        return {
            "id": relative or str(path),
            "name": path.name,
            "path": str(path),
            "relative_path": relative,
            "format": path.suffix.lower().lstrip("."),
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "metadata": metadata,
            "download_url": f"/api/three-d/assets/file?path={relative}" if relative else None,
        }

    def list_assets(self, limit: int = 500) -> list[dict[str, Any]]:
        rows = [self.asset_record(path) for path in self._asset_candidates(self.assets_root)]
        return rows[: max(1, min(int(limit), 5000))]

    def asset_path_from_relative(self, relative: str) -> Path:
        if not relative:
            raise ValueError("Asset path is required.")
        root = self.assets_root.resolve()
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Asset path escapes the managed 3D asset directory.") from exc
        if not candidate.exists() or not candidate.is_file() or candidate.suffix.lower() not in ASSET_EXTENSIONS:
            raise FileNotFoundError(str(candidate))
        return candidate

    def open_in_blender(self, payload: dict[str, Any]) -> dict[str, Any]:
        asset = self._resolve_asset_input(payload)
        blender = self._resolve_blender_executable(str(payload.get("blender_executable") or ""))
        script = self.paths.root / "integrations" / "blender_scripts" / "dct_open_asset.py"
        command = [blender]
        if script.exists():
            command += ["--python", str(script), "--", "--input", str(asset)]
        else:
            command.append(str(asset))
        process = subprocess.Popen(command, cwd=str(self.paths.root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "pid": process.pid, "command": command, "asset_path": str(asset)}

    # ------------------------------------------------------------------
    # Browser 3D viewport payloads
    # ------------------------------------------------------------------
    def viewport_modes(self) -> list[dict[str, Any]]:
        return [
            {"key": "shaded", "label": "Shaded solid", "description": "Lightweight shaded mesh view with model-space color."},
            {"key": "wireframe", "label": "Topology / wireframe", "description": "Mesh edges and triangle topology for checking geometry."},
            {"key": "uv_topology", "label": "UV topology", "description": "2D UV islands/triangles when UVs are available."},
            {"key": "normals", "label": "Normals", "description": "Draws face normals from triangle centers."},
            {"key": "bones", "label": "Rig bones", "description": "Armature bones, labels, and groups."},
            {"key": "material", "label": "Material color", "description": "Material-aware browser preview when material names are available."},
            {"key": "rendered", "label": "Rendered preview", "description": "Uses the same payload with material names and optional Blender preview renders."},
        ]

    def _parse_obj_payload(self, path: Path, *, max_vertices: int = 200000, max_faces: int = 200000) -> dict[str, Any]:
        vertices: list[list[float]] = []
        uvs: list[list[float]] = []
        faces: list[list[int]] = []
        uv_faces: list[list[list[float]]] = []
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if line.startswith("v ") and len(vertices) < max_vertices:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                        except Exception:
                            pass
                elif line.startswith("vt "):
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            uvs.append([float(parts[1]), float(parts[2])])
                        except Exception:
                            pass
                elif line.startswith("f ") and len(faces) < max_faces:
                    raw = line.split()[1:]
                    poly: list[int] = []
                    poly_uvs: list[list[float]] = []
                    for part in raw:
                        fields = part.split("/")
                        try:
                            vi = int(fields[0])
                            if vi < 0:
                                vi = len(vertices) + vi + 1
                            poly.append(vi - 1)
                            if len(fields) > 1 and fields[1]:
                                ui = int(fields[1])
                                if ui < 0:
                                    ui = len(uvs) + ui + 1
                                if 0 <= ui - 1 < len(uvs):
                                    poly_uvs.append(uvs[ui - 1])
                        except Exception:
                            continue
                    if len(poly) >= 3:
                        # triangulate fan-style for the viewport
                        for i in range(1, len(poly) - 1):
                            tri = [poly[0], poly[i], poly[i + 1]]
                            if all(0 <= idx < len(vertices) for idx in tri):
                                faces.append(tri)
                                if len(poly_uvs) >= len(poly):
                                    uv_faces.append([poly_uvs[0], poly_uvs[i], poly_uvs[i + 1]])
        return {
            "source_path": str(path),
            "source_format": "obj",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "coordinate_system": "OBJ coordinates",
            "meshes": [{"name": path.stem, "vertices": vertices, "faces": faces, "uvs": uv_faces, "normals": [], "materials": []}],
            "armatures": [],
            "objects": [{"name": path.stem, "type": "MESH"}],
            "truncated": len(vertices) >= max_vertices or len(faces) >= max_faces,
        }

    def prepare_viewer_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        source_value = str(payload.get("asset_path") or payload.get("path") or payload.get("input_path") or "").strip()
        if not source_value:
            raise ValueError("Select or enter a 3D asset path first.")
        source = Path(source_value).expanduser().resolve()
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(str(source))
        if source.suffix.lower() not in ASSET_EXTENSIONS | {".blend", ".dae", ".3ds", ".abc", ".bvh", ".x3d"}:
            raise ValueError(f"Unsupported 3D viewport format: {source.suffix}")
        job_dir = self._safe_job_dir(self.viewport_root, "viewport")
        viewer_json = job_dir / "viewer_payload.json"
        max_vertices = int(payload.get("max_vertices") or 200000)
        max_faces = int(payload.get("max_faces") or 200000)
        blender = str(payload.get("blender_executable") or payload.get("blender") or "").strip()
        details: dict[str, Any] = {"method": ""}
        if source.suffix.lower() == ".obj" and not bool(payload.get("force_blender", False)):
            data = self._parse_obj_payload(source, max_vertices=max_vertices, max_faces=max_faces)
            viewer_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            details["method"] = "direct_obj_parser"
        else:
            blender = self._resolve_blender_executable(blender)
            script = self.paths.root / "integrations" / "blender_scripts" / "dct_export_viewer_payload.py"
            if not script.exists():
                raise FileNotFoundError(f"Bundled Blender viewport exporter missing: {script}")
            command = [blender, "--background", "--factory-startup", "--python", str(script), "--", "--input", str(source), "--output", str(viewer_json), "--max-vertices", str(max_vertices), "--max-faces", str(max_faces)]
            proc = subprocess.run(command, cwd=str(self.paths.root), text=True, capture_output=True, timeout=int(payload.get("timeout_seconds") or 300), check=False)
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            (job_dir / "blender_viewport_stdout.log").write_text(stdout, encoding="utf-8", errors="ignore")
            (job_dir / "blender_viewport_stderr.log").write_text(stderr, encoding="utf-8", errors="ignore")
            details = {"method": "blender_exporter", "command": command, "returncode": proc.returncode, "stdout": stdout[-20000:], "stderr": stderr[-20000:], "stdout_log": str(job_dir / "blender_viewport_stdout.log"), "stderr_log": str(job_dir / "blender_viewport_stderr.log")}
            if proc.returncode != 0:
                raise RuntimeError(f"Blender viewport export failed. Use blender.exe, not blender-launcher.exe.\n{details['stderr'] or details['stdout']}")
            if not viewer_json.exists():
                raise RuntimeError(
                    "Blender completed but did not produce a viewport payload JSON. "
                    "Use the real blender.exe rather than blender-launcher.exe and check the saved stdout/stderr logs in the generated viewport job folder.\n"
                    f"Command: {command}\nStdout tail:\n{stdout[-4000:]}\nStderr tail:\n{stderr[-4000:]}"
                )
        try:
            data = json.loads(viewer_json.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        return {
            "ok": True,
            "source_path": str(source),
            "viewer_payload_path": str(viewer_json),
            "viewer_payload_url": f"/api/three-d/viewport/file?path={viewer_json}",
            "mode_options": self.viewport_modes(),
            "mesh_count": len(data.get("meshes") or []),
            "armature_count": len(data.get("armatures") or []),
            "object_count": len(data.get("objects") or []),
            "truncated": bool(data.get("truncated")),
            "details": details,
            "payload": data if bool(payload.get("include_payload", True)) else {},
        }

    def viewer_payload_from_path(self, path: str) -> Path:
        candidate = Path(path).expanduser().resolve()
        root = self.viewport_root.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Viewport payload path escapes the managed viewer directory.") from exc
        if not candidate.exists() or not candidate.is_file() or candidate.name != "viewer_payload.json":
            raise FileNotFoundError(str(candidate))
        return candidate


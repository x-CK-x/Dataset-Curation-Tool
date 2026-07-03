from __future__ import annotations

"""Bidirectional ComfyUI bridge for Data Curation Tool.

This module intentionally exposes neutral Data Curation Tool names only.  It
reuses the metadata extraction capabilities that originated in the uploaded
metadata-toolkit code, but it does not expose the old custom-node names or
prefixes in the application UI, API, generated workflows, or install package.
"""

import base64
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..paths import AppPaths
from .media_service import MediaService
from .metadata_service import MetadataService
from .tag_service import TagService

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".gif"}


class ComfyBridgeService:
    def __init__(self, paths: AppPaths, media: MediaService, metadata: MetadataService, tags: TagService):
        self.paths = paths
        self.media = media
        self.metadata = metadata
        self.tags = tags
        self.root = paths.outputs / "comfy_bridge"
        self.inbox = self.root / "inbox"
        self.outbox = self.root / "outbox"
        self.workflows = self.root / "workflows"
        self.packages = paths.root / "integrations"
        for folder in (self.root, self.inbox, self.outbox, self.workflows, self.packages):
            folder.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict[str, Any]:
        package = self.packages / "data_curation_tool_comfyui_nodes.zip"
        return {
            "ok": True,
            "bridge_name": "Data Curation Tool ComfyUI Bridge",
            "api_base": "http://127.0.0.1:7865/api/comfy",
            "package_exists": package.exists(),
            "package_path": str(package),
            "inbox": str(self.inbox),
            "outbox": str(self.outbox),
            "supported": {
                "metadata": ["A1111", "ComfyUI workflow/prompt", "NovelAI", "Fooocus/Civitai/Invoke-style JSON", "EXIF/PIL", "video metadata", "safetensors LoRA headers"],
                "media_push": ["image", "video", "mask", "metadata_json", "tag_string", "caption"],
                "roundtrip": ["send selected media to ComfyUI", "receive generated image/video/mask", "import metadata", "apply tags/captions"],
            },
            "name_policy": "Old node prefixes are not used in the DCT UI, API, workflows, or node package.",
        }

    def save_incoming_media(self, *, filename: str, data: bytes | None = None, source_path: str = "", metadata: dict[str, Any] | None = None, import_to_dataset: bool = False, dataset_id: int | None = None) -> dict[str, Any]:
        if not filename and source_path:
            filename = Path(source_path).name
        safe_name = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in (filename or f"comfy_{uuid.uuid4().hex}.png")).strip() or f"comfy_{uuid.uuid4().hex}.png"
        dest = self.inbox / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{safe_name}"
        if data is not None:
            dest.write_bytes(data)
        elif source_path:
            src = Path(source_path).expanduser().resolve()
            if not src.exists() or not src.is_file():
                raise FileNotFoundError(str(src))
            shutil.copy2(src, dest)
        else:
            raise ValueError("Provide file bytes, base64 data, or source_path.")
        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "filename": filename,
            "path": str(dest),
            "source_path": source_path,
            "metadata": metadata or {},
        }
        manifest_path = dest.with_suffix(dest.suffix + ".dct.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        media_id = None
        if import_to_dataset:
            # Import through the normal media/indexing path.  The caller can then
            # run standard metadata extraction/tag application if desired.
            record = self.media.add_media(Path(dest), dataset_id=dataset_id) if hasattr(self.media, "add_media") else None
            media_id = record.get("id") if isinstance(record, dict) else None
        return {"ok": True, "path": str(dest), "manifest": str(manifest_path), "media_id": media_id, "metadata": manifest}

    def receive_json_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        data_b64 = str(payload.get("data_base64") or "").strip()
        data: bytes | None = None
        if data_b64:
            if "," in data_b64 and data_b64.split(",", 1)[0].startswith("data:"):
                data_b64 = data_b64.split(",", 1)[1]
            data = base64.b64decode(data_b64)
        return self.save_incoming_media(
            filename=str(payload.get("filename") or payload.get("name") or "comfy_output.png"),
            data=data,
            source_path=str(payload.get("source_path") or ""),
            metadata=dict(payload.get("metadata") or {}),
            import_to_dataset=bool(payload.get("import_to_dataset", False)),
            dataset_id=payload.get("dataset_id"),
        )

    def media_package(self, media_id: int, *, include_metadata: bool = True) -> dict[str, Any]:
        item = self.media.get(int(media_id))
        if not item:
            raise FileNotFoundError(f"Unknown media_id={media_id}")
        src = Path(item.path).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(str(src))
        dest = self.outbox / f"media_{media_id}_{src.name}"
        shutil.copy2(src, dest)
        payload: dict[str, Any] = {
            "media_id": media_id,
            "source_path": str(src),
            "handoff_path": str(dest),
            "tags": list(getattr(item, "tags", []) or []),
            "caption": getattr(item, "caption", "") or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if include_metadata:
            try:
                payload["metadata"] = self.metadata.extract_media(media_id, include_raw=True, persist=True)
            except Exception as exc:
                payload["metadata_error"] = str(exc)
        manifest = dest.with_suffix(dest.suffix + ".dct.json")
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["manifest_path"] = str(manifest)
        return payload

    def workflow_templates(self) -> dict[str, Any]:
        templates = {
            "extract_metadata_from_load_image": {
                "name": "DCT Metadata Extractor from Load Image",
                "description": "Recovers metadata from a ComfyUI image path and sends normalized prompts/tags back to the DCT API.",
                "api_base": "http://127.0.0.1:7865/api/comfy",
                "nodes": ["DCT Metadata Extractor", "DCT Send Media", "DCT Text Preview"],
            },
            "send_generated_image_to_dct": {
                "name": "Send generated image/video/mask to DCT",
                "description": "Pushes a finished output file and sidecar metadata into the DCT inbox.",
                "api_base": "http://127.0.0.1:7865/api/comfy",
                "nodes": ["DCT Send Media", "DCT Send Metadata"],
            },
            "receive_dct_media": {
                "name": "Receive selected DCT media in ComfyUI",
                "description": "Loads a handoff manifest created by DCT so a workflow can reuse selected media, tags, masks, or metadata.",
                "api_base": "http://127.0.0.1:7865/api/comfy",
                "nodes": ["DCT Receive Media Package", "DCT Metadata Field"],
            },
        }
        out = self.workflows / "dct_comfy_workflow_templates.json"
        out.write_text(json.dumps(templates, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"templates": templates, "path": str(out)}

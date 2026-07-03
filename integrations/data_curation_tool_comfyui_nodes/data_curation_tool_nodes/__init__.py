from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

try:
    import requests
except Exception:  # ComfyUI will show install error in node output instead.
    requests = None


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    if requests is None:
        return {"ok": False, "error": "Install requests in the ComfyUI environment."}
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _get_json(url: str) -> dict[str, Any]:
    if requests is None:
        return {"ok": False, "error": "Install requests in the ComfyUI environment."}
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


class DCTHealthCheck:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status_json",)
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"api_base": ("STRING", {"default": "http://127.0.0.1:7865/api/comfy"})}}

    def run(self, api_base: str):
        try:
            return (json.dumps(_get_json(api_base.rstrip('/') + '/status'), indent=2),)
        except Exception as exc:
            return (json.dumps({"ok": False, "error": str(exc)}, indent=2),)


class DCTSendMedia:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("response_json", "saved_path")
    FUNCTION = "send"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"api_base": ("STRING", {"default": "http://127.0.0.1:7865/api/comfy"}), "source_path": ("STRING", {"default": ""}), "metadata_json": ("STRING", {"default": "{}", "multiline": True}), "import_to_dataset": ("BOOLEAN", {"default": False})}}

    def send(self, api_base: str, source_path: str, metadata_json: str = "{}", import_to_dataset: bool = False):
        try:
            meta = json.loads(metadata_json or "{}")
        except Exception:
            meta = {"raw_metadata_text": metadata_json}
        payload = {"source_path": source_path, "filename": Path(source_path).name, "metadata": meta, "import_to_dataset": import_to_dataset}
        try:
            response = _post_json(api_base.rstrip('/') + '/receive', payload)
            return (json.dumps(response, indent=2), response.get("path", ""))
        except Exception as exc:
            return (json.dumps({"ok": False, "error": str(exc)}, indent=2), "")


class DCTReceiveMediaPackage:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("source_path", "tag_string", "metadata_json")
    FUNCTION = "receive"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"manifest_path": ("STRING", {"default": ""})}}

    def receive(self, manifest_path: str):
        try:
            data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
            return (data.get("handoff_path") or data.get("source_path") or "", ", ".join(data.get("tags") or []), json.dumps(data.get("metadata") or data, indent=2))
        except Exception as exc:
            return ("", "", json.dumps({"ok": False, "error": str(exc)}, indent=2))


class DCTMetadataExtractor:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("metadata_json", "positive_prompt", "negative_prompt", "tag_string")
    FUNCTION = "extract"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"api_base": ("STRING", {"default": "http://127.0.0.1:7865/api/comfy"}), "source_path": ("STRING", {"default": ""})}}

    def extract(self, api_base: str, source_path: str):
        try:
            response = _post_json(api_base.rstrip('/') + '/metadata/extract', {"source_path": source_path, "filename": Path(source_path).name})
            meta = response.get("metadata") or {}
            return (json.dumps(meta, indent=2), meta.get("positive_prompt", ""), meta.get("negative_prompt", ""), meta.get("tag_string", ""))
        except Exception as exc:
            return (json.dumps({"ok": False, "error": str(exc)}, indent=2), "", "", "")


class DCTMetadataField:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    FUNCTION = "field"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"metadata_json": ("STRING", {"default": "{}", "multiline": True}), "path": ("STRING", {"default": "positive_prompt"}), "default": ("STRING", {"default": ""})}}

    def field(self, metadata_json: str, path: str, default: str = ""):
        try:
            data = json.loads(metadata_json or "{}")
            cur = data
            for part in path.replace("$.", "").split('.'):
                if not part:
                    continue
                if isinstance(cur, dict):
                    cur = cur.get(part, default)
                else:
                    return (default,)
            return (json.dumps(cur, ensure_ascii=False) if isinstance(cur, (dict, list)) else str(cur),)
        except Exception:
            return (default,)


class DCTSendMetadata:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response_json",)
    FUNCTION = "send"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"api_base": ("STRING", {"default": "http://127.0.0.1:7865/api/comfy"}), "filename": ("STRING", {"default": "metadata.json"}), "metadata_json": ("STRING", {"default": "{}", "multiline": True})}}

    def send(self, api_base: str, filename: str, metadata_json: str):
        try:
            meta = json.loads(metadata_json or "{}")
            response = _post_json(api_base.rstrip('/') + '/receive', {"filename": filename, "metadata": meta})
            return (json.dumps(response, indent=2),)
        except Exception as exc:
            return (json.dumps({"ok": False, "error": str(exc)}, indent=2),)


class DCTTextPreview:
    CATEGORY = "Data Curation Tool/Bridge"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "preview"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": ("STRING", {"default": "", "multiline": True}), "title": ("STRING", {"default": "DCT Preview"})}}

    def preview(self, text: str, title: str = "DCT Preview"):
        return (f"{title}\n{'=' * len(title)}\n{text}",)


NODE_CLASS_MAPPINGS = {
    "DCTHealthCheck": DCTHealthCheck,
    "DCTSendMedia": DCTSendMedia,
    "DCTReceiveMediaPackage": DCTReceiveMediaPackage,
    "DCTMetadataExtractor": DCTMetadataExtractor,
    "DCTMetadataField": DCTMetadataField,
    "DCTSendMetadata": DCTSendMetadata,
    "DCTTextPreview": DCTTextPreview,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "DCTHealthCheck": "DCT Health Check",
    "DCTSendMedia": "DCT Send Media",
    "DCTReceiveMediaPackage": "DCT Receive Media Package",
    "DCTMetadataExtractor": "DCT Metadata Extractor",
    "DCTMetadataField": "DCT Metadata Field",
    "DCTSendMetadata": "DCT Send Metadata",
    "DCTTextPreview": "DCT Text Preview",
}

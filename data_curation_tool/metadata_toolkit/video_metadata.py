from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .image_metadata import SCHEMA_VERSION, comfy_prompt_to_image_metadata, parse_a1111_parameters, parse_comfy_prompt, parse_json_comment
from .security import file_stat, json_dumps, safe_json_loads, truncate_text
from .text_utils import coerce_float, coerce_int


def _fps(v: str) -> float:
    try:
        if not v or v == "0/0":
            return 0.0
        if "/" in v:
            a, b = v.split("/", 1)
            return float(a) / float(b)
        return float(v)
    except Exception:
        return 0.0


def _generation_from_tags(tags: dict[str, Any]) -> dict[str, Any]:
    for k, v in (tags or {}).items():
        key = str(k).lower()
        text = v if isinstance(v, str) else json_dumps(v, False)
        parsed = safe_json_loads(text, default=None)
        if key == "prompt" and isinstance(parsed, dict):
            return {"source_app": "ComfyUI video tag", "normalized": parse_comfy_prompt(parsed)}
        if isinstance(parsed, dict) and ("prompt" in parsed or "negativePrompt" in parsed or "steps" in parsed or "cfg" in parsed):
            return {"source_app": "Video JSON metadata", "normalized": parse_json_comment(parsed, 0, 0, "Video JSON metadata")}
        if "Steps:" in str(text) or "Negative prompt:" in str(text):
            return {"source_app": "A1111 video tag", "normalized": parse_a1111_parameters(str(text))}
    return {"source_app": "Unknown/Generic", "normalized": {}}


def probe_video(path: Path, use_ffprobe: bool = True, timeout_seconds: int = 20, parse_generation_metadata: bool = True) -> dict[str, Any]:
    path = Path(path).resolve()
    out = {
        "schema_version": SCHEMA_VERSION,
        "type": "video_metadata",
        "file": file_stat(path),
        "status": "ok",
        "probe_tool": "none",
        "format": {},
        "streams": [],
        "normalized": {
            "duration_seconds": 0.0,
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "codec": "",
            "frame_count": 0,
            "tags": {},
            "generation": {},
        },
        "safety": {"shell_used": False, "network_used": False, "ffprobe_timeout_seconds": int(timeout_seconds)},
        "raw": {},
    }
    ffprobe = shutil.which("ffprobe") if use_ffprobe else None
    if not ffprobe:
        out["status"] = "ffprobe_not_available"
        out["raw"] = {"note": "Install ffmpeg/ffprobe and ensure ffprobe is on PATH for full video metadata."}
        return out
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    try:
        c = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False, timeout=max(1, int(timeout_seconds)), check=False)
    except subprocess.TimeoutExpired:
        out["status"] = "ffprobe_timeout"
        return out
    except Exception as e:
        out["status"] = "ffprobe_error"
        out["raw"] = {"error": str(e)}
        return out
    if c.returncode != 0:
        out["status"] = "ffprobe_failed"
        out["raw"] = {"stderr": truncate_text(c.stderr, 8000)}
        return out
    data = safe_json_loads(c.stdout, default={})
    if not isinstance(data, dict):
        out["status"] = "ffprobe_invalid_json"
        return out
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    video = next((s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"), {})
    tags: dict[str, Any] = {}
    for obj in (fmt, video):
        if isinstance(obj, dict) and isinstance(obj.get("tags"), dict):
            tags.update(obj.get("tags") or {})
    out.update({"probe_tool": "ffprobe", "format": fmt, "streams": streams, "raw": data})
    nb_frames = coerce_int(video.get("nb_frames", 0), 0)
    out["normalized"].update(
        {
            "duration_seconds": coerce_float(fmt.get("duration", 0.0)),
            "width": coerce_int(video.get("width", 0)),
            "height": coerce_int(video.get("height", 0)),
            "fps": _fps(video.get("avg_frame_rate", "")),
            "codec": str(video.get("codec_name", "")),
            "frame_count": nb_frames,
            "tags": tags,
        }
    )
    if parse_generation_metadata:
        out["normalized"]["generation"] = _generation_from_tags(tags)
    return out


def tensor_video_metadata(width: int, height: int, frame_count: int = 1, channels: int = 3, fps: float = 0.0, prompt_obj: Any = None) -> dict[str, Any]:
    generation: dict[str, Any] = {}
    if isinstance(prompt_obj, dict) and prompt_obj:
        generation = comfy_prompt_to_image_metadata(prompt_obj, width, height, source="Current ComfyUI prompt graph for frame batch")
    return {
        "schema_version": SCHEMA_VERSION,
        "type": "video_metadata",
        "source_app": "ComfyUI IMAGE batch / frame tensor",
        "status": "tensor_only_no_container_metadata",
        "probe_tool": "tensor_shape",
        "format": {},
        "streams": [],
        "normalized": {
            "duration_seconds": (float(frame_count) / float(fps)) if fps else 0.0,
            "width": int(width),
            "height": int(height),
            "fps": float(fps),
            "codec": "tensor_frames",
            "frame_count": int(frame_count),
            "channels": int(channels),
            "tags": {},
            "generation": generation,
        },
        "safety": {"shell_used": False, "network_used": False},
        "raw": {"note": "Frame tensors do not include container/EXIF/PNG metadata. Provide a video file path for full container metadata."},
    }


def metadata_to_text(data: dict[str, Any]) -> str:
    n = data.get("normalized", {})
    gen = n.get("generation", {}) if isinstance(n.get("generation"), dict) else {}
    return "\n".join(
        [
            f"File: {data.get('file',{}).get('name','')}",
            f"Status: {data.get('status','')}",
            f"Duration: {n.get('duration_seconds',0)}",
            f"Video: {n.get('width',0)}x{n.get('height',0)} @ {n.get('fps',0)} fps codec={n.get('codec','')} frames={n.get('frame_count',0)}",
            "",
            "Tags:",
            json_dumps(n.get("tags", {})),
            "",
            "Generation:",
            json_dumps(gen),
            "",
            "Raw JSON:",
            json_dumps(data),
        ]
    )

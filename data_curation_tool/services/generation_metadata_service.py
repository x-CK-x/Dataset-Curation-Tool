from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import ExifTags, Image

from ..database import Database, now_iso
from ..utils import classify_media, normalize_tag, parse_tag_string, tag_string, write_text
from .media_service import MediaService
from .tag_service import TagService

LORA_RE = re.compile(r"<\s*lora\s*:\s*([^:>]+?)\s*(?::\s*([-+]?\d*\.?\d+))?(?::[^>]*)?>", re.I)
SETTING_SPLIT_RE = re.compile(r",\s+(?=[A-Za-z][A-Za-z0-9 _/()\-]+:\s*)")


def _safe_json_loads(value: Any, default: Any = None) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return str(value)


def _decode_user_comment(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if not isinstance(value, (bytes, bytearray)):
        return str(value)
    data = bytes(value)
    payloads = [data[8:], data] if len(data) > 8 else [data]
    for payload in payloads:
        for enc in ("utf-16", "utf-16-be", "utf-16-le", "utf-8", "latin-1"):
            try:
                text = payload.decode(enc, errors="strict").strip("\x00\ufeff ")
                if text and sum(ch.isprintable() for ch in text) / max(1, len(text)) > 0.70:
                    return text
            except Exception:
                continue
    return data.decode("utf-8", errors="replace")


def _truncate(value: Any, limit: int = 200_000) -> str:
    try:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    return text if len(text) <= limit else text[:limit] + "…[truncated]"


def _split_settings_line(raw: str) -> dict[str, str]:
    text = (raw or "").strip().lstrip(",").strip()
    if not text:
        return {}
    result: dict[str, str] = {}
    for part in SETTING_SPLIT_RE.split(text):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip()
        if key and key not in result:
            result[key] = value.strip()
    return result


def _first(data: dict[str, Any], keys: Iterable[str], default: Any = "") -> Any:
    lowered = {str(k).lower().replace(" ", "_").replace("-", "_"): v for k, v in data.items()}
    for key in keys:
        if key in data and data[key] not in (None, "", "None"):
            return data[key]
        normalized = str(key).lower().replace(" ", "_").replace("-", "_")
        if normalized in lowered and lowered[normalized] not in (None, "", "None"):
            return lowered[normalized]
    return default


def _coerce_metadata_object(value: Any) -> dict[str, Any]:
    data = _safe_json_loads(value, value) if isinstance(value, str) else value
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        result: dict[str, Any] = {}
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                result[f"item_{idx}"] = item
                continue
            key = item.get("label") or item.get("name") or item.get("key") or item.get("title") or item.get("field")
            val = item.get("value")
            if val is None:
                val = item.get("text") if item.get("text") is not None else item.get("content")
            result[str(key) if key else f"item_{idx}"] = val
        if result:
            result.setdefault("_raw_items", data)
            return result
    return {}


def _json_from_text(raw: str) -> Any:
    parsed = _safe_json_loads(raw, None)
    if parsed is not None:
        return parsed
    text = str(raw or "")
    starts = [idx for idx, ch in enumerate(text) if ch in "{["]
    for start in starts[:30]:
        for end in range(len(text), start, -1):
            snippet = text[start:end].strip()
            if not snippet or snippet[-1:] not in "}]":
                continue
            parsed = _safe_json_loads(snippet, None)
            if isinstance(parsed, (dict, list)):
                return parsed
            if len(snippet) > 2_000_000:
                break
    return None


def _clean_lora_name(name: str) -> str:
    base = str(name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if "." in base and base.rsplit(".", 1)[0]:
        base = base.rsplit(".", 1)[0]
    return base


def extract_lora_references(prompt: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for match in LORA_RE.finditer(prompt or ""):
        try:
            weight = float(match.group(2)) if match.group(2) not in (None, "") else 1.0
        except Exception:
            weight = 1.0
        name = _clean_lora_name(match.group(1))
        key = (name, str(weight))
        if name and key not in seen:
            refs.append({"raw": match.group(0), "name": name, "weight": weight, "start": match.start(), "end": match.end()})
            seen.add(key)
    return refs


def _strip_lora_references(prompt: str) -> str:
    text = LORA_RE.sub("", prompt or "")
    text = re.sub(r"\s*,\s*,+", ",", text)
    text = re.sub(r"(^\s*,\s*)|(\s*,\s*$)", "", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _prompt_to_tags(prompt: str) -> list[str]:
    text = _strip_lora_references(prompt)
    tags: list[str] = []
    for raw in re.split(r"[,;\n]+", text):
        item = raw.strip().strip('"\'')
        if not item:
            continue
        if ":" in item and re.match(r"^[A-Za-z][A-Za-z0-9 _/()\-]{1,40}:\s*", item):
            continue
        item = re.sub(r"^[({\[]+|[)}\]]+$", "", item)
        tag = normalize_tag(item)
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _looks_like_comfy_prompt(obj: Any) -> bool:
    if isinstance(obj, str):
        obj = _safe_json_loads(obj, None)
    return isinstance(obj, dict) and any(isinstance(v, dict) and ("class_type" in v or "inputs" in v) for v in obj.values())


def parse_a1111_parameters(raw: str, width: int = 0, height: int = 0) -> dict[str, Any]:
    text = str(raw or "").replace("\r\n", "\n")
    positive = text
    negative = ""
    settings_line = ""
    if "Negative prompt:" in text:
        positive, rest = text.split("Negative prompt:", 1)
        if "Steps:" in rest:
            negative, settings_line = rest.split("Steps:", 1)
            settings_line = "Steps:" + settings_line
        else:
            negative = rest
    elif "Steps:" in text:
        positive, settings_line = text.split("Steps:", 1)
        settings_line = "Steps:" + settings_line
    settings = _split_settings_line(settings_line)
    size = settings.get("Size") or settings.get("size") or ""
    if size and "x" in size.lower():
        try:
            w, h = re.split("x", size.lower(), maxsplit=1)
            width, height = int(float(w.strip())), int(float(h.strip()))
        except Exception:
            pass
    return _normalized("Automatic1111 / compatible parameters", positive, negative, settings, width, height)


def parse_comfy_prompt(prompt_obj: Any, width: int = 0, height: int = 0) -> dict[str, Any]:
    prompt = _safe_json_loads(prompt_obj, {})
    if not isinstance(prompt, dict):
        return {}
    positives: list[str] = []
    negatives: list[str] = []
    loras: list[dict[str, Any]] = []
    models: list[str] = []
    samplers: list[dict[str, Any]] = []
    for node_id, node in prompt.items():
        if not isinstance(node, dict):
            continue
        cls = str(node.get("class_type") or node.get("type") or "")
        inputs = node.get("inputs") or {}
        low = cls.lower()
        if "cliptextencode" in low or low.endswith("text"):
            text = inputs.get("text")
            if isinstance(text, str) and text.strip():
                is_negative = any(
                    isinstance(other, dict)
                    and isinstance((other.get("inputs") or {}).get("negative"), list)
                    and str((other.get("inputs") or {}).get("negative", [""])[0]) == str(node_id)
                    for other in prompt.values()
                )
                (negatives if is_negative else positives).append(text.strip())
        if "loraloader" in low or ("lora" in low and "loader" in low):
            name = inputs.get("lora_name") or inputs.get("name")
            if name:
                loras.append({"name": _clean_lora_name(str(name)), "raw_name": str(name), "strength_model": inputs.get("strength_model"), "strength_clip": inputs.get("strength_clip"), "source": cls})
        if "checkpoint" in low or "ckpt" in low:
            name = inputs.get("ckpt_name") or inputs.get("model_name") or inputs.get("model")
            if name:
                models.append(str(name))
        if "sampler" in low:
            samplers.append({k: _jsonable(v) for k, v in inputs.items() if k in {"steps", "cfg", "sampler_name", "scheduler", "seed", "denoise"}})
        if "emptylatentimage" in low:
            try:
                width = int(inputs.get("width") or width or 0)
                height = int(inputs.get("height") or height or 0)
            except Exception:
                pass
    norm = _normalized("ComfyUI prompt/workflow", ", ".join(positives), ", ".join(negatives), {"samplers": samplers, "models": models}, width, height)
    norm["lora_references"] = loras or norm.get("lora_references", [])
    return norm


def parse_json_comment(comment: Any, width: int = 0, height: int = 0, source: str = "JSON metadata") -> dict[str, Any]:
    data = _coerce_metadata_object(comment)
    for wrapper in ("meta", "metadata", "generation", "generation_data", "generationData", "sui_image_params"):
        if isinstance(data.get(wrapper), dict):
            nested = dict(data.get(wrapper) or {})
            nested.update({k: v for k, v in data.items() if k not in nested})
            data = nested
            break
    if _looks_like_comfy_prompt(data):
        return parse_comfy_prompt(data, width, height)
    positive = _first(data, ("prompt", "positive", "positive_prompt", "description", "caption", "text", "v4_prompt"), "")
    negative = _first(data, ("negative_prompt", "negativePrompt", "uc", "undesired_content", "negative"), "")
    tags_value = _first(data, ("tags", "tag_string", "prompt_tags", "labels"), "")
    tags = parse_tag_string(tags_value) if tags_value else _prompt_to_tags(str(positive))
    try:
        width = int(_first(data, ("width", "image_width"), width) or 0)
        height = int(_first(data, ("height", "image_height"), height) or 0)
    except Exception:
        pass
    settings = {k: _jsonable(v) for k, v in data.items() if str(k).lower() not in {"prompt", "positive", "positive_prompt", "negative_prompt", "negativeprompt", "uc", "caption", "text", "tags", "tag_string", "labels"}}
    norm = _normalized(source, positive, negative, settings, width, height)
    if tags:
        norm["tags"] = tags
    if not norm.get("caption") and str(positive).strip() and len(tags) < 3:
        norm["caption"] = str(positive).strip()
    return norm


def _normalized(source: str, positive: Any = "", negative: Any = "", settings: dict[str, Any] | None = None, width: int = 0, height: int = 0) -> dict[str, Any]:
    settings = settings or {}
    positive_s = str(positive or "").strip()
    negative_s = str(negative or "").strip()
    return {
        "source_app": source,
        "width": int(width or 0),
        "height": int(height or 0),
        "positive_prompt": positive_s,
        "negative_prompt": negative_s,
        "caption": str(_first(settings, ("caption", "description", "text"), "") or ""),
        "settings": _jsonable(settings),
        "tags": _prompt_to_tags(positive_s),
        "negative_tags": _prompt_to_tags(negative_s),
        "lora_references": extract_lora_references(positive_s + ", " + negative_s),
    }


@dataclass
class MetadataApplyResult:
    media_id: int | None
    tags: list[str]
    caption: str
    source_app: str


class GenerationMetadataService:
    def __init__(self, db: Database, media_service: MediaService, tag_service: TagService):
        self.db = db
        self.media = media_service
        self.tags = tag_service
        self.ensure_tables()

    def ensure_tables(self) -> None:
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS media_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
                path TEXT NOT NULL,
                media_type TEXT NOT NULL DEFAULT 'unknown',
                source_app TEXT NOT NULL DEFAULT 'Unknown',
                positive_prompt TEXT NOT NULL DEFAULT '',
                negative_prompt TEXT NOT NULL DEFAULT '',
                tag_string TEXT NOT NULL DEFAULT '',
                caption TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(media_id, path)
            )"""
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_media_metadata_media ON media_metadata(media_id)")

    def latest(self, media_id: int) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM media_metadata WHERE media_id=? ORDER BY updated_at DESC LIMIT 1", (media_id,))
        if not row:
            return None
        payload = _safe_json_loads(row.get("payload_json"), {}) or {}
        return {**row, "payload": payload}

    def extract_for_media(self, media_id: int, include_raw: bool = False) -> dict[str, Any]:
        item = self.media.get(media_id)
        if not item:
            raise FileNotFoundError(f"Media not found: {media_id}")
        payload = self.extract_path(Path(item.path), include_raw=include_raw)
        payload["media_id"] = media_id
        self.record_metadata(media_id, Path(item.path), payload)
        return payload

    def extract_path(self, path: Path, include_raw: bool = False) -> dict[str, Any]:
        path = Path(path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(str(path))
        kind = classify_media(path)
        if kind in {"image", "animation"}:
            return self.extract_image(path, include_raw=include_raw)
        if kind == "video":
            return self.extract_video(path, include_raw=include_raw)
        return self.extract_generic(path, include_raw=include_raw)

    def extract_image(self, path: Path, include_raw: bool = False) -> dict[str, Any]:
        info: dict[str, Any] = {}
        exif: dict[str, Any] = {}
        width = height = 0
        with Image.open(path) as img:
            width, height = img.width, img.height
            info = {str(k): _jsonable(v) for k, v in (img.info or {}).items()}
            try:
                for k, v in img.getexif().items():
                    tag = ExifTags.TAGS.get(k, str(k))
                    exif[tag] = _decode_user_comment(v) if tag == "UserComment" else _jsonable(v)
            except Exception as exc:
                exif["_error"] = str(exc)
        raw_sources: list[tuple[str, Any]] = []
        for key in ("parameters", "prompt", "workflow", "Comment", "comment", "Description", "description", "UserComment", "XML:com.adobe.xmp"):
            if key in info:
                raw_sources.append((key, info[key]))
            if key in exif:
                raw_sources.append((key, exif[key]))
        normalized: dict[str, Any] = {}
        source = "Unknown / generic image metadata"
        if info.get("parameters") or exif.get("parameters"):
            normalized = parse_a1111_parameters(str(info.get("parameters") or exif.get("parameters") or ""), width, height)
        elif info.get("prompt") and _looks_like_comfy_prompt(info.get("prompt")):
            normalized = parse_comfy_prompt(info.get("prompt"), width, height)
        elif info.get("workflow") and _looks_like_comfy_prompt(info.get("workflow")):
            normalized = parse_comfy_prompt(info.get("workflow"), width, height)
        else:
            for key, value in raw_sources:
                parsed = _json_from_text(str(value or "")) if isinstance(value, str) else _safe_json_loads(value, None)
                if isinstance(parsed, (dict, list)):
                    label = "NovelAI / JSON image metadata" if isinstance(parsed, dict) and ("uc" in parsed or "signed_hash" in parsed or "v4_prompt" in parsed) else "JSON image metadata"
                    normalized = parse_json_comment(parsed, width, height, label)
                    break
                if isinstance(value, str) and ("Negative prompt:" in value or "Steps:" in value):
                    normalized = parse_a1111_parameters(value, width, height)
                    break
        if not normalized:
            normalized = parse_json_comment({**info, **exif}, width, height, source)
        source = normalized.get("source_app") or source
        return self._result(path, "image", source, normalized, {"png_info": info, "exif": exif} if include_raw else {})

    def extract_video(self, path: Path, include_raw: bool = False) -> dict[str, Any]:
        ffprobe = shutil.which("ffprobe")
        fmt: dict[str, Any] = {}
        streams: list[Any] = []
        tags: dict[str, Any] = {}
        status = "ffprobe_not_available"
        if ffprobe:
            cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False, timeout=30, check=False)
            if proc.returncode == 0:
                data = _safe_json_loads(proc.stdout, {}) or {}
                fmt = data.get("format") or {}
                streams = data.get("streams") or []
                video_stream = next((s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"), {})
                for obj in (fmt, video_stream):
                    if isinstance(obj, dict) and isinstance(obj.get("tags"), dict):
                        tags.update(obj.get("tags") or {})
                status = "ok"
            else:
                status = "ffprobe_failed"
        normalized: dict[str, Any] = {}
        source = "Unknown / generic video metadata"
        for _, value in tags.items():
            parsed = _json_from_text(str(value or ""))
            if isinstance(parsed, (dict, list)):
                normalized = parse_comfy_prompt(parsed) if _looks_like_comfy_prompt(parsed) else parse_json_comment(parsed, source="Video JSON metadata")
                break
            if isinstance(value, str) and ("Negative prompt:" in value or "Steps:" in value):
                normalized = parse_a1111_parameters(value)
                break
        if not normalized and tags:
            normalized = parse_json_comment(tags, source="Video container tags")
        source = normalized.get("source_app") or source
        payload = self._result(path, "video", source, normalized, {"format": fmt, "streams": streams, "container_tags": tags, "probe_status": status} if include_raw else {})
        payload["probe_status"] = status
        return payload

    def extract_generic(self, path: Path, include_raw: bool = False) -> dict[str, Any]:
        sidecar = path.with_suffix(".json")
        raw: dict[str, Any] = {}
        normalized: dict[str, Any] = {}
        source = "Generic file metadata"
        if sidecar.exists():
            data = _safe_json_loads(sidecar.read_text(encoding="utf-8", errors="ignore"), {})
            raw["sidecar"] = data
            normalized = parse_json_comment(data, source="Sidecar JSON metadata")
            source = normalized.get("source_app") or "Sidecar JSON metadata"
        return self._result(path, classify_media(path), source, normalized, raw if include_raw else {})

    def _result(self, path: Path, media_type: str, source_app: str, normalized: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
        positive = str(normalized.get("positive_prompt") or "").strip()
        negative = str(normalized.get("negative_prompt") or "").strip()
        tags = [normalize_tag(t) for t in (normalized.get("tags") or []) if normalize_tag(t)]
        caption = str(normalized.get("caption") or "").strip()
        if not caption and positive and len(tags) < 3 and "," not in positive:
            caption = positive
        return {
            "path": str(path),
            "file_name": path.name,
            "media_type": media_type,
            "source_app": source_app or "Unknown",
            "positive_prompt": positive,
            "negative_prompt": negative,
            "tags": tags,
            "tag_string": tag_string(tags),
            "negative_tags": [normalize_tag(t) for t in (normalized.get("negative_tags") or []) if normalize_tag(t)],
            "caption": caption,
            "lora_refs": normalized.get("lora_references") or normalized.get("lora_refs") or [],
            "settings": normalized.get("settings") or {},
            "width": normalized.get("width") or 0,
            "height": normalized.get("height") or 0,
            "raw": raw,
        }

    def record_metadata(self, media_id: int | None, path: Path, payload: dict[str, Any]) -> None:
        now = now_iso()
        self.db.execute(
            """INSERT INTO media_metadata(media_id, path, media_type, source_app, positive_prompt, negative_prompt, tag_string, caption, payload_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(media_id, path) DO UPDATE SET media_type=excluded.media_type, source_app=excluded.source_app,
               positive_prompt=excluded.positive_prompt, negative_prompt=excluded.negative_prompt, tag_string=excluded.tag_string,
               caption=excluded.caption, payload_json=excluded.payload_json, updated_at=excluded.updated_at""",
            (media_id, str(path), payload.get("media_type") or classify_media(path), payload.get("source_app") or "Unknown", payload.get("positive_prompt") or "", payload.get("negative_prompt") or "", payload.get("tag_string") or "", payload.get("caption") or "", json.dumps(payload, ensure_ascii=False, default=str), now, now),
        )

    def apply_to_media(self, media_id: int, payload: dict[str, Any] | None = None, *, apply_tags: bool = True, apply_caption: bool = False, profile_key: str = "e621", order_strategy: str = "retain", save_sidecars: bool = True) -> MetadataApplyResult:
        item = self.media.get(media_id)
        if not item:
            raise FileNotFoundError(f"Media not found: {media_id}")
        data = payload or self.extract_for_media(media_id)
        tags = [normalize_tag(t) for t in (data.get("tags") or parse_tag_string(data.get("tag_string") or "")) if normalize_tag(t)]
        caption = str(data.get("caption") or "").strip()
        if apply_tags and tags:
            self.tags.set_tags(media_id, tags, source="generation_metadata", save_sidecar=save_sidecars, profile_key=profile_key, order_strategy=order_strategy)
        if apply_caption and caption:
            self.db.upsert_caption(media_id, caption, source="generation_metadata")
            if save_sidecars:
                write_text(Path(item.path).with_suffix(".caption"), caption)
        self.record_metadata(media_id, Path(item.path), data)
        return MetadataApplyResult(media_id=media_id, tags=tags, caption=caption, source_app=data.get("source_app") or "Unknown")

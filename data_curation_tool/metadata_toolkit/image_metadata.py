from __future__ import annotations

import gzip
import json
import re
from pathlib import Path
from typing import Any, Iterable

from PIL import ExifTags, Image

from .security import file_stat, json_dumps, safe_json_loads, truncate_text
from .text_utils import coerce_float, coerce_int, extract_lora_references, unique_preserve_order

NOVELAI_MAGIC = "stealth_pngcomp"
SCHEMA_VERSION = "0.2.4"


def _jsonable(v: Any) -> Any:
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    return str(v)


def _decode_user_comment(v: Any) -> str:
    if not v:
        return ""
    if isinstance(v, str):
        return v
    if not isinstance(v, (bytes, bytearray)):
        return str(v)
    data = bytes(v)
    payloads = [data[8:], data] if len(data) > 8 else [data]
    for p in payloads:
        for enc in ("utf-16", "utf-16-be", "utf-16-le", "utf-8", "latin-1"):
            try:
                s = p.decode(enc, errors="strict").strip("\x00\ufeff ")
                if s and sum(ch.isprintable() for ch in s) / max(1, len(s)) > 0.75:
                    return s
            except Exception:
                pass
    return data.decode("utf-8", errors="replace")


def _exif_dict(img: Image.Image) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        exif = img.getexif()
        for k, v in exif.items():
            tag = ExifTags.TAGS.get(k, str(k))
            out[tag] = _decode_user_comment(v) if tag == "UserComment" else _jsonable(v)
    except Exception as e:
        out["_error"] = str(e)
    return out


def _split_settings_line(setting: str) -> dict[str, str]:
    """Parse A1111-like `Key: value, Key: value` strings without breaking prompt commas."""
    setting = (setting or "").strip().lstrip(",").strip()
    if not setting:
        return {}
    parts = re.split(r",\s+(?=[A-Za-z][A-Za-z0-9 _/()\-]+:\s*)", setting)
    d: dict[str, str] = {}
    for p in parts:
        if ":" in p:
            k, v = p.split(":", 1)
            k = k.strip()
            v = v.strip()
            if k and k not in d:
                d[k] = v
    return d


def _lower_map(data: dict[str, Any]) -> dict[str, Any]:
    return {str(k).lower().replace(" ", "_").replace("-", "_"): v for k, v in data.items()}


def _first(data: dict[str, Any], aliases: Iterable[str], default: Any = "") -> Any:
    if not isinstance(data, dict):
        return default
    lmap = _lower_map(data)
    for a in aliases:
        if a in data and data[a] not in (None, "", "None"):
            return data[a]
        key = str(a).lower().replace(" ", "_").replace("-", "_")
        if key in lmap and lmap[key] not in (None, "", "None"):
            return lmap[key]
    return default


def _as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    parsed = safe_json_loads(value, default=None)
    if isinstance(parsed, list):
        return parsed
    return [value]


def _coerce_metadata_object(value: Any) -> dict[str, Any]:
    """Normalize common metadata structures into a dict.

    Some generators store metadata as JSON dicts, while Fooocus/related tools may store
    a list of {label/name/key, value/text/content} records. This function preserves raw
    structures while exposing common key/value pairs for normalization.
    """
    data = safe_json_loads(value, default=value) if isinstance(value, str) else value
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        out: dict[str, Any] = {}
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                out[f"item_{i}"] = item
                continue
            key = item.get("label") or item.get("name") or item.get("key") or item.get("title") or item.get("field")
            val = item.get("value")
            if val is None:
                val = item.get("text") if item.get("text") is not None else item.get("content")
            if key:
                out[str(key)] = val
            else:
                out[f"item_{i}"] = item
        if out:
            out.setdefault("_raw_items", data)
            return out
    return {}


def _looks_like_comfy_prompt(obj: Any) -> bool:
    if isinstance(obj, str):
        obj = safe_json_loads(obj, default=None)
    if not isinstance(obj, dict):
        return False
    return any(isinstance(v, dict) and ("class_type" in v or "inputs" in v) for v in obj.values())


def _extract_json_from_text_blob(raw: Any) -> Any:
    text = str(raw or "")
    if not text:
        return None
    parsed = safe_json_loads(text, default=None)
    if parsed is not None:
        return parsed
    # XMP/XML wrappers often contain escaped JSON in a user-comment field. Do a conservative
    # brace scan rather than a greedy regex over the full file.
    starts = [i for i, ch in enumerate(text) if ch in "{["]
    for start in starts[:20]:
        for end in range(len(text), start, -1):
            snippet = text[start:end].strip()
            if not snippet or snippet[-1] not in "}]":
                continue
            parsed = safe_json_loads(snippet, default=None)
            if isinstance(parsed, (dict, list)):
                return parsed
            if len(snippet) > 2_000_000:
                break
    return None


def _compact_source_image(value: Any, limit: int = 4096) -> str:
    """Return a usable source-image reference while avoiding giant base64 dumps in node outputs."""
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("filename", "file", "path", "url", "image", "name", "hash"):
            if value.get(key):
                return truncate_text(value.get(key), limit)
        return truncate_text(json_dumps(value, pretty=False), limit)
    return truncate_text(value, limit)


def _extract_noise_settings(settings: dict[str, Any]) -> tuple[Any, Any, dict[str, Any]]:
    noise: dict[str, Any] = {}
    for k, v in (settings or {}).items():
        if "noise" in str(k).lower():
            noise[str(k)] = v
    amount = _first(
        settings,
        (
            "noise_injection_amount",
            "noise injection amount",
            "noiseInjectionAmount",
            "noise_multiplier",
            "Noise multiplier",
            "noise_strength",
            "noise strength",
            "eta noise seed delta",
            "Eta noise seed delta",
            "noise_offset",
            "Noise offset",
        ),
        "",
    )
    ntype = _first(
        settings,
        (
            "noise_injection_type",
            "noise injection type",
            "noiseInjectionType",
            "noise_type",
            "Noise type",
            "noise_schedule",
            "Noise Schedule",
            "noiseSchedule",
            "scheduler",
            "Schedule type",
        ),
        "",
    )
    return amount, ntype, noise


def _normalize_lora_refs(refs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for r in refs or []:
        if not isinstance(r, dict):
            continue
        name = str(r.get("name") or r.get("lora_name") or r.get("raw_name") or "").strip()
        if not name:
            continue
        strength_model = r.get("strength_model", r.get("weight", r.get("strength", "")))
        strength_clip = r.get("strength_clip", "")
        source = str(r.get("source", "prompt") or "prompt")
        key = (name, str(strength_model), str(strength_clip), source)
        if key in seen:
            continue
        seen.add(key)
        item = dict(r)
        item.setdefault("name", name)
        item.setdefault("strength_model", strength_model)
        item.setdefault("strength_clip", strength_clip)
        item.setdefault("weight", strength_model)
        item.setdefault("source", source)
        out.append(item)
    return out


def _extract_character_prompts(data: Any) -> list[dict[str, Any]]:
    """Handle known NovelAI v4-ish structures and generic character prompt arrays."""
    prompts: list[dict[str, Any]] = []

    def add(prompt: Any, source_key: str, index: int | None = None, raw: Any = None) -> None:
        if prompt is None:
            return
        text = truncate_text(prompt).strip()
        if not text:
            return
        item = {"index": len(prompts) if index is None else index, "prompt": text, "source_key": source_key}
        if raw is not None and isinstance(raw, dict):
            centers = raw.get("centers") or raw.get("coords") or raw.get("positions")
            if centers not in (None, ""):
                item["centers"] = _jsonable(centers)
        prompts.append(item)

    def walk(obj: Any, source_key: str = "root") -> None:
        if isinstance(obj, dict):
            # NovelAI v4 prompt has been seen in nested caption structures in user-supplied metadata examples.
            caption = obj.get("caption") if isinstance(obj.get("caption"), dict) else obj
            if isinstance(caption, dict):
                char_caps = _first(caption, ("char_captions", "character_captions", "character_prompts", "characters"), None)
                if isinstance(char_caps, list):
                    for i, ch in enumerate(char_caps):
                        if isinstance(ch, dict):
                            text = _first(ch, ("char_caption", "caption", "prompt", "description", "text"), "")
                            add(text, source_key + ".char_captions", i, ch)
                        else:
                            add(ch, source_key + ".char_captions", i)
            for k, v in obj.items():
                lk = str(k).lower()
                if isinstance(v, str) and ("character" in lk or lk.startswith("char_")) and any(tok in lk for tok in ("prompt", "caption", "description", "text")):
                    add(v, str(k))
                elif isinstance(v, list) and ("character" in lk or lk.startswith("char") or "char_" in lk):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            text = _first(item, ("char_caption", "caption", "prompt", "description", "text"), "")
                            add(text, str(k), i, item)
                        else:
                            add(item, str(k), i)
                elif isinstance(v, dict) and (lk in {"v4_prompt", "v4_negative_prompt", "caption"} or "character" in lk or lk.startswith("char")):
                    walk(v, str(k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{source_key}.{i}")

    walk(data)
    # De-duplicate exact prompt strings while preserving order.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for p in prompts:
        key = p.get("prompt", "").strip()
        if key and key not in seen:
            p["index"] = len(unique)
            unique.append(p)
            seen.add(key)
    return unique


def _extract_character_references(data: Any) -> list[dict[str, Any]]:
    """Collect character/reference-image source, strength, and fidelity/information-extracted values.

    The code is intentionally key-tolerant because metadata producers change names over time.
    It recognizes arrays/dicts containing reference images, strength values, fidelity values, and
    NovelAI-style "information extracted" values.
    """
    if not isinstance(data, dict):
        return []

    flat: dict[str, Any] = {}

    def flatten(obj: Any, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else str(k)
                flat[key] = v
                if isinstance(v, dict):
                    flatten(v, key)
        # Lists are kept as list values under their direct key; recursing into them creates too much noise.

    flatten(data)

    image_candidates: list[Any] = []
    strength_candidates: list[Any] = []
    fidelity_candidates: list[Any] = []
    raw_reference_objects: list[dict[str, Any]] = []

    for k, v in flat.items():
        lk = k.lower()
        has_ref = "reference" in lk or "ref_" in lk or lk.endswith("ref") or "character_reference" in lk
        if not has_ref:
            continue
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            if any(any(tok in str(key).lower() for tok in ("image", "source", "strength", "fidelity", "information")) for item in v for key in item.keys()):
                raw_reference_objects.extend([x for x in v if isinstance(x, dict)])
        if any(tok in lk for tok in ("image", "source", "file", "url")) and not any(tok in lk for tok in ("strength", "fidelity", "information", "extract")):
            image_candidates = _as_list(v) if not image_candidates else image_candidates
        if "strength" in lk or "weight" in lk:
            strength_candidates = _as_list(v) if not strength_candidates else strength_candidates
        if "fidelity" in lk or "information" in lk or "extract" in lk:
            fidelity_candidates = _as_list(v) if not fidelity_candidates else fidelity_candidates

    refs: list[dict[str, Any]] = []
    for obj in raw_reference_objects:
        refs.append(
            {
                "index": len(refs),
                "source_image": _compact_source_image(_first(obj, ("source_image", "image", "file", "path", "url", "source"), "")),
                "strength": _first(obj, ("strength", "reference_strength", "weight"), ""),
                "fidelity": _first(obj, ("fidelity", "information_extracted", "reference_information_extracted", "extracted"), ""),
                "raw": _jsonable(obj),
            }
        )

    count = max(len(image_candidates), len(strength_candidates), len(fidelity_candidates))
    for i in range(count):
        refs.append(
            {
                "index": len(refs),
                "source_image": _compact_source_image(image_candidates[i] if i < len(image_candidates) else ""),
                "strength": strength_candidates[i] if i < len(strength_candidates) else "",
                "fidelity": fidelity_candidates[i] if i < len(fidelity_candidates) else "",
            }
        )

    # Remove empty and duplicate rows.
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for r in refs:
        if not any(r.get(k) not in (None, "") for k in ("source_image", "strength", "fidelity")):
            continue
        key = json_dumps({k: r.get(k) for k in ("source_image", "strength", "fidelity")}, pretty=False)
        if key in seen:
            continue
        r["index"] = len(out)
        out.append(r)
        seen.add(key)
    return out


def _character_prompts_text(prompts: list[dict[str, Any]]) -> str:
    lines = []
    for i, item in enumerate(prompts or []):
        prompt = str(item.get("prompt", "")).strip()
        if prompt:
            lines.append(f"Character {i + 1}: {prompt}")
    return "\n".join(lines)


def _common_normalized(
    *,
    source_app: str,
    positive_prompt: Any = "",
    negative_prompt: Any = "",
    settings_text: str = "",
    settings: dict[str, Any] | None = None,
    width: int = 0,
    height: int = 0,
    lora_refs: list[dict[str, Any]] | None = None,
    raw_context: Any = None,
) -> dict[str, Any]:
    settings = settings or {}
    raw_context = raw_context if raw_context is not None else settings
    pos = truncate_text(positive_prompt)
    neg = truncate_text(negative_prompt)
    seed = _first(settings, ("Seed", "seed", "noise_seed", "Noise seed"), "")
    steps = _first(settings, ("Steps", "steps", "step_count", "stepCount", "sampling_steps"), "")
    cfg = _first(settings, ("CFG scale", "cfg", "cfg_scale", "scale", "guidance", "guidance_scale"), "")
    sampler = _first(settings, ("Sampler", "sampler", "sampler_name", "samplerName"), "")
    scheduler = _first(settings, ("Scheduler", "scheduler", "Schedule type", "schedule_type", "noise_schedule", "noiseSchedule"), "")
    model = _first(settings, ("Model", "model", "model_name", "Source", "ckpt_name", "checkpoint", "base_model_name"), "")
    base_model = _first(settings, ("Base model", "base_model", "baseModel", "baseModelName", "base_model_name"), "")
    model_hash = _first(settings, ("Model hash", "Model Hash", "model_hash", "modelHash", "hash", "sha256"), "")
    denoise = _first(settings, ("Denoising strength", "denoising_strength", "denoise", "denoise_strength", "img2img_strength"), "")
    strength = _first(settings, ("strength", "Strength", "image_strength", "reference_strength", "img2img_strength"), "")
    noise_amount, noise_type, noise_settings = _extract_noise_settings(settings)
    chars = _extract_character_prompts(raw_context)
    refs = _extract_character_references(raw_context)
    prompt_loras = extract_lora_references(pos + "\n" + neg)
    for r in prompt_loras:
        r.setdefault("source", "prompt")
    all_loras = _normalize_lora_refs((lora_refs or []) + prompt_loras)
    return {
        "source_app": source_app,
        "positive_prompt": pos,
        "negative_prompt": neg,
        "settings_text": settings_text,
        "settings": _jsonable(settings),
        "seed": seed,
        "steps": steps,
        "step_count": steps,
        "cfg_scale": cfg,
        "cfg": cfg,
        "sampler": sampler,
        "sampler_name": sampler,
        "scheduler": scheduler,
        "model": model,
        "model_name": model,
        "base_model": base_model,
        "model_hash": model_hash,
        "width": coerce_int(width, 0),
        "height": coerce_int(height, 0),
        "denoise_strength": denoise,
        "strength": strength,
        "noise_injection_amount": noise_amount,
        "noise_injection_type": noise_type,
        "noise_settings": _jsonable(noise_settings),
        "lora_references": all_loras,
        "character_prompts": chars,
        "character_prompts_text": _character_prompts_text(chars),
        "character_references": refs,
    }


def parse_a1111_parameters(raw: str, width: int = 0, height: int = 0) -> dict[str, Any]:
    raw = raw or ""
    positive = raw.strip()
    negative = ""
    setting = ""
    m = re.search(r"(?:^|\n)Steps\s*:", raw)
    steps_idx = m.start() if m else -1
    neg_idx = raw.find("\nNegative prompt:")
    if steps_idx != -1:
        setting_start = steps_idx + (1 if steps_idx < len(raw) and raw[steps_idx:steps_idx+1] == "\n" else 0)
        setting = raw[setting_start:].strip()
        positive = raw[:steps_idx].strip()
    if neg_idx != -1:
        positive = raw[:neg_idx].strip()
        neg_start = neg_idx + len("\nNegative prompt:")
        negative = raw[neg_start:steps_idx].strip() if steps_idx != -1 and steps_idx > neg_start else raw[neg_start:].strip()
    settings = _split_settings_line(setting)
    w, h = width, height
    if "x" in str(settings.get("Size", "")):
        a, b = str(settings["Size"]).lower().split("x", 1)
        w = coerce_int(a, width)
        h = coerce_int(b, height)
    return _common_normalized(
        source_app="A1111 webUI",
        positive_prompt=positive,
        negative_prompt=negative,
        settings_text=setting,
        settings=settings,
        width=w,
        height=h,
        raw_context=settings,
    )


class _StealthReader:
    def __init__(self, img: Image.Image):
        rgba = img.convert("RGBA")
        self.w, self.h = rgba.size
        self.p = rgba.load()
        self.row = 0
        self.col = 0

    def _bit(self) -> int:
        if self.col >= self.w:
            raise EOFError("NovelAI stealth payload ended early")
        bit = self.p[self.col, self.row][3] & 1
        self.row += 1
        if self.row == self.h:
            self.row = 0
            self.col += 1
        return bit

    def byte(self) -> int:
        b = 0
        for _ in range(8):
            b = (b << 1) | self._bit()
        return b

    def bytes(self, n: int) -> bytes:
        return bytes(self.byte() for _ in range(max(0, int(n))))

    def u32be(self) -> int:
        return int.from_bytes(self.bytes(4), "big", signed=False)


def extract_novelai_stealth(img: Image.Image) -> dict[str, Any] | None:
    try:
        r = _StealthReader(img)
        if r.bytes(len(NOVELAI_MAGIC)).decode("utf-8") != NOVELAI_MAGIC:
            return None
        nbits = r.u32be()
        nbytes = nbits // 8
        if nbytes <= 0 or nbytes > 16 * 1024 * 1024:
            return None
        data = json.loads(gzip.decompress(r.bytes(nbytes)).decode("utf-8"))
        if isinstance(data.get("Comment"), str):
            c = safe_json_loads(data.get("Comment"), default=None)
            if isinstance(c, dict):
                data["Comment"] = c
        return data
    except Exception:
        return None


def parse_novelai(info: dict[str, Any], width: int, height: int) -> dict[str, Any]:
    # NovelAI legacy stores Description + Comment; stealth may provide prompt fields directly.
    c = info.get("Comment")
    data = safe_json_loads(c, default={}) if isinstance(c, str) else (c if isinstance(c, dict) else {})
    merged: dict[str, Any] = {}
    if isinstance(data, dict):
        merged.update(data)
    for k, v in info.items():
        if k != "Comment" and k not in merged:
            merged[k] = v

    v4_prompt = merged.get("v4_prompt") if isinstance(merged.get("v4_prompt"), dict) else {}
    pos = merged.get("prompt") or merged.get("Description") or ""
    if not pos and isinstance(v4_prompt, dict):
        caption = v4_prompt.get("caption") if isinstance(v4_prompt.get("caption"), dict) else {}
        pos = caption.get("base_caption", "")
    neg = merged.get("uc") or merged.get("negative_prompt") or merged.get("v4_negative_prompt") or ""
    if isinstance(neg, dict):
        neg = json_dumps(neg, pretty=False)

    settings = {k: v for k, v in merged.items() if k not in {"prompt", "uc", "negative_prompt", "Description"}}
    return _common_normalized(
        source_app="NovelAI",
        positive_prompt=pos,
        negative_prompt=neg,
        settings_text=", ".join(f"{k}: {v}" for k, v in settings.items() if not isinstance(v, (dict, list))),
        settings=settings,
        width=coerce_int(merged.get("width"), width),
        height=coerce_int(merged.get("height"), height),
        raw_context=merged,
    )


def _node(prompt: dict[str, Any], node_id: Any) -> dict[str, Any]:
    return prompt.get(str(node_id), {}) if isinstance(prompt, dict) else {}


def _text_from_node(prompt: dict[str, Any], node_id: Any, seen: set[str] | None = None) -> str:
    seen = seen or set()
    node_id = str(node_id)
    if node_id in seen:
        return ""
    seen.add(node_id)
    node = _node(prompt, node_id)
    inputs = node.get("inputs") or {}
    ctype = node.get("class_type") or ""
    ctype_l = str(ctype).lower()
    if ctype in {"CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner"} or ("sdxl" in ctype_l and "text" in ctype_l):
        vals = []
        for k in ("text_g", "text_l", "text"):
            v = inputs.get(k)
            if isinstance(v, list):
                vals.append(_text_from_node(prompt, v[0], seen))
            elif v:
                vals.append(str(v))
        return ",\n".join(unique_preserve_order([x for x in vals if x]))
    if ctype in {"CLIPTextEncode", "BNK_CLIPTextEncodeAdvanced"} or "textencode" in ctype_l:
        v = inputs.get("text", "")
        return _text_from_node(prompt, v[0], seen) if isinstance(v, list) else str(v or "")
    for k in ("text", "value", "prompt", "positive", "negative", "string"):
        v = inputs.get(k)
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            got = _text_from_node(prompt, v[0], seen)
            if got:
                return got
    return ""


def _trace_model(prompt: dict[str, Any], node_id: Any, seen: set[str] | None = None) -> tuple[str, list[dict[str, Any]]]:
    seen = seen or set()
    node_id = str(node_id)
    if node_id in seen:
        return "", []
    seen.add(node_id)
    node = _node(prompt, node_id)
    inputs = node.get("inputs") or {}
    ctype = str(node.get("class_type") or "")
    ctype_l = ctype.lower()
    if "checkpointloader" in ctype_l or ctype in {"CheckpointLoaderSimple", "UNETLoader"}:
        return str(inputs.get("ckpt_name") or inputs.get("unet_name") or inputs.get("model_name") or ""), []
    loras: list[dict[str, Any]] = []
    if "lora" in ctype_l or "lycoris" in ctype_l:
        name = str(inputs.get("lora_name") or inputs.get("lora") or inputs.get("name") or "")
        if name:
            loras.append(
                {
                    "name": name,
                    "raw_name": name,
                    "strength_model": inputs.get("strength_model", inputs.get("strength", inputs.get("model_strength", ""))),
                    "strength_clip": inputs.get("strength_clip", inputs.get("clip_strength", "")),
                    "weight": inputs.get("strength_model", inputs.get("strength", "")),
                    "node_id": node_id,
                    "class_type": ctype,
                    "source": "comfyui_lora_loader",
                }
            )
    for k in ("model", "base_model", "model_in"):
        v = inputs.get(k)
        if isinstance(v, list):
            m, prev = _trace_model(prompt, v[0], seen)
            return m, prev + loras
    return "", loras


def _latent_size(prompt: dict[str, Any], node_id: Any, seen: set[str] | None = None) -> tuple[int, int]:
    seen = seen or set()
    node_id = str(node_id)
    if node_id in seen:
        return 0, 0
    seen.add(node_id)
    node = _node(prompt, node_id)
    inputs = node.get("inputs") or {}
    if "width" in inputs and "height" in inputs:
        return coerce_int(inputs.get("width")), coerce_int(inputs.get("height"))
    for k in ("latent_image", "samples", "image", "pixels", "samples_from"):
        v = inputs.get(k)
        if isinstance(v, list):
            w, h = _latent_size(prompt, v[0], seen)
            if w or h:
                return w, h
    return 0, 0


def parse_comfy_prompt(prompt_obj: Any, width: int = 0, height: int = 0) -> dict[str, Any]:
    prompt = safe_json_loads(prompt_obj, default={}) if isinstance(prompt_obj, str) else (prompt_obj if isinstance(prompt_obj, dict) else {})
    samplers = [(i, n) for i, n in prompt.items() if isinstance(n, dict) and "sampler" in str(n.get("class_type", "")).lower()]
    sid, snode = samplers[0] if samplers else ("", {})
    inputs = snode.get("inputs") or {}
    pos = _text_from_node(prompt, inputs["positive"][0]) if isinstance(inputs.get("positive"), list) else ""
    neg = _text_from_node(prompt, inputs["negative"][0]) if isinstance(inputs.get("negative"), list) else ""
    model, loras = _trace_model(prompt, inputs["model"][0]) if isinstance(inputs.get("model"), list) else ("", [])
    w, h = (0, 0)
    if isinstance(inputs.get("latent_image"), list):
        w, h = _latent_size(prompt, inputs["latent_image"][0])
    width = w or width
    height = h or height
    settings = {
        "steps": inputs.get("steps", ""),
        "step_count": inputs.get("steps", ""),
        "sampler_name": inputs.get("sampler_name", ""),
        "scheduler": inputs.get("scheduler", ""),
        "cfg": inputs.get("cfg", ""),
        "seed": inputs.get("seed", inputs.get("noise_seed", "")),
        "noise_seed": inputs.get("noise_seed", ""),
        "denoise": inputs.get("denoise", ""),
        "add_noise": inputs.get("add_noise", ""),
        "model": model,
        "width": width,
        "height": height,
        "sampler_node_id": sid,
    }
    return _common_normalized(
        source_app="ComfyUI",
        positive_prompt=pos,
        negative_prompt=neg,
        settings_text=", ".join(f"{k}: {v}" for k, v in settings.items() if v not in (None, "")),
        settings=settings,
        width=width,
        height=height,
        lora_refs=loras,
        raw_context={"prompt": prompt, "sampler_inputs": inputs},
    )


def parse_json_comment(comment: Any, width: int, height: int, source: str = "Fooocus/Civitai JSON Comment") -> dict[str, Any]:
    data = _coerce_metadata_object(comment)
    # Civitai/Comfy-like wrappers can keep the useful payload under meta/settings/parameters.
    for wrapper_key in ("meta", "metadata", "generation", "generation_data", "generationData"):
        if isinstance(data.get(wrapper_key), dict):
            nested = dict(data.get(wrapper_key) or {})
            nested.update({k: v for k, v in data.items() if k not in nested})
            data = nested
            break
    pos = _first(data, ("prompt", "Prompt", "positive", "positive_prompt", "Positive prompt", "Positive Prompt", "caption", "description"), "")
    neg = _first(data, ("negative_prompt", "negativePrompt", "Negative prompt", "Negative Prompt", "negative", "uc", "uncond", "negativePromptText"), "")
    settings = {k: v for k, v in data.items() if k not in {"prompt", "Prompt", "positive", "positive_prompt", "Positive prompt", "Positive Prompt", "negative_prompt", "negativePrompt", "Negative prompt", "Negative Prompt", "negative", "uc", "uncond", "caption", "description"}}
    return _common_normalized(
        source_app=source,
        positive_prompt=pos,
        negative_prompt=neg,
        settings_text=", ".join(f"{k}: {v}" for k, v in settings.items() if not isinstance(v, (dict, list))),
        settings=settings | {k: v for k, v in data.items() if k in {"seed", "Seed", "steps", "Steps", "cfg", "cfgScale", "CFG scale", "sampler", "Sampler", "model", "Model", "model_hash", "Model hash"}},
        width=coerce_int(_first(data, ("width", "Width", "W"), ""), width),
        height=coerce_int(_first(data, ("height", "Height", "H"), ""), height),
        raw_context=data,
    )

def _choose(info: dict[str, Any], exif: dict[str, Any], img: Image.Image, parse_stealth: bool) -> tuple[str, dict[str, Any], str]:
    w, h = img.size

    # A1111 / StableSwarm / JSON-in-parameters. A1111 uses a text line with Steps; some
    # applications put JSON in the same PNG chunk name.
    if info.get("parameters"):
        raw = str(info.get("parameters"))
        parsed = _extract_json_from_text_blob(raw)
        if isinstance(parsed, (dict, list)):
            src = "StableSwarmUI/JSON parameters" if "sui_image_params" in raw else "JSON parameters"
            return src, parse_json_comment(parsed, w, h, src), raw
        return "A1111 webUI", parse_a1111_parameters(raw, w, h), raw

    # EXIF UserComment: A1111 JPEG/WebP, Easy Diffusion JSON, Civitai-downloaded files.
    if exif.get("UserComment"):
        raw = str(exif.get("UserComment"))
        p = _extract_json_from_text_blob(raw)
        if isinstance(p, (dict, list)):
            return "JSON EXIF metadata", parse_json_comment(p, w, h, "JSON EXIF metadata"), raw
        return "A1111 webUI", parse_a1111_parameters(raw, w, h), raw

    # ComfyUI PNG stores API prompt graph in "prompt" and UI workflow in "workflow".
    if info.get("prompt"):
        raw = str(info.get("prompt"))
        parsed = safe_json_loads(raw, default=None)
        if _looks_like_comfy_prompt(parsed):
            return "ComfyUI", parse_comfy_prompt(parsed, w, h), raw
        # Some tools use a plain "prompt" key. Treat it as generic prompt-field metadata.
        return "Generic prompt fields", parse_json_comment(info, w, h, "Generic prompt fields"), raw

    # Easy Diffusion and other apps with direct key/value fields.
    direct_prompt_keys = {"Prompt", "positive_prompt", "positive", "negative_prompt", "Negative Prompt", "Negative prompt"}
    if any(k in info for k in direct_prompt_keys):
        return "Generic prompt fields", parse_json_comment(info, w, h, "Generic prompt fields"), json_dumps(info, pretty=False)

    # NovelAI legacy and modern non-stealth chunks.
    if info.get("Software") == "NovelAI" or ("Description" in info and "Comment" in info):
        return "NovelAI", parse_novelai(info, w, h), str(info.get("Comment", ""))

    # Fooocus/Civitai/JSON comments.
    comment = info.get("Comment", info.get("comment"))
    if comment:
        p = _extract_json_from_text_blob(comment)
        if isinstance(p, (dict, list)):
            return "Fooocus/Civitai JSON Comment", parse_json_comment(p, w, h), str(comment)
        raw = str(comment)
        if "Steps:" in raw or "Negative prompt:" in raw:
            return "A1111 webUI", parse_a1111_parameters(raw, w, h), raw

    # InvokeAI variants.
    for key in ("invokeai_metadata", "sd-metadata"):
        if info.get(key):
            raw = str(info.get(key))
            return "InvokeAI", parse_json_comment(_extract_json_from_text_blob(raw) or raw, w, h, "InvokeAI"), raw

    # Draw Things / XMP / Adobe-style containers sometimes put user comments in XML text.
    for key in ("XML:com.adobe.xmp", "xmp", "XMP", "xml"):
        if info.get(key):
            raw = str(info.get(key))
            p = _extract_json_from_text_blob(raw)
            if isinstance(p, (dict, list)):
                return "XMP JSON metadata", parse_json_comment(p, w, h, "XMP JSON metadata"), raw

    # NovelAI stealth must happen late because it is expensive and only possible for alpha images.
    if parse_stealth and img.mode == "RGBA":
        stealth = extract_novelai_stealth(img)
        if stealth:
            return "NovelAI stealth pnginfo", parse_novelai(stealth, w, h), json_dumps(stealth)

    return (
        "Unknown/Generic",
        _common_normalized(source_app="Unknown/Generic", width=w, height=h, settings={}, raw_context={}),
        "",
    )

def extract_image_metadata(path: Path, parse_stealth: bool = True, include_raw: bool = True) -> dict[str, Any]:
    p = Path(path).resolve()
    with Image.open(p) as img:
        info = {str(k): _jsonable(v) for k, v in (img.info or {}).items()}
        exif = _exif_dict(img)
        source, norm, raw = _choose(info, exif, img, parse_stealth)
        result = {
            "schema_version": SCHEMA_VERSION,
            "type": "image_metadata",
            "source_app": source,
            "status": "ok",
            "file": file_stat(p),
            "image": {"format": img.format, "mode": img.mode, "width": img.size[0], "height": img.size[1]},
            "normalized": norm,
            "safety": {"network_used": False, "code_executed_from_metadata": False, "metadata_written": False},
            "raw_text": truncate_text(raw),
        }
        result["raw"] = {"pil_info": info, "exif": exif} if include_raw else {"omitted": True}
        return result


def tensor_image_metadata(width: int, height: int, batch: int = 1, channels: int = 3, source: str = "ComfyUI IMAGE tensor") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "type": "image_metadata",
        "source_app": source,
        "status": "tensor_only_no_embedded_file_metadata",
        "image": {"format": "tensor", "mode": "RGB/RGBA", "width": int(width), "height": int(height), "batch": int(batch), "channels": int(channels)},
        "normalized": _common_normalized(source_app=source, width=int(width), height=int(height), settings={"batch": batch, "channels": channels}),
        "safety": {"network_used": False, "code_executed_from_metadata": False, "metadata_written": False},
        "raw": {"note": "ComfyUI IMAGE tensors do not preserve original PNG/EXIF metadata. Provide a file path or input-file name for full embedded metadata extraction."},
    }


def comfy_prompt_to_image_metadata(prompt_obj: Any, width: int = 0, height: int = 0, source: str = "Current ComfyUI prompt graph") -> dict[str, Any]:
    norm = parse_comfy_prompt(prompt_obj, width, height)
    norm["source_app"] = source
    return {
        "schema_version": SCHEMA_VERSION,
        "type": "image_metadata",
        "source_app": source,
        "status": "ok_current_prompt_graph",
        "image": {"format": "tensor/workflow", "width": int(width), "height": int(height)},
        "normalized": norm,
        "safety": {"network_used": False, "code_executed_from_metadata": False, "metadata_written": False},
        "raw": {"prompt": prompt_obj},
    }


def civitai_image_meta_to_normalized(image_obj: dict[str, Any]) -> dict[str, Any]:
    meta = image_obj.get("meta", image_obj) if isinstance(image_obj, dict) else {}
    return {"schema_version": SCHEMA_VERSION, "type": "civitai_image_meta", "source_app": "Civitai API image.meta", "status": "ok", "normalized": parse_json_comment(meta, 0, 0, "Civitai API image.meta"), "raw": image_obj}


def metadata_to_text(data: dict[str, Any]) -> str:
    n = data.get("normalized", {})
    return "\n".join(
        [
            f"Source: {data.get('source_app') or n.get('source_app','')}",
            f"Status: {data.get('status','')}",
            f"File: {data.get('file',{}).get('name','')}",
            f"Size: {n.get('width','')}x{n.get('height','')}",
            f"Seed: {n.get('seed','')}",
            f"Steps: {n.get('steps','')}",
            f"CFG: {n.get('cfg_scale','')}",
            f"Sampler: {n.get('sampler','')}",
            f"Scheduler: {n.get('scheduler','')}",
            f"Model: {n.get('model','')}",
            f"Base model: {n.get('base_model','')}",
            f"Model hash: {n.get('model_hash','')}",
            f"Denoise: {n.get('denoise_strength','')}",
            f"Strength: {n.get('strength','')}",
            f"Noise injection: amount={n.get('noise_injection_amount','')} type={n.get('noise_injection_type','')}",
            "",
            "Positive prompt:",
            str(n.get("positive_prompt", "")),
            "",
            "Negative prompt:",
            str(n.get("negative_prompt", "")),
            "",
            "Character prompts:",
            str(n.get("character_prompts_text", "")),
            "",
            "Character references:",
            json_dumps(n.get("character_references", [])),
            "",
            "Settings:",
            json_dumps(n.get("settings", {})),
            "",
            "LoRA references:",
            json_dumps(n.get("lora_references", [])),
            "",
            "Raw JSON:",
            json_dumps(data),
        ]
    )

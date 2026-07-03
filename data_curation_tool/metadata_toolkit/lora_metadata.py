from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .security import MAX_SAFETENSORS_HEADER_BYTES, file_stat, json_dumps, safe_json_loads, sha256_file, truncate_text
from .text_utils import split_tags, unique_preserve_order

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _folder_paths():
    try:
        import folder_paths  # type: ignore
        return folder_paths
    except Exception:
        return None


def available_loras() -> list[str]:
    fp = _folder_paths()
    if fp:
        try:
            names = fp.get_filename_list("loras")
            return sorted(names) if names else [""]
        except Exception:
            pass
    return [""]


def resolve_lora_path(lora_name: str = "", external_lora_path: str = "") -> Path:
    ext = str(external_lora_path or "").strip().strip('"')
    if ext:
        p = Path(ext).expanduser()
        candidates = [p] if p.is_absolute() else [Path.cwd()/p, PACKAGE_ROOT/p, PACKAGE_ROOT.parent/p]
        for c in candidates:
            if c.exists() and c.is_file(): return c.resolve()
        raise FileNotFoundError(f"LoRA path not found: {external_lora_path}")
    name = str(lora_name or "").strip()
    if not name: raise FileNotFoundError("No LoRA selected")
    fp = _folder_paths()
    if fp:
        p = fp.get_full_path("loras", name)
        if p and Path(p).exists(): return Path(p).resolve()
    p = Path(name).expanduser()
    if p.exists() and p.is_file(): return p.resolve()
    raise FileNotFoundError(f"LoRA not found: {lora_name}")


def read_safetensors_header(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        prefix = f.read(8)
        if len(prefix) != 8: raise ValueError("File too small for safetensors")
        size = int.from_bytes(prefix, "little", signed=False)
        if size <= 0: raise ValueError("Invalid safetensors header size")
        if size > MAX_SAFETENSORS_HEADER_BYTES: raise ValueError(f"Safetensors header too large: {size} bytes")
        header_bytes = f.read(size)
        if len(header_bytes) != size: raise ValueError("Truncated safetensors header")
    if not header_bytes.lstrip().startswith(b"{"):
        raise ValueError("Safetensors header is not JSON")
    header = json.loads(header_bytes.decode("utf-8"))
    meta = header.get("__metadata__", {}) if isinstance(header, dict) else {}
    if not isinstance(meta, dict): meta = {}
    return {"header_size_bytes": size, "metadata": meta, "tensor_names": [k for k in header.keys() if k != "__metadata__"], "header": header}


def _parse_possible_json(v: Any) -> Any:
    p = safe_json_loads(v, default=None)
    return p if p is not None else v


def _walk_for_keys(data: Any, wanted: set[str]) -> list[Any]:
    found = []
    if isinstance(data, dict):
        for k, v in data.items():
            kl = str(k).lower()
            if kl in wanted: found.append(v)
            parsed = _parse_possible_json(v)
            if isinstance(parsed, (dict, list)): found += _walk_for_keys(parsed, wanted)
            elif isinstance(v, (dict, list)): found += _walk_for_keys(v, wanted)
    elif isinstance(data, list):
        for item in data: found += _walk_for_keys(item, wanted)
    return found


def aggregate_training_tags(meta: dict[str, Any], top_n: int = 200) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    parsed = safe_json_loads(meta.get("ss_tag_frequency"), default=None)
    if isinstance(parsed, dict):
        for dataset in parsed.values():
            if isinstance(dataset, dict):
                for tag, count in dataset.items():
                    tag = str(tag).strip()
                    if tag:
                        try: counts[tag] += int(count)
                        except Exception: counts[tag] += 1
    for key in ("modelspec.tags", "ss_tags", "tags"):
        for tag in split_tags(meta.get(key)):
            counts.setdefault(tag, 1)
    return [{"tag": t, "count": c} for t, c in counts.most_common(max(0, int(top_n)))]


def extract_trigger_words(meta: dict[str, Any], training_tags: list[dict[str, Any]] | None = None, fallback_name: str = "") -> list[str]:
    wanted = {"ss_trigger_words", "ss_trigger_word", "trigger_words", "triggerwords", "trainedwords", "activation text", "activation_text", "activationtext"}
    values = []
    for k, v in meta.items():
        if str(k).lower() in wanted or "trigger" in str(k).lower(): values.append(v)
    values += _walk_for_keys(meta, wanted)
    words = []
    for v in values: words += split_tags(v)
    for k, v in meta.items():
        if "civitai" in str(k).lower() or "model" in str(k).lower():
            p = _parse_possible_json(v)
            if isinstance(p, (dict, list)):
                for found in _walk_for_keys(p, wanted): words += split_tags(found)
    if not words and training_tags:
        words += [x["tag"] for x in training_tags[:20] if x.get("tag")]
    if not words and fallback_name:
        words.append(Path(fallback_name).stem)
    return unique_preserve_order(words)


def normalize_lora_metadata(path: Path, hash_file: bool = True, top_training_tags: int = 200, append_lora_name_if_empty: bool = True) -> dict[str, Any]:
    path = Path(path).resolve()
    data: dict[str, Any] = {
        "schema_version": "0.1.0", "type": "lora_metadata", "file": file_stat(path),
        "sha256": "", "short_hash": "", "format": path.suffix.lower().lstrip("."), "status": "ok", "warnings": [],
        "safety": {"deserialized_model": False, "tensor_data_read": False, "pickle_read": False, "network_used": False},
        "raw": {}, "normalized": {}
    }
    if hash_file:
        h = sha256_file(path); data["sha256"] = h; data["short_hash"] = h[:10]
    if path.suffix.lower() != ".safetensors":
        data["status"] = "hash_only_unsafe_to_parse"
        data["warnings"].append("Only safetensors JSON headers are parsed; .ckpt/.pt are not deserialized.")
        data["normalized"] = {"title": path.stem, "trigger_words": [path.stem] if append_lora_name_if_empty else [], "training_tags": [], "base_model": "", "architecture": ""}
        return data
    header = read_safetensors_header(path)
    meta = header["metadata"]
    tags = aggregate_training_tags(meta, top_training_tags)
    triggers = extract_trigger_words(meta, tags, path.stem if append_lora_name_if_empty else "")
    data["raw"] = {"safetensors_header_size_bytes": header["header_size_bytes"], "tensor_names_count": len(header["tensor_names"]), "tensor_names_preview": header["tensor_names"][:50], "metadata": meta}
    data["normalized"] = {
        "title": truncate_text(meta.get("modelspec.title") or meta.get("ss_output_name") or path.stem, 2000),
        "base_model": truncate_text(meta.get("ss_base_model_version") or meta.get("modelspec.base_model") or meta.get("modelspec.baseModel") or meta.get("ss_sd_model_name") or "", 2000),
        "architecture": truncate_text(meta.get("modelspec.architecture") or meta.get("ss_network_module") or meta.get("network_module") or "", 2000),
        "network_dim": meta.get("ss_network_dim") or meta.get("network_dim") or "",
        "network_alpha": meta.get("ss_network_alpha") or meta.get("network_alpha") or "",
        "trigger_words": triggers,
        "training_tags": tags,
        "training_tags_csv": ", ".join([x["tag"] for x in tags]),
        "raw_metadata_key_count": len(meta),
    }
    return data


def metadata_to_text(data: dict[str, Any]) -> str:
    n = data.get("normalized", {})
    lines = [f"File: {data.get('file',{}).get('name','')}", f"SHA256: {data.get('sha256','')}", f"Title: {n.get('title','')}", f"Base model: {n.get('base_model','')}", f"Architecture: {n.get('architecture','')}", f"Trigger words: {', '.join(n.get('trigger_words',[]) or [])}", "Training tags:"]
    lines += [f"  - {x.get('tag')}: {x.get('count')}" for x in (n.get("training_tags") or [])[:100] if isinstance(x, dict)]
    lines += ["", "Raw JSON:", json_dumps(data, True)]
    return "\n".join(lines)

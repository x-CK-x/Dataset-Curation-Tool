from __future__ import annotations

import csv
import json
import re
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Iterable


# Official Ultralytics COCO checkpoints expose these 80 classes. Keeping the
# names locally lets the UI show valid classes without triggering a model
# download merely to inspect metadata.
COCO80_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich",
    "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush",
]

_GENERIC_QUERIES = {"", "*", "all", "any", "object", "objects", "everything", "none"}
_CLASS_KEYS = (
    "id2label", "label2id", "names", "classes", "class_names", "classnames", "labels",
    "categories", "class_map", "class_mapping",
)


def normalize_class_name(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def _coerce_names(value: Any) -> list[dict[str, Any]]:
    """Normalize common class-name containers into ``[{id, name}, ...]``."""
    rows: list[dict[str, Any]] = []
    if value is None:
        return rows
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return rows
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = None
        if parsed is not None and parsed is not value:
            return _coerce_names(parsed)
        # Try Python/YAML-ish dictionary/list strings before falling back to
        # comma/newline-separated names.
        if raw.startswith("{") and raw.endswith("}"):
            pairs = re.findall(r"(?:^|[,\s])['\"]?(\d+)['\"]?\s*:\s*['\"]?([^,'\"}]+)", raw)
            if pairs:
                return [{"id": int(idx), "name": name.strip()} for idx, name in pairs if name.strip()]
        parts = [p.strip().strip("'\"") for p in re.split(r"[\r\n,;]+", raw) if p.strip()]
        return [{"id": index, "name": name} for index, name in enumerate(parts)]
    if isinstance(value, dict):
        # id -> label
        numeric_keys = []
        for key, name in value.items():
            try:
                numeric_keys.append((int(key), str(name)))
            except Exception:
                numeric_keys = []
                break
        if numeric_keys:
            return [{"id": idx, "name": name} for idx, name in sorted(numeric_keys) if name.strip()]
        # label -> id
        label_ids: list[tuple[int, str]] = []
        for name, idx in value.items():
            try:
                label_ids.append((int(idx), str(name)))
            except Exception:
                continue
        if label_ids:
            return [{"id": idx, "name": name} for idx, name in sorted(label_ids) if name.strip()]
        return rows
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            if isinstance(item, dict):
                name = item.get("name") or item.get("label") or item.get("class") or item.get("tag")
                idx = item.get("id", item.get("index", index))
                if name not in (None, ""):
                    try:
                        idx = int(idx)
                    except Exception:
                        idx = index
                    rows.append({"id": idx, "name": str(name)})
            elif item not in (None, ""):
                rows.append({"id": index, "name": str(item)})
    return rows


def _dedupe(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[int, str] = {}
    seen_names: set[str] = set()
    for index, row in enumerate(rows):
        try:
            idx = int(row.get("id", index))
        except Exception:
            idx = index
        name = str(row.get("name") or "").strip()
        normalized = normalize_class_name(name)
        if not normalized or normalized in seen_names:
            continue
        seen_names.add(normalized)
        while idx in by_id:
            idx += 1
        by_id[idx] = name
    return [{"id": idx, "name": by_id[idx]} for idx in sorted(by_id)]


def _extract_from_mapping(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    # Prefer well-known class metadata keys.
    for key in _CLASS_KEYS:
        if key in data:
            rows = _coerce_names(data[key])
            if rows:
                return _dedupe(rows)
    # Some model configs nest the useful mapping.
    for key in ("model", "data", "dataset", "metadata", "config", "head"):
        nested = data.get(key)
        rows = _extract_from_mapping(nested)
        if rows:
            return rows
    return []


def _read_json(path: Path) -> list[dict[str, Any]]:
    try:
        return _extract_from_mapping(json.loads(path.read_text(encoding="utf-8", errors="ignore")))
    except Exception:
        return []


def _read_yaml(path: Path) -> list[dict[str, Any]]:
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore"))
        rows = _extract_from_mapping(data)
        if rows:
            return rows
    except Exception:
        pass
    # Minimal fallback for common Ultralytics ``names:`` YAML layouts.
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    inline = re.search(r"(?ms)^names\s*:\s*(\[[^\n]+\]|\{[^\n]+\})", text)
    if inline:
        return _dedupe(_coerce_names(inline.group(1)))
    block_match = re.search(r"(?ms)^names\s*:\s*\n((?:\s+[^\n]+\n?)+)", text)
    if block_match:
        pairs: list[dict[str, Any]] = []
        for line in block_match.group(1).splitlines():
            match = re.match(r"\s*(\d+)\s*:\s*['\"]?(.+?)['\"]?\s*$", line)
            if match:
                pairs.append({"id": int(match.group(1)), "name": match.group(2).strip()})
        return _dedupe(pairs)
    return []


def _read_text_names(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(\d+)\s*[:\t ]\s*(.+)$", line)
        if match:
            rows.append({"id": int(match.group(1)), "name": match.group(2).strip()})
        else:
            rows.append({"id": index, "name": line})
    return _dedupe(rows)


def _read_csv_names(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return []
            normalized = {normalize_class_name(name).replace(" ", "_"): name for name in reader.fieldnames}
            name_col = next((normalized[key] for key in ("name", "class_name", "class", "label", "tag") if key in normalized), None)
            id_col = next((normalized[key] for key in ("id", "class_id", "index") if key in normalized), None)
            if not name_col:
                return []
            rows = []
            for index, row in enumerate(reader):
                name = str(row.get(name_col) or "").strip()
                if not name:
                    continue
                try:
                    idx = int(row.get(id_col)) if id_col and row.get(id_col) not in (None, "") else index
                except Exception:
                    idx = index
                rows.append({"id": idx, "name": name})
            return _dedupe(rows)
    except Exception:
        return []


def _read_onnx_metadata(path: Path) -> list[dict[str, Any]]:
    try:
        import onnxruntime as ort
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        metadata = dict(session.get_modelmeta().custom_metadata_map or {})
        rows = _extract_from_mapping(metadata)
        if rows:
            return rows
        for key in _CLASS_KEYS:
            if key in metadata:
                rows = _coerce_names(metadata[key])
                if rows:
                    return _dedupe(rows)
    except Exception:
        pass
    return []


def _read_safetensors_metadata(path: Path) -> list[dict[str, Any]]:
    try:
        from safetensors import safe_open
        with safe_open(str(path), framework="pt", device="cpu") as handle:
            metadata = dict(handle.metadata() or {})
        rows = _extract_from_mapping(metadata)
        if rows:
            return rows
        for key in _CLASS_KEYS:
            if key in metadata:
                rows = _coerce_names(metadata[key])
                if rows:
                    return _dedupe(rows)
    except Exception:
        pass
    return []


def _try_ultralytics_names(path_or_id: str) -> list[dict[str, Any]]:
    try:
        from ultralytics import YOLO
        model = YOLO(str(path_or_id))
        names = getattr(model, "names", None)
        return _dedupe(_coerce_names(names))
    except Exception:
        return []


def inspect_model_classes(
    model_path: str | Path | None,
    *,
    model_key: str = "",
    provider: str = "",
    capabilities: Iterable[str] | None = None,
    custom_model_type: str = "auto",
    allow_runtime_load: bool = True,
) -> dict[str, Any]:
    """Inspect a model/checkpoint/repository for its supported classes.

    This never unpickles arbitrary custom checkpoints directly. Ultralytics `.pt`
    files are inspected through the Ultralytics loader; JSON/YAML/TXT/CSV/ONNX/
    safetensors metadata is parsed using format-specific safe readers.
    """
    caps = {str(value).lower() for value in (capabilities or [])}
    key = str(model_key or "").lower()
    provider = str(provider or "").lower()
    custom_type = str(custom_model_type or "auto").lower()
    is_sam = "sam" in caps or "sam2" in caps or key.startswith(("sam-", "sam2", "custom-sam")) or custom_type in {"sam", "sam_hq", "sam2"}
    is_open_vocab = "open_vocabulary" in caps or "text_prompt" in caps or "grounding" in key or "owlv" in key
    is_yolo = provider == "ultralytics" or "yolo" in caps or "yolo" in key or custom_type == "yolo"
    if is_sam and not is_yolo:
        return {
            "mode": "class_agnostic",
            "classes": [],
            "class_count": 0,
            "source": "model_capability",
            "prompt_affects_geometry": False,
            "message": "SAM-family models do not understand class names. A class name only labels the output; use a point/bbox prompt or a detector-guided segmentation pipeline for semantic class-specific masks.",
        }
    if is_open_vocab and not is_yolo:
        return {
            "mode": "text_conditioned",
            "classes": [],
            "class_count": None,
            "source": "model_capability",
            "prompt_affects_geometry": True,
            "message": "This model accepts free-form text prompts rather than a fixed class list.",
        }

    path = Path(str(model_path)).expanduser() if model_path else None
    candidates: list[Path] = []
    if path and path.exists():
        if path.is_dir():
            preferred_names = [
                "data.yaml", "dataset.yaml", "model.yaml", "config.yaml", "config.json",
                "classes.txt", "labels.txt", "names.txt", "obj.names", "metadata.json",
            ]
            for name in preferred_names:
                candidate = path / name
                if candidate.exists():
                    candidates.append(candidate)
            for pattern in ("*.names", "*classes*.txt", "*labels*.txt", "*.yaml", "*.yml", "*.json", "*.csv", "*.onnx", "*.safetensors"):
                for candidate in sorted(path.rglob(pattern))[:100]:
                    if candidate not in candidates:
                        candidates.append(candidate)
        else:
            candidates.append(path)
            parent = path.parent
            for name in ("data.yaml", "dataset.yaml", "config.json", "classes.txt", "labels.txt", "names.txt", "obj.names"):
                candidate = parent / name
                if candidate.exists() and candidate not in candidates:
                    candidates.append(candidate)

    # For official Ultralytics COCO models, class names are known without loading.
    if is_yolo and (not path or not path.exists()) and re.search(r"yolo(?:11|26|v?\d+).*(?:detect|seg)?$", key.replace("-", "")):
        rows = [{"id": index, "name": name} for index, name in enumerate(COCO80_CLASSES)]
        return {
            "mode": "closed_set", "classes": rows, "class_count": len(rows),
            "source": "built_in_coco80", "prompt_affects_geometry": True,
            "message": "Closed-set COCO model. The class token is resolved to a class ID and passed to inference as a strict filter.",
        }

    # Ultralytics is the authoritative source for custom/official YOLO .pt names.
    if is_yolo and allow_runtime_load and model_path:
        rows = _try_ultralytics_names(str(model_path))
        if rows:
            return {
                "mode": "closed_set", "classes": rows, "class_count": len(rows),
                "source": "ultralytics_model.names", "prompt_affects_geometry": True,
                "message": "Classes were read from the loaded Ultralytics checkpoint. Typed class names are applied as strict inference filters.",
            }

    readers = {
        ".json": _read_json,
        ".yaml": _read_yaml,
        ".yml": _read_yaml,
        ".txt": _read_text_names,
        ".names": _read_text_names,
        ".csv": _read_csv_names,
        ".onnx": _read_onnx_metadata,
        ".safetensors": _read_safetensors_metadata,
    }
    for candidate in candidates:
        reader = readers.get(candidate.suffix.lower())
        if not reader:
            continue
        rows = reader(candidate)
        if rows:
            return {
                "mode": "closed_set", "classes": rows, "class_count": len(rows),
                "source": str(candidate), "prompt_affects_geometry": True,
                "message": "Classes were parsed from model-side metadata. Typed class names are used as strict filters when the runtime supports class filtering.",
            }

    if is_yolo:
        return {
            "mode": "closed_set", "classes": [], "class_count": 0,
            "source": "not_found", "prompt_affects_geometry": True,
            "message": "No class metadata could be parsed. Load/validate the model or place data.yaml, config.json, classes.txt, labels.txt, or names.txt beside the custom checkpoint.",
        }
    return {
        "mode": "unknown", "classes": [], "class_count": 0,
        "source": "not_found", "prompt_affects_geometry": None,
        "message": "The model did not expose a fixed class list. Check its model card/configuration or use an explicit adapter.",
    }


def resolve_class_query(classes: Iterable[dict[str, Any]], query: str | None) -> dict[str, Any]:
    rows = _dedupe(classes)
    raw = str(query or "").strip()
    normalized = normalize_class_name(raw)
    if normalized in _GENERIC_QUERIES:
        return {"query": raw, "class_ids": [], "matches": [], "all_classes": True, "suggestions": []}

    by_id = {int(row["id"]): row for row in rows}
    by_name = {normalize_class_name(row["name"]): row for row in rows}
    tokens = [part.strip() for part in re.split(r"[,;|]+", raw) if part.strip()]
    matches: list[dict[str, Any]] = []
    missing: list[str] = []
    suggestions: list[str] = []
    for token in tokens:
        token_norm = normalize_class_name(token)
        row = None
        if token_norm.isdigit() and int(token_norm) in by_id:
            row = by_id[int(token_norm)]
        if row is None:
            row = by_name.get(token_norm)
        if row is None:
            singular = token_norm[:-1] if token_norm.endswith("s") else token_norm
            plural = token_norm + "s"
            row = by_name.get(singular) or by_name.get(plural)
        if row is None:
            contains = [candidate for name, candidate in by_name.items() if token_norm in name or name in token_norm]
            if len(contains) == 1:
                row = contains[0]
        if row is None:
            missing.append(token)
            suggestions.extend(get_close_matches(token_norm, list(by_name), n=6, cutoff=0.45))
        elif int(row["id"]) not in {int(item["id"]) for item in matches}:
            matches.append(row)
    return {
        "query": raw,
        "class_ids": [int(row["id"]) for row in matches],
        "matches": matches,
        "all_classes": False,
        "missing": missing,
        "suggestions": list(dict.fromkeys(suggestions))[:12],
    }

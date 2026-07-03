from __future__ import annotations

import json, re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any, Iterable

_LORA_RE = re.compile(r"<\s*lora\s*:\s*([^:>]+?)\s*(?::\s*([-+]?\d*\.?\d+))?(?::[^>]*)?>", re.I)


def unique_preserve_order(items: Iterable[Any]) -> list[Any]:
    seen, out = set(), []
    for item in items:
        key = str(item).strip()
        if key and key not in seen:
            out.append(item); seen.add(key)
    return out


def split_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return unique_preserve_order([str(x).strip() for x in value if str(x).strip()])
    if isinstance(value, dict):
        return split_tags(list(value.keys()))
    text = str(value).strip()
    if not text:
        return []
    if text[:1] in "[{":
        try:
            return split_tags(json.loads(text))
        except Exception:
            pass
    return unique_preserve_order([p.strip().strip('"\'') for p in re.split(r"[,;\n]+", text) if p.strip().strip('"\'')])


def clean_lora_name(name: str) -> str:
    text = str(name).strip().replace("\\", "/")
    base = PureWindowsPath(PurePosixPath(text).name).name
    if "." in base and base.rsplit(".", 1)[0]:
        return base.rsplit(".", 1)[0]
    return base


def extract_lora_references(prompt: str) -> list[dict[str, Any]]:
    refs = []
    for m in _LORA_RE.finditer(prompt or ""):
        try:
            weight = float(m.group(2)) if m.group(2) not in (None, "") else 1.0
        except Exception:
            weight = 1.0
        refs.append({"raw": m.group(0), "name": clean_lora_name(m.group(1)), "raw_name": m.group(1).strip(), "weight": weight, "start": m.start(), "end": m.end()})
    return refs


def strip_lora_references(prompt: str) -> str:
    text = _LORA_RE.sub("", prompt or "")
    text = re.sub(r"\s*,\s*,+", ",", text)
    text = re.sub(r"(^\s*,\s*)|(\s*,\s*$)", "", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def parse_selector(selector: str, items: list[str]) -> list[str]:
    selector = (selector or ":").strip() or ":"
    out: dict[int, str] = {}
    n = len(items)
    for part in selector.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if ":" not in part:
                idx = int(part); idx = n + idx if idx < 0 else idx
                if 0 <= idx < n: out[idx] = items[idx]
            elif part.count(":") == 1:
                a, b = [x.strip() for x in part.split(":")]
                start = int(a) if a else 0; end = int(b) if b else n
                start = n + start if start < 0 else start; end = n + end if end < 0 else end
                for idx in range(max(0, min(start, n)), max(0, min(end, n))): out[idx] = items[idx]
        except Exception:
            continue
    return [out[i] for i in sorted(out)]


def format_tags(tags: list[str], weight: float = 1.0, ensure_comma: bool = True) -> str:
    parts = [f"({t}:{float(weight):g})" if abs(float(weight)-1.0) > 1e-9 else t for t in [str(x).strip() for x in tags] if t]
    text = ", ".join(parts)
    return text + ("," if ensure_comma and text and not text.endswith(",") else "")


def deep_get(data: Any, path: str, default: Any = "") -> Any:
    cur = data
    for part in [p for p in (path or "").replace("/", ".").split(".") if p != ""]:
        if isinstance(cur, dict): cur = cur.get(part, default)
        elif isinstance(cur, list):
            try: cur = cur[int(part)]
            except Exception: return default
        else: return default
    return cur


def coerce_int(value: Any, default: int = 0) -> int:
    try:
        return default if value in (None, "", "None") else int(float(str(value).strip()))
    except Exception:
        return default


def coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return default if value in (None, "", "None") else float(str(value).strip())
    except Exception:
        return default

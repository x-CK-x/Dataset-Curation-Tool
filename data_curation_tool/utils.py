from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageOps

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".opus", ".aac"}
MODEL_METADATA_EXTENSIONS = {".safetensors"}
ANIMATION_EXTENSIONS = {".gif"}
SIDECAR_EXTENSIONS = {".txt", ".caption", ".json"}
TAG_SPLIT_RE = re.compile(r"[,\n]+")
TAG_SAFE_RE = re.compile(r"\s+")
TAG_TEXT_MODES = {"underscores", "spaces"}


def tag_text_mode() -> str:
    mode = os.environ.get("DCT_TAG_TEXT_MODE_ACTIVE", "underscores").strip().lower()
    return mode if mode in TAG_TEXT_MODES else "underscores"


def set_tag_text_mode(mode: str | None) -> str:
    clean = str(mode or "underscores").strip().lower()
    if clean not in TAG_TEXT_MODES:
        clean = "underscores"
    os.environ["DCT_TAG_TEXT_MODE_ACTIVE"] = clean
    return clean


def normalize_tag_canonical(tag: str) -> str:
    text = str(tag).strip()
    text = text.replace(" ", "_")
    text = TAG_SAFE_RE.sub("_", text)
    return text.strip("_,")


def format_tag_for_mode(tag: str, mode: str | None = None) -> str:
    canonical = normalize_tag_canonical(tag)
    clean_mode = str(mode or tag_text_mode()).strip().lower()
    if clean_mode == "spaces":
        return canonical.replace("_", " ").strip(" ,")
    return canonical


def tag_for_source_query(tag: str) -> str:
    """Return source/API-safe tag text, preserving booru underscore syntax."""
    return normalize_tag_canonical(tag)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def average_hash(path: Path, hash_size: int = 8) -> str | None:
    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)
            pixels = list(im.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if px >= avg else '0' for px in pixels)
            return hex(int(bits, 2))[2:].rjust(hash_size * hash_size // 4, "0")
    except Exception:
        return None


def hamming_hex(left: str | None, right: str | None) -> int | None:
    if not left or not right:
        return None
    width = max(len(left), len(right))
    a = int(left, 16)
    b = int(right, 16)
    return (a ^ b).bit_count() if width else None


def image_size(path: Path) -> tuple[int | None, int | None]:
    try:
        # Header-only probe.  Avoid EXIF transpose here because import only needs
        # an approximate stored width/height and transpose can force more image
        # work across large folders.  Thumbnail/render paths still handle EXIF.
        with Image.open(path) as im:
            return im.width, im.height
    except Exception:
        return None, None


def classify_media(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in ANIMATION_EXTENSIONS:
        return "animation"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in MODEL_METADATA_EXTENSIONS:
        return "model"
    return "unknown"


def iter_media_files(root: Path, recursive: bool = True) -> Iterable[Path]:
    pattern = "**/*" if recursive else "*"
    for path in root.glob(pattern):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS:
            yield path


def normalize_tag(tag: str) -> str:
    return format_tag_for_mode(tag)


def parse_tag_string(tag_string: str, separator: str = ",") -> list[str]:
    if not tag_string:
        return []
    if separator and separator != ",":
        raw = tag_string.split(separator)
    else:
        raw = TAG_SPLIT_RE.split(tag_string)
    tags: list[str] = []
    seen: set[str] = set()
    for item in raw:
        tag = normalize_tag(item)
        if tag and tag.lower() != "nan" and tag not in seen:
            tags.append(tag)
            seen.add(tag)
    return tags


def tag_string(tags: Iterable[str], separator: str = ", ") -> str:
    return separator.join([normalize_tag(tag) for tag in tags if normalize_tag(tag)])


def sidecar_for(path: Path, suffix: str = ".txt") -> Path:
    return path.with_suffix(suffix)


def read_text_if_exists(path: Path | None) -> str:
    if path and path.exists():
        try:
            return path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            return path.read_text(errors="ignore").strip()
    return ""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def is_safe_readonly_sql(sql: str) -> bool:
    stripped = sql.strip().lower()
    return stripped.startswith("select") or stripped.startswith("with") or stripped.startswith("pragma")

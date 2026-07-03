from __future__ import annotations

import hashlib, json, os, re, tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

MAX_SAFETENSORS_HEADER_BYTES = 128 * 1024 * 1024
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_TEXT_FIELD_CHARS = 4 * 1024 * 1024
MAX_THUMBNAIL_BYTES = 12 * 1024 * 1024
_TOKEN_RE = re.compile(r"(?i)(token|api[_-]?key|authorization|bearer)([=:\s]+)([^\s&]+)")
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._ -]+")


def redact_secret(text: Any) -> str:
    return _TOKEN_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", str(text))


def sanitize_filename(name: str, fallback: str = "metadata") -> str:
    name = Path(str(name)).name.strip().strip(".")
    name = _SAFE_FILENAME_RE.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or fallback


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except OSError:
            pass


def json_dumps(data: Any, pretty: bool = True) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, separators=None if pretty else (",", ":"))


def safe_json_loads(value: Any, default: Any = None, max_chars: int = MAX_JSON_BYTES) -> Any:
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        if len(value) > max_chars:
            return default
        value = value.decode("utf-8", errors="replace")
    if not isinstance(value, str) or len(value) > max_chars:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def truncate_text(value: Any, limit: int = MAX_TEXT_FIELD_CHARS) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else text[:limit] + f"\n...[truncated to {limit} chars]"


def sha256_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def file_stat(path: Path) -> dict[str, Any]:
    p = Path(path)
    st = p.stat()
    return {"path": str(p), "name": p.name, "suffix": p.suffix.lower(), "size_bytes": int(st.st_size), "modified_unix": float(st.st_mtime)}


def ensure_output_child(output_dir: Path, filename: str) -> Path:
    output_dir = Path(output_dir).resolve()
    path = (output_dir / sanitize_filename(filename)).resolve()
    if output_dir != path.parent and output_dir not in path.parents:
        raise ValueError("Refusing to write outside output directory")
    return path


def unique_path(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        return path
    for i in range(1, 100000):
        candidate = path.with_name(f"{path.stem}_{i:03d}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find a unique filename for {path}")


def validate_https_url(url: str, allowed_hosts: Iterable[str] | None = None) -> str:
    parsed = urlparse(str(url).strip())
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError("Only https URLs with a host are allowed")
    if allowed_hosts:
        host = parsed.hostname or ""
        allowed = set(allowed_hosts)
        if host not in allowed and not any(host.endswith("." + h) for h in allowed):
            raise ValueError(f"Host is not allow-listed: {host}")
    return parsed.geturl()


def resolve_existing_path(path_text: str, candidates: Iterable[Path] = ()) -> Path:
    text = os.path.expandvars(os.path.expanduser(str(path_text or "").strip().strip('"')))
    if not text:
        raise FileNotFoundError("No file path provided")
    p = Path(text)
    possible = [p] if p.is_absolute() else [Path.cwd() / p, *[Path(c) / p for c in candidates]]
    for candidate in possible:
        try:
            r = candidate.resolve()
        except Exception:
            continue
        if r.exists() and r.is_file():
            return r
    raise FileNotFoundError(f"File not found: {path_text}")

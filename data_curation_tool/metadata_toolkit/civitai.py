from __future__ import annotations

import json, os, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from typing import Any

from .security import MAX_JSON_BYTES, MAX_THUMBNAIL_BYTES, atomic_write_text, json_dumps, redact_secret, safe_json_loads, validate_https_url

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = PACKAGE_ROOT / "cache" / "civitai"
API_BASE = "https://civitai.com"
ALLOWED_IMAGE_HOSTS = {"image.civitai.com", "imagecache.civitai.com", "civitai.com"}


def _token(t: str = "", use_env_token: bool = True) -> str:
    return str(t or "").strip() or (os.environ.get("CIVITAI_API_TOKEN", "").strip() if use_env_token else "")


def _read_limited(resp, max_bytes: int) -> bytes:
    chunks, total = [], 0
    while True:
        chunk = resp.read(64 * 1024)
        if not chunk: break
        total += len(chunk)
        if total > max_bytes: raise ValueError(f"Response exceeded {max_bytes} bytes")
        chunks.append(chunk)
    return b"".join(chunks)


def api_get(path: str, params: dict[str, Any] | None = None, civitai_api_token: str = "", use_env_token: bool = True, network_enabled: bool = False, timeout_seconds: int = 20) -> dict[str, Any]:
    if not network_enabled:
        return {"status": "network_disabled", "error": "Network use is disabled. Toggle network_enabled to call Civitai.", "data": None}
    if not path.startswith("/api/v1/"): raise ValueError("Only /api/v1/ Civitai API paths are allowed")
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v not in (None, "")})
    url = API_BASE + path + (("?" + query) if query else "")
    headers = {"Accept": "application/json", "User-Agent": "ComfyUI-Metadata-Toolkit/0.1"}
    tok = _token(civitai_api_token, use_env_token)
    if tok: headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=max(1, int(timeout_seconds))) as resp:
            body = _read_limited(resp, MAX_JSON_BYTES).decode("utf-8", errors="replace")
            data = safe_json_loads(body, default=None)
            if data is None: raise ValueError("Civitai returned non-JSON")
            return {"status": "ok", "url": url, "data": data, "error": ""}
    except urllib.error.HTTPError as e:
        try: body = e.read(8192).decode("utf-8", errors="replace")
        except Exception: body = ""
        return {"status":"http_error","url":url,"status_code":e.code,"error":redact_secret(body or e.reason),"data":None}
    except Exception as e:
        return {"status":"error","url":url,"error":redact_secret(e),"data":None}


def _cache_path(kind: str, key: str) -> Path:
    clean = "".join(ch for ch in str(key) if ch.isalnum() or ch in "-_")[:160]
    return CACHE_ROOT / kind / f"{clean}.json"


def _read_cache(kind: str, key: str) -> dict[str, Any] | None:
    p = _cache_path(kind, key)
    if not p.exists(): return None
    try:
        d = json.loads(p.read_text(encoding="utf-8")); d.setdefault("cache", {})["cache_hit"] = True; d["cache"]["cache_path"] = str(p); return d
    except Exception: return None


def _write_cache(kind: str, key: str, data: dict[str, Any]) -> None:
    p = _cache_path(kind, key)
    wrapped = dict(data); wrapped["cache"] = {"cached_at_unix": time.time(), "cache_key": key, "cache_kind": kind, "cache_hit": False, "cache_path": str(p)}
    atomic_write_text(p, json_dumps(wrapped))


def _cached(kind: str, key: str, fetch_func, cache_policy: str) -> dict[str, Any]:
    if cache_policy in {"read_cache_first", "cache_only"}:
        c = _read_cache(kind, key)
        if c is not None: return c
        if cache_policy == "cache_only": return {"status":"cache_miss","error":"No cached Civitai result","data":None}
    r = fetch_func()
    if r.get("status") == "ok" and cache_policy != "network_only": _write_cache(kind, key, r)
    return r


def lookup_by_hash(sha256: str, **kw) -> dict[str, Any]:
    sha = str(sha256 or "").strip().lower()
    if not sha: return {"status":"missing_hash","error":"No SHA256 hash supplied","data":None}
    cp = kw.pop("cache_policy", "read_cache_first")
    return _cached("by_hash", sha, lambda: api_get(f"/api/v1/model-versions/by-hash/{urllib.parse.quote(sha)}", **kw), cp)


def lookup_by_model_version_id(model_version_id: int, **kw) -> dict[str, Any]:
    key = str(int(model_version_id)); cp = kw.pop("cache_policy", "read_cache_first")
    return _cached("by_version", key, lambda: api_get(f"/api/v1/model-versions/{key}", **kw), cp)


def lookup_by_model_id(model_id: int, **kw) -> dict[str, Any]:
    key = str(int(model_id)); cp = kw.pop("cache_policy", "read_cache_first")
    return _cached("by_model", key, lambda: api_get(f"/api/v1/models/{key}", **kw), cp)


def _first_image(data: dict[str, Any]) -> dict[str, Any]:
    imgs = data.get("images") or []
    if isinstance(imgs, list) and imgs and isinstance(imgs[0], dict): return imgs[0]
    versions = data.get("modelVersions") or []
    if isinstance(versions, list) and versions and isinstance(versions[0], dict):
        imgs = versions[0].get("images") or []
        if isinstance(imgs, list) and imgs and isinstance(imgs[0], dict): return imgs[0]
    return {}


def _primary_file(data: dict[str, Any]) -> dict[str, Any]:
    files = data.get("files") or []
    if not files and isinstance(data.get("modelVersions"), list) and data["modelVersions"] and isinstance(data["modelVersions"][0], dict): files = data["modelVersions"][0].get("files") or []
    if not isinstance(files, list): return {}
    return next((f for f in files if isinstance(f, dict) and f.get("primary")), files[0] if files and isinstance(files[0], dict) else {})


def summarize_model_version(api_result: dict[str, Any]) -> dict[str, Any]:
    data = api_result.get("data") if isinstance(api_result, dict) else None
    if not isinstance(data, dict):
        return {"schema_version":"0.1.0","type":"civitai_model_version","status":api_result.get("status","error") if isinstance(api_result,dict) else "error","error":api_result.get("error","") if isinstance(api_result,dict) else "Invalid result","normalized":{},"raw":api_result}
    img = _first_image(data); pf = _primary_file(data); model = data.get("model") if isinstance(data.get("model"), dict) else {}
    model_id = data.get("modelId") or model.get("id") or ""; version_id = data.get("id", "")
    n = {"model_name": data.get("modelName") or model.get("name") or data.get("name") or "", "model_id": model_id, "model_version_id": version_id, "model_version_name": data.get("name", ""), "model_type": model.get("type") or data.get("type") or "", "base_model": data.get("baseModel", ""), "trained_words": data.get("trainedWords") or [], "download_url": data.get("downloadUrl", ""), "model_url": f"https://civitai.com/models/{model_id}?modelVersionId={version_id}" if model_id and version_id else "", "thumbnail_url": img.get("url", ""), "first_image_meta": img.get("meta"), "primary_file": pf, "file_hashes": pf.get("hashes", {}) if isinstance(pf, dict) else {}, "file_format": pf.get("format", "") if isinstance(pf, dict) else "", "pickle_scan_result": pf.get("pickleScanResult", "") if isinstance(pf, dict) else "", "virus_scan_result": pf.get("virusScanResult", "") if isinstance(pf, dict) else "", "nsfw": data.get("nsfw") or model.get("nsfw") or False}
    return {"schema_version":"0.1.0","type":"civitai_model_version","status":api_result.get("status","ok"),"error":api_result.get("error",""),"normalized":n,"safety":{"network_used": api_result.get("status") == "ok" and not api_result.get("cache",{}).get("cache_hit",False), "token_stored": False, "downloads_model_files": False},"cache":api_result.get("cache",{}),"raw":data}


def download_thumbnail_bytes(url: str, civitai_api_token: str = "", use_env_token: bool = True, network_enabled: bool = False, timeout_seconds: int = 20, max_bytes: int = MAX_THUMBNAIL_BYTES) -> tuple[bytes | None, str]:
    if not network_enabled: return None, "network_disabled"
    try: url = validate_https_url(url, ALLOWED_IMAGE_HOSTS)
    except Exception as e: return None, f"invalid_url: {e}"
    headers = {"Accept":"image/*","User-Agent":"ComfyUI-Metadata-Toolkit/0.1"}
    tok = _token(civitai_api_token, use_env_token)
    if tok: headers["Authorization"] = f"Bearer {tok}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers, method="GET"), timeout=max(1, int(timeout_seconds))) as resp:
            ct = resp.headers.get("Content-Type", "")
            if not ct.lower().startswith("image/"): return None, f"unexpected_content_type: {ct}"
            return _read_limited(resp, max_bytes), "ok"
    except Exception as e:
        return None, redact_secret(e)

from __future__ import annotations

import json
import re
import time
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from ..database import Database, now_iso
from ..jobs import CancelledJobError
from ..schemas import DownloadRequest
from ..utils import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, normalize_tag, tag_for_source_query, tag_string, write_text
from .preset_service import PresetService
from .tag_service import TagService


def _raise_if_cancelled(progress=None) -> None:
    checker = getattr(progress, "cancel_requested", None) if progress is not None else None
    event = getattr(progress, "cancel_event", None) if progress is not None else None
    try:
        if callable(checker) and checker():
            raise CancelledJobError("Cancelled by user")
        if event is not None and getattr(event, "is_set", lambda: False)():
            raise CancelledJobError("Cancelled by user")
    except CancelledJobError:
        raise
    except Exception:
        return


def _cancelable_sleep(seconds: float, progress=None) -> None:
    end = time.time() + max(0.0, float(seconds or 0.0))
    while True:
        _raise_if_cancelled(progress)
        remaining = end - time.time()
        if remaining <= 0:
            return
        time.sleep(min(0.25, remaining))


BOORU_SOURCES: dict[str, dict[str, Any]] = {
    "e621": {
        "label": "e621 JSON API",
        "api_url": "https://e621.net/posts.json",
        "results_key": "posts",
        "file_url_key": "file.url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "page",
        "max_limit": 320,
        "delay_seconds": 1.0,
        "sort_newest": "order:id_desc",
        "sort_oldest": "order:id_asc",
        "notes": "Requires a descriptive User-Agent and user authorization/compliance with the source rules.",
    },
    "e926": {
        "label": "e926 JSON API",
        "api_url": "https://e926.net/posts.json",
        "results_key": "posts",
        "file_url_key": "file.url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "page",
        "max_limit": 320,
        "delay_seconds": 1.0,
        "sort_newest": "order:id_desc",
        "sort_oldest": "order:id_asc",
    },
    "danbooru": {
        "label": "Danbooru JSON API",
        "api_url": "https://danbooru.donmai.us/posts.json",
        "file_url_key": "file_url",
        "large_file_url_key": "large_file_url",
        "tags_key": "tag_string",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "page",
        "max_limit": 200,
        "delay_seconds": 1.0,
        "sort_newest": "order:id_desc",
        "sort_oldest": "order:id_asc",
    },
    "gelbooru": {
        "label": "Gelbooru DAPI JSON",
        "api_url": "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1",
        "results_key": "post",
        "file_url_key": "file_url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "pid",
        "max_limit": 100,
        "delay_seconds": 1.0,
        "sort_newest": "sort:id:desc",
        "sort_oldest": "sort:id:asc",
    },
    "safebooru": {
        "label": "Safebooru DAPI JSON",
        "api_url": "https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1",
        "results_key": "post",
        "file_url_key": "file_url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "pid",
        "max_limit": 100,
        "delay_seconds": 1.0,
        "sort_newest": "sort:id:desc",
        "sort_oldest": "sort:id:asc",
    },
    "rule34": {
        "label": "Rule34 DAPI JSON",
        "api_url": "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1",
        "results_key": "post",
        "file_url_key": "file_url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "pid",
        "max_limit": 100,
        "delay_seconds": 1.0,
        "sort_newest": "sort:id:desc",
        "sort_oldest": "sort:id:asc",
    },
    "konachan": {
        "label": "Konachan JSON API",
        "api_url": "https://konachan.com/post.json",
        "file_url_key": "file_url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "page",
        "max_limit": 100,
        "delay_seconds": 1.0,
        "sort_newest": "order:id_desc",
        "sort_oldest": "order:id_asc",
    },
    "yandere": {
        "label": "Yande.re JSON API",
        "api_url": "https://yande.re/post.json",
        "file_url_key": "file_url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "page_param": "page",
        "max_limit": 100,
        "delay_seconds": 1.0,
        "sort_newest": "order:id_desc",
        "sort_oldest": "order:id_asc",
    },
    "generic-json": {
        "label": "Generic JSON Source",
        "api_url": None,
        "file_url_key": "file_url",
        "tags_key": "tags",
        "tags_param": "tags",
        "limit_param": "limit",
        "max_limit": 100,
        "delay_seconds": 1.0,
    },
}


DEFAULT_DOWNLOAD_CATEGORIES = ["general", "artist", "character", "copyright", "species", "meta", "rating", "style", "concept"]


_LOGIC_OPERATORS = {"AND", "OR", "NOT", "&&", "||", "!", "&", "|", "-"}
_LOGIC_STARTERS = {"TAG", "LPAREN", "NOT"}
_LOGIC_ENDERS = {"TAG", "RPAREN"}


_LOGIC_KEYWORDS = {"AND", "OR", "NOT", "EXCEPT"}


def _logic_boundary_before(src: str, index: int) -> bool:
    if index <= 0:
        return True
    prev = src[index - 1]
    return prev.isspace() or prev in "(,|&!"


def _logic_boundary_after(src: str, index: int) -> bool:
    if index >= len(src):
        return True
    nxt = src[index]
    return nxt.isspace() or nxt in "),|&!"


def _match_logic_keyword(src: str, index: int) -> tuple[str, int] | None:
    """Return an explicit Boolean keyword token at index.

    Tag text can contain spaces, so whitespace alone is never a separator.
    Boolean words are accepted case-insensitively when they appear as a
    standalone logic word at a structural boundary. Tags that literally contain
    these words can still be wrapped in quotes, e.g. ``"black and white"``.
    Symbol operators remain unambiguous: ``&&``, ``||``, ``!``, ``-tag``,
    commas, and parentheses.
    """
    for word in sorted(_LOGIC_KEYWORDS, key=len, reverse=True):
        end = index + len(word)
        if src[index:end].upper() != word:
            continue
        before_ok = _logic_boundary_before(src, index)
        after_ok = _logic_boundary_after(src, end)
        if before_ok and after_ok:
            return ("NOT" if word == "EXCEPT" else word, end)
    return None


def _logic_tokenize(expression: str) -> list[tuple[str, str]]:
    """Tokenize a booru/e621 Boolean tag expression.

    Supported examples:
      cat AND (solo OR duo) AND NOT sketch
      wolf && (male || female) && -animated
      blue eyes AND (red hair OR black fur)
      rating:s AND score:>100 AND (standing OR sitting)

    Commas are treated as AND separators. Whitespace inside tag names is
    preserved; whitespace alone is not a tag separator. Use AND/OR/NOT,
    parentheses, symbols, or commas to separate clauses.
    """
    src = str(expression or "").strip()
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(src):
        ch = src[i]
        if ch.isspace():
            i += 1
            continue
        kw = _match_logic_keyword(src, i)
        if kw:
            kind, end = kw
            tokens.append((kind, kind))
            i = end
            continue
        if ch == ',':
            tokens.append(("AND", "AND"))
            i += 1
            continue
        if ch == '(':
            tokens.append(("LPAREN", ch)); i += 1; continue
        if ch == ')':
            tokens.append(("RPAREN", ch)); i += 1; continue
        if src.startswith('&&', i):
            tokens.append(("AND", "AND")); i += 2; continue
        if src.startswith('||', i):
            tokens.append(("OR", "OR")); i += 2; continue
        if ch == '&':
            tokens.append(("AND", "AND")); i += 1; continue
        if ch == '|':
            tokens.append(("OR", "OR")); i += 1; continue
        if ch == '!':
            tokens.append(("NOT", "NOT")); i += 1; continue
        if ch == '-':
            tokens.append(("NOT", "NOT")); i += 1; continue
        if ch in {'"', "'"}:
            quote = ch
            i += 1
            buf = []
            while i < len(src):
                if src[i] == '\\' and i + 1 < len(src):
                    buf.append(src[i + 1]); i += 2; continue
                if src[i] == quote:
                    break
                buf.append(src[i]); i += 1
            if i >= len(src) or src[i] != quote:
                raise ValueError("Unclosed quote in downloader logic expression.")
            i += 1
            value = "".join(buf).strip()
            if value:
                tokens.append(("TAG", value))
            continue

        start = i
        while i < len(src):
            ch = src[i]
            if ch in '(),&|!':
                break
            if ch == '-':
                # A hyphen only acts as a negative operator at token start. Inside
                # a tag it remains part of the tag text.
                if i == start:
                    break
                i += 1
                continue
            if ch.isspace():
                j = i
                while j < len(src) and src[j].isspace():
                    j += 1
                if j >= len(src):
                    i = j
                    break
                if _match_logic_keyword(src, j) or src[j] in '(),&|!':
                    break
                # Preserve internal spaces as tag text, but skip over repeated
                # whitespace efficiently. normalize_tag() handles final cleanup.
                i = j
                continue
            kw = _match_logic_keyword(src, i)
            if kw:
                break
            i += 1
        word = src[start:i].strip()
        if word:
            tokens.append(("TAG", word))
    # Insert implicit AND between adjacent structural terms, not whitespace-separated
    # tag text: "cat (solo OR duo)" and "cat -sketch" still work.
    out: list[tuple[str, str]] = []
    for tok in tokens:
        if out and out[-1][0] in _LOGIC_ENDERS and tok[0] in _LOGIC_STARTERS:
            out.append(("AND", "AND"))
        out.append(tok)
    return out


class _BooruLogicParser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self, kind: str | None = None) -> tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of downloader logic expression.")
        if kind is not None and tok[0] != kind:
            raise ValueError(f"Expected {kind}, got {tok[0]} ({tok[1]!r}).")
        self.pos += 1
        return tok

    def parse(self):
        if not self.tokens:
            return None
        node = self.parse_or()
        if self.peek() is not None:
            tok = self.peek()
            raise ValueError(f"Unexpected token {tok[1]!r} in downloader logic expression.")
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek() and self.peek()[0] == "OR":
            self.take("OR")
            node = ("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_unary()
        while self.peek() and self.peek()[0] == "AND":
            self.take("AND")
            node = ("and", node, self.parse_unary())
        return node

    def parse_unary(self):
        tok = self.peek()
        if tok and tok[0] == "NOT":
            self.take("NOT")
            return ("not", self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("Expected tag or grouped expression.")
        if tok[0] == "TAG":
            return ("tag", self.take("TAG")[1])
        if tok[0] == "LPAREN":
            self.take("LPAREN")
            node = self.parse_or()
            self.take("RPAREN")
            return node
        raise ValueError(f"Expected tag or '(', got {tok[1]!r}.")


def _normalize_logic_tag(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    # Keep booru operators such as rating:s, score:>100, order:id_desc intact.
    if re.match(r"^[A-Za-z0-9_.:+*/<>~=\[\]{}@#%^-]+$", text):
        return text
    return normalize_tag(text)


def _logic_dnf(node, *, negated: bool = False) -> list[tuple[set[str], set[str]]]:
    if node is None:
        return [(set(), set())]
    kind = node[0]
    if kind == "tag":
        tag = _normalize_logic_tag(node[1])
        if not tag:
            return [(set(), set())]
        return [(set(), {tag})] if negated else [({tag}, set())]
    if kind == "not":
        return _logic_dnf(node[1], negated=not negated)
    if kind == "or":
        if negated:
            return _logic_and(_logic_dnf(node[1], negated=True), _logic_dnf(node[2], negated=True))
        return _logic_dnf(node[1], negated=False) + _logic_dnf(node[2], negated=False)
    if kind == "and":
        if negated:
            return _logic_dnf(node[1], negated=True) + _logic_dnf(node[2], negated=True)
        return _logic_and(_logic_dnf(node[1], negated=False), _logic_dnf(node[2], negated=False))
    raise ValueError(f"Unknown logic node: {kind!r}")


def _logic_and(left: list[tuple[set[str], set[str]]], right: list[tuple[set[str], set[str]]]) -> list[tuple[set[str], set[str]]]:
    out: list[tuple[set[str], set[str]]] = []
    for lp, ln in left:
        for rp, rn in right:
            pos = set(lp) | set(rp)
            neg = set(ln) | set(rn)
            if pos & neg:
                continue
            out.append((pos, neg))
    return out


def expand_booru_logic_query(expression: str, *, max_clauses: int = 64) -> list[dict[str, list[str]]]:
    """Expand a Boolean tag expression into booru-compatible positive/negative clauses.

    Booru APIs generally accept whitespace AND and minus-prefixed negative tags. OR
    is therefore executed as multiple source queries with the downloader's normal
    cross-preset dedupe. The function returns a list of clauses; each clause has
    `positive` and `negative` tag arrays.
    """
    tokens = _logic_tokenize(expression)
    if not tokens:
        return []
    ast = _BooruLogicParser(tokens).parse()
    clauses = _logic_dnf(ast)
    normalized: list[dict[str, list[str]]] = []
    seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
    for pos, neg in clauses:
        pos_list = sorted(x for x in pos if x)
        neg_list = sorted(x for x in neg if x)
        if set(pos_list) & set(neg_list):
            continue
        key = (tuple(pos_list), tuple(neg_list))
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"positive": pos_list, "negative": neg_list})
        if len(normalized) > max_clauses:
            raise ValueError(f"Downloader logic expression expanded to more than {max_clauses} source queries. Narrow the OR branches or raise logic_max_clauses.")
    return normalized


def booru_logic_summary(expression: str, *, max_clauses: int = 64) -> dict[str, Any]:
    clauses = expand_booru_logic_query(expression, max_clauses=max_clauses)
    return {"query": expression, "clauses": clauses, "count": len(clauses), "max_clauses": max_clauses}



def source_definitions() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": value.get("label", key),
            "notes": value.get("notes", "Run only where downloads are permitted and desired by the user."),
            "max_limit": value.get("max_limit", 100),
            "supports_date_range": True,
            "supports_order": bool(value.get("sort_newest") or value.get("sort_oldest")),
            "supports_sort_order": True,
            "supports_download_all_posts": True,
            "dedupe_across_presets_default": True,
            "duplicates_media_in_category_folders_by_default": False,
            "categories": DEFAULT_DOWNLOAD_CATEGORIES,
            "category_options": DEFAULT_DOWNLOAD_CATEGORIES,
            "parallel_download_supported": True,
            "supports_logic_gates": True,
            "supports_preflight_count": True,
            "blacklists_applied_by_default": False,
            "content_filter_keys": ["animated", "video", "3d", "blender", "render", "images", "audio", "other"],
            "rating_filter_keys": ["safe", "questionable", "explicit"],
            "logic_gate_modes": ["boolean_expand", "raw_append"],
            "logic_gate_syntax": "AND / OR / NOT / parentheses; lower-case and/or/not, && || ! commas and -tag aliases are accepted. Whitespace inside tag names is preserved; whitespace alone is not a separator. Quote tags that literally contain operator words. OR expands into multiple deduped source queries.",
            "default_delay_seconds": value.get("delay_seconds", 1.0),
            "default_timeout_seconds": value.get("timeout_seconds", 60),
        }
        for key, value in BOORU_SOURCES.items()
    ]




BOORU_SOURCE_FIXTURES: dict[str, Any] = {
    "e621": {"posts": [{"id": 1, "file": {"url": "https://static.example/e621.png"}, "tags": {"general": ["solo"], "character": ["example_character"]}}]},
    "e926": {"posts": [{"id": 1, "file": {"url": "https://static.example/e926.png"}, "tags": {"general": ["safe"], "species": ["wolf"]}}]},
    "danbooru": [{"id": 1, "file_url": "https://static.example/danbooru.jpg", "large_file_url": "https://static.example/danbooru-large.jpg", "tag_string": "solo blue_eyes"}],
    "gelbooru": {"post": [{"id": 1, "file_url": "https://static.example/gelbooru.jpg", "tags": "solo blue_eyes"}]},
    "safebooru": {"post": [{"id": 1, "file_url": "https://static.example/safebooru.jpg", "tags": "solo safe"}]},
    "rule34": {"post": [{"id": 1, "file_url": "https://static.example/rule34.jpg", "tags": "solo tag"}]},
    "konachan": [{"id": 1, "file_url": "https://static.example/konachan.jpg", "tags": "solo scenic"}],
    "yandere": [{"id": 1, "file_url": "https://static.example/yandere.jpg", "tags": "solo scenic"}],
    "generic-json": [{"file_url": "https://static.example/generic.png", "tags": ["generic", "tag"]}],
}


def validate_source_configs() -> dict[str, Any]:
    """Offline fixture validation for all bundled booru/generic sources."""
    rows: list[dict[str, Any]] = []
    all_ok = True
    for key, cfg in BOORU_SOURCES.items():
        missing = []
        for field in ["file_url_key", "tags_key", "tags_param", "limit_param"]:
            if not cfg.get(field):
                missing.append(field)
        if key != "generic-json" and not cfg.get("api_url"):
            missing.append("api_url")
        sample_item = _sample_item_for_source(key)
        sample_tags = _extract_tags(sample_item, cfg.get("tags_key")) if sample_item else []
        sample_url = str(_nested_get(sample_item, cfg.get("file_url_key")) or (cfg.get("large_file_url_key") and _nested_get(sample_item, cfg.get("large_file_url_key"))) or "") if sample_item else ""
        ok = bool(not missing and sample_url and sample_tags)
        all_ok = all_ok and ok
        rows.append({
            "source": key,
            "key": key,
            "label": cfg.get("label", key),
            "ok": ok,
            "missing": missing,
            "error": "" if ok else f"missing={missing}, sample_url={sample_url!r}, sample_tags={sample_tags!r}",
            "api_url": cfg.get("api_url"),
            "page_param": cfg.get("page_param"),
            "limit_param": cfg.get("limit_param"),
            "tags_param": cfg.get("tags_param"),
            "results_key": cfg.get("results_key"),
            "file_url_key": cfg.get("file_url_key"),
            "tags_key": cfg.get("tags_key"),
            "sample_url": sample_url,
            "sample_tags": sample_tags,
            "sort_newest": cfg.get("sort_newest"),
            "sort_oldest": cfg.get("sort_oldest"),
            "default_delay_seconds": cfg.get("delay_seconds", 1.0),
            "notes": cfg.get("notes", ""),
        })
    return {"ok": all_ok, "sources": rows, "count": len(rows)}


CONTENT_FILTER_TAGS: dict[str, tuple[str, ...]] = {
    "animated": ("animated", "animation"),
    "3d": ("3d", "3d_(artwork)", "3d_artwork"),
    "blender": ("blender",),
    "render": ("render", "rendered", "3d_render", "cgi"),
}
RATING_ALIASES = {
    "s": "s", "safe": "s", "rating:s": "s", "rating_safe": "s",
    "q": "q", "questionable": "q", "rating:q": "q", "rating_questionable": "q",
    "e": "e", "explicit": "e", "rating:e": "e", "rating_explicit": "e",
    "g": "g", "general": "g", "rating:g": "g", "rating_general": "g",
}

def _rating_codes(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        code = RATING_ALIASES.get(str(raw or "").strip().lower())
        if code and code not in seen:
            seen.add(code)
            out.append(code)
    return out

def _item_ext(item: dict[str, Any], cfg: dict[str, Any], url: str | None = None) -> str:
    for key in ("file.ext", "ext", "file_ext", "file.extension", "image", "sample.ext"):
        value = _nested_get(item, key)
        if isinstance(value, str) and value.strip():
            clean = value.strip().lower().lstrip(".")
            if 1 <= len(clean) <= 8 and re.fullmatch(r"[a-z0-9]+", clean):
                return f".{clean}"
    candidate = str(url or _nested_get(item, cfg.get("file_url_key")) or "")
    try:
        path = urlparse(candidate).path
        suffix = Path(path).suffix.lower()
        return suffix
    except Exception:
        return ""

def _item_rating(item: dict[str, Any]) -> str:
    for key in ("rating", "post.rating", "safe_rating"):
        value = _nested_get(item, key)
        if value not in (None, "", [], {}):
            text = str(value).strip().lower()
            return RATING_ALIASES.get(text, text[:1] if text else "")
    tags = {tag_for_source_query(t).lower() for t in _extract_tags(item, "tags")}
    for tag in tags:
        code = RATING_ALIASES.get(tag)
        if code:
            return code
    return ""

def _item_has_any_tag(item: dict[str, Any], cfg: dict[str, Any], candidates: tuple[str, ...]) -> bool:
    tags = {tag_for_source_query(t).lower() for t in _extract_tags(item, cfg.get("tags_key"))}
    normalized = {tag_for_source_query(t).lower() for t in candidates}
    return bool(tags.intersection(normalized))

def _item_allowed_by_request(item: dict[str, Any], cfg: dict[str, Any], request: DownloadRequest | None, source_url: str | None = None) -> bool:
    if request is None:
        return True
    ratings = set(_rating_codes(getattr(request, "rating_filter", []) or []))
    if ratings:
        rating = _item_rating(item)
        if rating and rating not in ratings:
            return False
    ext = _item_ext(item, cfg, source_url)
    if ext in IMAGE_EXTENSIONS and not bool(getattr(request, "allow_images", True)):
        return False
    if ext in VIDEO_EXTENSIONS and not bool(getattr(request, "allow_video", True)):
        return False
    if ext in AUDIO_EXTENSIONS and not bool(getattr(request, "allow_audio", True)):
        return False
    if ext and ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS and ext not in AUDIO_EXTENSIONS and not bool(getattr(request, "allow_other_media", True)):
        return False
    if not bool(getattr(request, "allow_animated", True)) and (ext == ".gif" or _item_has_any_tag(item, cfg, CONTENT_FILTER_TAGS["animated"])):
        return False
    for key, tags in (("3d", CONTENT_FILTER_TAGS["3d"]), ("blender", CONTENT_FILTER_TAGS["blender"]), ("render", CONTENT_FILTER_TAGS["render"])):
        attr = f"allow_{key}" if key != "3d" else "allow_3d"
        if not bool(getattr(request, attr, True)) and _item_has_any_tag(item, cfg, tags):
            return False
    return True

def _download_eta(started_at: float, done: int, total: int | None) -> str:
    elapsed = max(0.001, time.time() - started_at)
    rate = done / elapsed if done > 0 else 0.0
    if not total or done <= 0 or rate <= 0:
        return f"elapsed {elapsed/60:.1f}m"
    remaining = max(0, total - done) / rate
    return f"elapsed {elapsed/60:.1f}m · ETA {remaining/60:.1f}m"

def _sample_item_for_source(key: str) -> dict[str, Any]:
    if key in {"e621", "e926"}:
        return {"file": {"url": f"https://example.invalid/{key}.png"}, "tags": {"general": ["blue_fur", "solo"], "character": ["sample_character"]}}
    if key == "danbooru":
        return {"file_url": "https://example.invalid/danbooru.jpg", "large_file_url": "https://example.invalid/danbooru_large.jpg", "tag_string": "solo blue_hair"}
    if key in {"gelbooru", "safebooru", "rule34", "konachan", "yandere"}:
        return {"file_url": f"https://example.invalid/{key}.jpg", "tags": "solo blue_hair"}
    return {"file_url": "https://example.invalid/generic.jpg", "tags": ["solo", "blue_hair"]}

class DownloaderService:
    def __init__(self, db: Database, presets: PresetService, user_agent: str = "DataCurationTool/5.36.0", tags: TagService | None = None):
        self.db = db
        self.presets = presets
        self.user_agent = user_agent
        self.tags = tags

    def validate_source_configurations(self, live: bool = False) -> dict[str, Any]:
        result = validate_source_configs()
        if not live:
            result["live"] = False
            return result
        live_rows: list[dict[str, Any]] = []
        for key, cfg in BOORU_SOURCES.items():
            if key == "generic-json" or not cfg.get("api_url"):
                live_rows.append({"key": key, "live_ok": None, "message": "generic/custom source; no live URL to smoke test"})
                continue
            params = {cfg.get("limit_param", "limit"): 1}
            if cfg.get("tags_param"):
                params[cfg.get("tags_param", "tags")] = ""
            if cfg.get("page_param"):
                params[cfg["page_param"]] = 0 if cfg["page_param"] == "pid" else 1
            try:
                response = requests.get(
                    cfg["api_url"],
                    params=params,
                    headers={"User-Agent": self.user_agent},
                    timeout=10,
                )
                response.raise_for_status()
                payload = response.json()
                items = _nested_get(payload, cfg.get("results_key")) if cfg.get("results_key") else payload
                if isinstance(items, dict) and "post" in items:
                    items = items.get("post")
                live_rows.append({
                    "key": key,
                    "live_ok": True,
                    "status_code": response.status_code,
                    "url": response.url,
                    "items_type": type(items).__name__,
                    "items_seen": len(items) if isinstance(items, list) else None,
                })
            except Exception as exc:
                live_rows.append({"key": key, "live_ok": False, "error": str(exc)})
        result["live"] = True
        result["live_sources"] = live_rows
        result["live_ok"] = all(row.get("live_ok") is not False for row in live_rows)
        return result

    def validate_sources(self, live: bool = False, tags: str = "", limit: int = 1, timeout_seconds: int = 20) -> dict[str, Any]:
        results = []
        for key in BOORU_SOURCES:
            if live:
                results.append(self.validate_source(key, tags=tags, limit=limit, timeout_seconds=timeout_seconds))
            else:
                results.append(self._validate_source_fixture(key))
        return {"ok": all(r.get("ok") for r in results), "live": bool(live), "results": results}

    def _validate_source_fixture(self, source: str) -> dict[str, Any]:
        cfg = dict(BOORU_SOURCES.get(source, {}))
        if not cfg:
            return {"ok": False, "source": source, "error": "missing source config"}
        sample_by_source = {
            "e621": {"file": {"url": "https://static1.e621.net/data/sample.jpg"}, "tags": {"general": ["sample_tag"], "artist": ["artist_name"]}},
            "e926": {"file": {"url": "https://static1.e926.net/data/sample.jpg"}, "tags": {"general": ["sample_tag"]}},
            "danbooru": {"file_url": "https://cdn.donmai.us/sample.jpg", "large_file_url": "https://cdn.donmai.us/large.jpg", "tag_string": "sample_tag artist_name"},
            "gelbooru": {"file_url": "https://img.gelbooru.com/sample.jpg", "tags": "sample_tag artist_name"},
            "safebooru": {"file_url": "https://safebooru.org/sample.jpg", "tags": "sample_tag artist_name"},
            "rule34": {"file_url": "https://api-cdn.rule34.xxx/sample.jpg", "tags": "sample_tag artist_name"},
            "konachan": {"file_url": "https://konachan.com/sample.jpg", "tags": "sample_tag artist_name"},
            "yandere": {"file_url": "https://yande.re/sample.jpg", "tags": "sample_tag artist_name"},
            "generic-json": {"file_url": "https://example.invalid/sample.jpg", "tags": ["sample_tag", "artist_name"]},
        }
        sample = sample_by_source.get(source, sample_by_source["generic-json"])
        file_url = _nested_get(sample, cfg.get("file_url_key"))
        if not file_url and cfg.get("large_file_url_key"):
            file_url = _nested_get(sample, cfg.get("large_file_url_key"))
        tags = _extract_tags(sample, cfg.get("tags_key"))
        missing = []
        for field in ["file_url_key", "tags_key", "tags_param", "limit_param"]:
            if not cfg.get(field):
                missing.append(field)
        return {
            "ok": bool(file_url and tags and not missing),
            "source": source,
            "label": cfg.get("label", source),
            "sample_file_url": file_url,
            "sample_tags": tags,
            "missing_config": missing,
            "page_param": cfg.get("page_param"),
            "max_limit": cfg.get("max_limit"),
        }

    def _collect_request_presets(self, request: DownloadRequest) -> list[dict[str, Any]]:
        presets: list[dict[str, Any]] = []
        if request.preset:
            presets.append(request.preset.model_dump())
        for direct_preset in getattr(request, "presets", []) or []:
            presets.append(direct_preset.model_dump() if hasattr(direct_preset, "model_dump") else dict(direct_preset))
        for name in request.preset_names:
            preset = self.presets.get(name)
            if preset:
                presets.append(preset)
        return presets

    def _prepare_presets(self, request: DownloadRequest) -> list[dict[str, Any]]:
        presets = self._collect_request_presets(request)
        if not presets:
            raise ValueError("No download presets selected.")
        presets = self._expand_presets_for_categories(presets, request)
        presets = self._expand_presets_for_logic(presets, request)
        if not presets:
            raise ValueError("No tags were found for the selected download category/profile or logic expression.")
        return presets

    def _resolved_source_config(self, preset: dict[str, Any], request: DownloadRequest | None = None) -> tuple[str, dict[str, Any], dict[str, Any]]:
        source = preset.get("source", "generic-json")
        if source == "booru":
            source = "e621"
        preset_options = dict(preset.get("options") or {})
        if source == "generic-json" and not preset_options.get("api_url") and request is not None:
            profile_source = str(getattr(request, "tag_profile", "") or "").strip()
            if profile_source in BOORU_SOURCES and profile_source != "generic-json":
                source = profile_source
                preset = {**preset, "source": source, "name": str(preset.get("name") or "direct").replace("direct-generic-json", f"direct-{source}", 1)}
        if source not in BOORU_SOURCES:
            raise ValueError(f"Unsupported source plugin: {source}")
        cfg = dict(BOORU_SOURCES[source])
        cfg.update(preset_options)
        # Apply preset-local output settings before request-level settings.
        #
        # Direct UI presets are validated by Pydantic, so omitted fields are
        # materialized with defaults such as filename_mode="hash_original".  In
        # v5.78.8 those defaults were applied after the page/run-level controls
        # and therefore overwrote a user-selected "Post ID only" mode.  The
        # run-level DownloadRequest values must be authoritative because the
        # dropdown on the Downloads page describes the current run, including
        # direct multi-source and saved-preset runs.
        preset_filename_mode = preset.get("filename_mode")
        if preset_filename_mode:
            cfg["filename_mode"] = str(preset_filename_mode)
        if "write_metadata_json_sidecar" in preset:
            cfg["write_metadata_json_sidecar"] = bool(preset.get("write_metadata_json_sidecar"))
        if "write_tag_txt_sidecar" in preset:
            cfg["write_tag_txt_sidecar"] = bool(preset.get("write_tag_txt_sidecar"))
        if request is not None:
            if request.api_delay_seconds is not None:
                cfg["delay_seconds"] = max(0.0, float(request.api_delay_seconds))
            if request.file_delay_seconds is not None:
                cfg["file_delay_seconds"] = max(0.0, float(request.file_delay_seconds))
            if request.request_timeout_seconds is not None:
                cfg["timeout_seconds"] = max(5, int(request.request_timeout_seconds))
            if request.max_retries is not None:
                cfg["max_retries"] = max(0, int(request.max_retries))
            if request.retry_backoff_seconds is not None:
                cfg["retry_backoff_seconds"] = max(0.0, float(request.retry_backoff_seconds))
            cfg["force_download"] = bool(getattr(request, "force_download", False))
            cfg["filename_mode"] = str(getattr(request, "filename_mode", "hash_original") or "hash_original")
            cfg["write_metadata_json_sidecar"] = bool(getattr(request, "write_metadata_json_sidecar", True))
            cfg["write_tag_txt_sidecar"] = bool(getattr(request, "write_tag_txt_sidecar", True))
            cfg["apply_source_blacklists"] = bool(getattr(request, "apply_source_blacklists", False))
        api_url = cfg.get("api_url")
        if not api_url:
            raise ValueError("This source requires options.api_url")
        return source, preset, cfg

    def preflight(self, request: DownloadRequest, progress=None) -> dict[str, Any]:
        presets = self._prepare_presets(request)
        total_unique = 0
        total_seen = 0
        total_pages = 0
        rows: list[dict[str, Any]] = []
        global_keys: set[str] = set()
        started = time.time()
        for idx, preset in enumerate(presets, start=1):
            source, resolved_preset, cfg = self._resolved_source_config(preset, request)
            api_url = cfg.get("api_url")
            source_max_limit = int(cfg.get("max_limit", 100))
            per_page = source_max_limit if request.download_all_posts else min(int(request.max_items or source_max_limit), source_max_limit)
            page_param = cfg.get("page_param")
            page = int(request.start_page if request.start_page is not None else cfg.get("start_page", 0 if page_param == "pid" else 1))
            max_pages = int(request.max_pages if request.max_pages is not None else cfg.get("max_pages", 0) or 0)
            pages = 0
            unique = 0
            seen = 0
            while request.download_all_posts or seen < int(request.max_items or 1):
                if max_pages and pages >= max_pages:
                    break
                pages += 1
                total_pages += 1
                batch = self._fetch_page(resolved_preset, cfg, api_url, per_page, page if page_param else None, request=request, progress=progress)
                if not batch:
                    break
                for item in batch:
                    url = str(_nested_get(item, cfg.get("file_url_key")) or (cfg.get("large_file_url_key") and _nested_get(item, cfg.get("large_file_url_key"))) or "")
                    if not url or not _item_allowed_by_request(item, cfg, request, url):
                        continue
                    seen += 1
                    total_seen += 1
                    keys = _dedupe_keys_for_item(item, cfg, source, url)
                    compound = [f"{source}:{k}" for k in keys] or [f"url:{url}"]
                    if request.dedupe_across_presets and any(k in global_keys for k in compound):
                        continue
                    global_keys.update(compound)
                    unique += 1
                    total_unique += 1
                    if not request.download_all_posts and unique >= int(request.max_items or 1):
                        break
                if progress:
                    progress(min(0.99, idx / max(len(presets), 1)), f"Preflight counted {total_unique} unique post(s) across {total_pages} page(s); {_download_eta(started, total_unique, None)}")
                if not request.download_all_posts and unique >= int(request.max_items or 1):
                    break
                if not page_param or len(batch) < per_page:
                    break
                page += 1
                delay = float(cfg.get("delay_seconds", 0.0) or 0.0)
                if delay > 0 and (request.download_all_posts or max_pages):
                    _cancelable_sleep(delay, progress)
            rows.append({"preset": resolved_preset.get("name"), "source": source, "pages": pages, "matching_items": seen, "unique_items": unique})
        if progress:
            progress(1.0, f"Preflight complete: {total_unique} unique downloadable post(s) estimated across {len(presets)} expanded query clause(s).")
        return {
            "estimated_total": total_unique,
            "matching_items_seen": total_seen,
            "expanded_presets": len(presets),
            "pages_fetched": total_pages,
            "dedupe_across_presets": bool(request.dedupe_across_presets),
            "download_all_posts": bool(request.download_all_posts),
            "max_pages": request.max_pages,
            "source_blacklists_applied": bool(request.apply_source_blacklists),
            "blacklists_applied_by_default": False,
            "rows": rows,
        }

    def run(self, request: DownloadRequest, progress) -> dict[str, Any]:
        if not request.confirmed_authorized:
            raise PermissionError("Confirm that the configured source permits this download before running.")
        output_dir = Path(request.output_dir or "runtime/downloads").expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        presets = self._prepare_presets(request)
        downloaded: list[str] = []
        workers = max(1, min(int(request.parallel_workers or request.max_concurrent_downloads or 1), 32))
        parallel_presets = bool(request.parallel_presets and workers > 1 and len(presets) > 1)
        all_posts = bool(request.download_all_posts)
        preset_limits = [None if all_posts else max(1, int((preset.get("options") or {}).get("_max_items") or request.max_items or 1)) for preset in presets]
        total_expected = None if all_posts else max(1, sum(int(x or 0) for x in preset_limits))
        if all_posts and bool(getattr(request, "estimate_total_before_download", False)):
            progress(0.0, "Preflight counting matching posts before download...")
            try:
                preflight = self.preflight(request, progress=progress)
                estimated = int(preflight.get("estimated_total") or 0)
                if estimated > 0:
                    total_expected = estimated
                    progress(0.0, f"Preflight estimate: {estimated} unique post(s) before download starts.")
            except Exception as exc:
                progress(0.0, f"Preflight estimate failed; continuing with unknown total: {exc}")
        counter_lock = threading.Lock()
        completed_files = 0
        started_at = time.time()
        shared_seen_urls: set[str] = set()
        shared_seen_keys: set[str] = set()
        shared_url_to_path: dict[str, str] = {}
        membership: dict[str, dict[str, Any]] = {}

        def report_file(source: str, path: str | None = None, *, skipped_duplicate: bool = False) -> None:
            nonlocal completed_files
            if skipped_duplicate:
                with counter_lock:
                    done = completed_files
                progress(0.0 if total_expected is None else min(0.99, done / max(total_expected, 1)), f"{source}: skipped duplicate; downloaded {done}" + ("" if total_expected is None else f"/{total_expected}") + f" · {_download_eta(started_at, done, total_expected)}")
                return
            with counter_lock:
                completed_files += 1
                done = completed_files
            if total_expected is None:
                progress(min(0.99, done / max(done + 1, 1)), f"{source}: downloaded {done} file(s); all-posts mode continues until the source is exhausted · {_download_eta(started_at, done, None)}")
            else:
                progress(min(1.0, done / total_expected), f"{source}: downloaded {done}/{total_expected} · {_download_eta(started_at, done, total_expected)}")

        def claim_url(url: str, source: str, preset: dict[str, Any], item: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None) -> bool:
            if not bool(request.dedupe_across_presets):
                return True
            keys = _dedupe_keys_for_item(item or {}, cfg or {}, source, url)
            with counter_lock:
                if url in shared_seen_urls or any(key in shared_seen_keys for key in keys):
                    _record_membership(membership, url, source, preset, shared_url_to_path.get(url))
                    return False
                shared_seen_urls.add(url)
                shared_seen_keys.update(keys)
                _record_membership(membership, url, source, preset, None)
                return True

        def register_url_path(url: str, path: str | None, source: str, preset: dict[str, Any]) -> None:
            if not path:
                return
            with counter_lock:
                shared_url_to_path[url] = path
                _record_membership(membership, url, source, preset, path)

        def run_one(index: int, preset: dict[str, Any]) -> list[str]:
            run_id = self.db.execute(
                """
                INSERT INTO download_runs(source, preset_name, status, output_dir, params_json, created_at, updated_at)
                VALUES (?, ?, 'running', ?, ?, ?, ?)
                """,
                (preset["source"], preset.get("name"), str(output_dir), json.dumps(preset), now_iso(), now_iso()),
            )
            try:
                limit = preset_limits[index - 1] if 0 <= index - 1 < len(preset_limits) else (None if request.download_all_posts else int((preset.get("options") or {}).get("_max_items") or request.max_items or 1))
                files = self._download_source(preset, output_dir, limit, progress, index, len(presets), request=request, download_workers=workers, report_file=report_file, claim_url=claim_url, register_url_path=register_url_path)
                self.db.execute("UPDATE download_runs SET status='completed', updated_at=? WHERE id=?", (now_iso(), run_id))
                return files
            except Exception as exc:
                self.db.execute(
                    "UPDATE download_runs SET status='failed', params_json=?, updated_at=? WHERE id=?",
                    (json.dumps({**preset, "error": str(exc)}), now_iso(), run_id),
                )
                raise

        if parallel_presets:
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dct-download-preset") as ex:
                future_map = {ex.submit(run_one, idx, preset): idx for idx, preset in enumerate(presets, start=1)}
                for fut in as_completed(future_map):
                    downloaded.extend(fut.result())
        else:
            for pidx, preset in enumerate(presets, start=1):
                downloaded.extend(run_one(pidx, preset))
        if request.store_membership_index and membership:
            self._write_membership_index(output_dir, membership)
        if total_expected is None:
            progress(1.0, f"Completed download: {len(downloaded)} unique file(s) (all posts mode)")
        else:
            progress(1.0, f"Completed download: {len(downloaded)}/{total_expected} unique file(s)")
        return {"downloaded": len(downloaded), "files": downloaded, "output_dir": str(output_dir), "expanded_presets": len(presets), "download_all_posts": bool(request.download_all_posts), "deduped_urls": len(shared_seen_urls), "dedupe_keys": len(shared_seen_keys), "membership_index": bool(request.store_membership_index and membership)}

    def _expand_category_presets(self, presets: list[dict[str, Any]], request: DownloadRequest) -> list[dict[str, Any]]:
        """Backward-compatible alias for tests and plugin callers."""
        return self._expand_presets_for_categories(presets, request)

    def _expand_presets_for_categories(self, presets: list[dict[str, Any]], request: DownloadRequest) -> list[dict[str, Any]]:
        categories = list(request.categories or [])
        if request.category and request.category not in categories:
            categories.append(request.category)
        categories = [c.strip().lower() for c in categories if c and c.strip()]
        if request.download_all_categories and not categories:
            categories = DEFAULT_DOWNLOAD_CATEGORIES
        if not (request.download_all_in_category or request.download_all_categories or categories):
            return presets
        expanded: list[dict[str, Any]] = []
        limit = int(request.per_category_limit or request.category_limit or 100)
        per_tag_limit = max(1, int(request.per_tag_limit or 1))
        for preset in presets:
            profile = request.tag_profile or preset.get("source") or "e621"
            for category in categories:
                tags = self._tags_for_category(profile=profile, category=category, limit=limit)
                for tag in tags:
                    clone = json.loads(json.dumps(preset))
                    clone["name"] = f"{preset.get('name') or preset.get('source')}-{category}-{tag}"
                    positives = [normalize_tag(x) for x in clone.get("positive_tags", []) if normalize_tag(x)]
                    if tag not in positives:
                        positives.append(tag)
                    clone["positive_tags"] = positives
                    options = dict(clone.get("options") or {})
                    options["_expanded_category"] = category
                    options["_expanded_category_tag"] = tag
                    options["category"] = category
                    options["category_tag"] = tag
                    options["_max_items"] = per_tag_limit
                    # Avoid category/tag folder duplication by default.  Category membership is tracked in
                    # _download_membership.json instead.  Users can still explicitly opt into legacy duplicate
                    # media folders with allow_duplicate_category_files=True.
                    if request.group_by_tag and request.allow_duplicate_category_files:
                        options["output_subdir"] = f"{_safe_dir(category)}/{_safe_dir(tag)}"
                    clone["options"] = options
                    expanded.append(clone)
        return expanded or presets

    def _expand_presets_for_logic(self, presets: list[dict[str, Any]], request: DownloadRequest) -> list[dict[str, Any]]:
        expanded: list[dict[str, Any]] = []
        request_logic = str(getattr(request, "logic_query", "") or "").strip()
        request_mode = str(getattr(request, "logic_mode", "") or "boolean_expand").strip().lower()
        max_clauses = max(1, int(getattr(request, "logic_max_clauses", 64) or 64))
        for preset in presets:
            options = dict(preset.get("options") or {})
            logic_query = str(options.get("logic_query") or options.get("boolean_query") or request_logic).strip()
            logic_mode = str(options.get("logic_mode") or request_mode or "boolean_expand").strip().lower()
            if not logic_query:
                expanded.append(preset)
                continue
            if logic_mode in {"raw", "raw_append", "append_raw", "source_raw"}:
                clone = json.loads(json.dumps(preset))
                # Logic mode is authoritative. Do not require or silently merge
                # positive/negative boxes when a logic expression is supplied.
                clone["positive_tags"] = []
                clone["negative_tags"] = []
                opts = dict(clone.get("options") or {})
                opts["_logic_raw"] = logic_query
                opts["logic_query"] = logic_query
                opts["logic_mode"] = "raw_append"
                opts["_logic_overrode_manual_tags"] = True
                clone["options"] = opts
                clone["name"] = f"{preset.get('name') or preset.get('source')}-logic-raw"
                expanded.append(clone)
                continue
            clauses = expand_booru_logic_query(logic_query, max_clauses=max_clauses)
            if not clauses:
                expanded.append(preset)
                continue
            for idx, clause in enumerate(clauses, start=1):
                clone = json.loads(json.dumps(preset))
                # Logic expression replaces the positive/negative boxes. This
                # makes the new logic field usable by itself and avoids stale
                # tag-box values accidentally narrowing the query.
                positives: list[str] = []
                negatives: list[str] = []
                for tag in clause.get("positive") or []:
                    tag = normalize_tag(tag)
                    if tag and tag not in positives:
                        positives.append(tag)
                for tag in clause.get("negative") or []:
                    tag = normalize_tag(tag)
                    if tag and tag not in negatives:
                        negatives.append(tag)
                clone["positive_tags"] = positives
                clone["negative_tags"] = negatives
                opts = dict(clone.get("options") or {})
                opts["logic_query"] = logic_query
                opts["logic_mode"] = "boolean_expand"
                opts["_logic_clause"] = {"index": idx, "count": len(clauses), **clause}
                opts["_logic_overrode_manual_tags"] = True
                clone["options"] = opts
                clone["name"] = f"{preset.get('name') or preset.get('source')}-logic-{idx:02d}-of-{len(clauses):02d}"
                expanded.append(clone)
        return expanded or presets

    def _tags_for_category(self, profile: str, category: str, limit: int) -> list[str]:
        profile = (profile or "e621").lower()
        category = (category or "general").lower()
        try:
            rows = self.db.query(
                """
                SELECT tag, MAX(post_count) AS post_count
                FROM tag_dictionary_entries
                WHERE source IN (?, 'custom') AND lower(category)=lower(?)
                GROUP BY tag
                ORDER BY MAX(CASE WHEN source='custom' THEN 1 ELSE 0 END) DESC, post_count DESC, tag ASC
                LIMIT ?
                """,
                (profile, category, int(limit)),
            )
        except Exception:
            rows = []
        tags = [str(r["tag"]) for r in rows]
        return tags or [category]

    def _download_source(self, preset: dict[str, Any], output_dir: Path, max_items: int | None, progress, preset_idx: int, preset_total: int, request: DownloadRequest | None = None, download_workers: int = 1, report_file=None, claim_url=None, register_url_path=None) -> list[str]:
        source, preset, source_cfg = self._resolved_source_config(preset, request)
        _raise_if_cancelled(progress)
        api_url = source_cfg.get("api_url")
        source_max_limit = int(source_cfg.get("max_limit", 100))
        per_page = source_max_limit if max_items is None else min(int(max_items or source_max_limit), source_max_limit)
        page_param = source_cfg.get("page_param")
        downloaded: list[str] = []
        seen_urls: set[str] = set()
        seen_keys: set[str] = set()
        page = int(request.start_page if request and request.start_page is not None else source_cfg.get("start_page", 0 if page_param == "pid" else 1))
        max_pages = int(request.max_pages if request and request.max_pages is not None else source_cfg.get("max_pages", 0) or 0)
        pages_fetched = 0
        while max_items is None or len(downloaded) < max_items:
            if max_pages and pages_fetched >= max_pages:
                break
            pages_fetched += 1
            _raise_if_cancelled(progress)
            try:
                batch = self._fetch_page(preset, source_cfg, api_url, per_page, page if page_param else None, request=request, progress=progress)
            except TypeError as exc:
                # Preserve compatibility with tests/plugins that monkeypatch the
                # older _fetch_page signature without the cooperative progress arg.
                if "progress" not in str(exc):
                    raise
                batch = self._fetch_page(preset, source_cfg, api_url, per_page, page if page_param else None, request=request)
            _raise_if_cancelled(progress)
            if not batch:
                break
            remaining = None if max_items is None else max_items - len(downloaded)
            unique_items: list[dict[str, Any]] = []
            for item in batch:
                url = str(_nested_get(item, source_cfg.get("file_url_key")) or (source_cfg.get("large_file_url_key") and _nested_get(item, source_cfg.get("large_file_url_key"))) or "")
                keys = _dedupe_keys_for_item(item, source_cfg, source, url)
                if not url or not _item_allowed_by_request(item, source_cfg, request, url) or url in seen_urls or any(key in seen_keys for key in keys):
                    continue
                if claim_url is not None and not claim_url(url, source, preset, item, source_cfg):
                    if report_file:
                        report_file(source, None, skipped_duplicate=True)
                    continue
                seen_urls.add(url)
                seen_keys.update(keys)
                unique_items.append(item)
                if remaining is not None and len(unique_items) >= remaining:
                    break
            items = unique_items
            if not items and len(batch) < per_page:
                break
            files: list[str] = []
            item_workers = max(1, min(download_workers, len(items), 16))
            if item_workers > 1:
                with ThreadPoolExecutor(max_workers=item_workers, thread_name_prefix="dct-download-file") as ex:
                    futs = {ex.submit(self._download_item_compat, item, source_cfg, output_dir, preset, progress): item for item in items}
                    for fut in as_completed(futs):
                        item = futs[fut]
                        path = fut.result()
                        if path:
                            files.append(path)
                            if register_url_path:
                                item_url = str(_nested_get(item, source_cfg.get("file_url_key")) or (source_cfg.get("large_file_url_key") and _nested_get(item, source_cfg.get("large_file_url_key"))) or "")
                                if item_url:
                                    register_url_path(item_url, path, source, preset)
                            if report_file:
                                report_file(source, path)
                            else:
                                done = len(downloaded) + len(files)
                                if max_items is None:
                                    progress(min(0.99, done / max(done + 1, 1)), f"{source}: downloaded {done} file(s); all-posts mode")
                                else:
                                    progress(((preset_idx - 1) + done / max(max_items, 1)) / preset_total, f"{source}: downloaded {done}/{max_items}")
            else:
                for item in items:
                    _raise_if_cancelled(progress)
                    path = self._download_item_compat(item, source_cfg, output_dir, preset, progress)
                    if path:
                        files.append(path)
                        if register_url_path:
                            item_url = str(_nested_get(item, source_cfg.get("file_url_key")) or (source_cfg.get("large_file_url_key") and _nested_get(item, source_cfg.get("large_file_url_key"))) or "")
                            if item_url:
                                register_url_path(item_url, path, source, preset)
                        if report_file:
                            report_file(source, path)
                        else:
                            done = len(downloaded) + len(files)
                            if max_items is None:
                                progress(min(0.99, done / max(done + 1, 1)), f"{source}: downloaded {done} file(s); all-posts mode")
                            else:
                                progress(((preset_idx - 1) + done / max(max_items, 1)) / preset_total, f"{source}: downloaded {done}/{max_items}")
                        _cancelable_sleep(float(source_cfg.get("delay_seconds", 1.0)), progress)
            before_extend = len(downloaded)
            downloaded.extend(files)
            if max_items is not None and len(downloaded) >= max_items:
                break
            if not page_param or len(batch) < per_page:
                break
            page += 1
            if not files and before_extend == len(downloaded):
                # A page can contain only duplicates or items excluded by media/rating filters.
                # Continue paging instead of assuming the entire source is exhausted.
                _cancelable_sleep(float(source_cfg.get("delay_seconds", 1.0)), progress)
                continue
            if item_workers > 1:
                # Friendly pacing per API page while file transfers inside page are parallel.
                _cancelable_sleep(float(source_cfg.get("delay_seconds", 1.0)), progress)
        return downloaded

    def _fetch_page(self, preset: dict[str, Any], cfg: dict[str, Any], api_url: str, limit: int, page: int | None, request: DownloadRequest | None = None, progress=None) -> list[dict[str, Any]]:
        _raise_if_cancelled(progress)
        tags = " ".join(tag_for_source_query(tag) for tag in (preset.get("positive_tags") or []) if tag_for_source_query(tag))
        negative = " ".join(f"-{tag_for_source_query(tag)}" for tag in (preset.get("negative_tags") or []) if tag_for_source_query(tag))
        options = dict(preset.get("options") or {})
        raw_logic = str(options.get("_logic_raw") or "").strip()
        extras = [tag_for_source_query(x) if not any(str(x).startswith(prefix) for prefix in ("order:", "sort:", "date:")) else str(x) for x in (self._query_extras(cfg, request) if request else [])]
        params: dict[str, Any] = {
            cfg.get("tags_param", "tags"): " ".join(x for x in [tags, negative, raw_logic, *extras] if x).strip(),
            cfg.get("limit_param", "limit"): limit,
        }
        if page is not None and cfg.get("page_param"):
            params[cfg["page_param"]] = page
        params.update(cfg.get("extra_params") or {})
        response = self._request_with_retries(
            "GET",
            api_url,
            params=params,
            headers={"User-Agent": self.user_agent},
            timeout=int(cfg.get("timeout_seconds", 60) or 60),
            max_retries=int(cfg.get("max_retries", 3) or 0),
            backoff_seconds=float(cfg.get("retry_backoff_seconds", 2.0) or 0.0),
            progress=progress,
        )
        _raise_if_cancelled(progress)
        data = response.json()
        items = _nested_get(data, cfg.get("results_key")) if cfg.get("results_key") else data
        if isinstance(items, dict):
            if "post" in items and isinstance(items["post"], list):
                items = items["post"]
            else:
                items = [v for v in items.values() if isinstance(v, dict)]
        if not isinstance(items, list):
            raise ValueError("JSON source did not return a list of posts/items.")
        return [item for item in items if isinstance(item, dict)]

    def _query_extras(self, cfg: dict[str, Any], request: DownloadRequest) -> list[str]:
        extras: list[str] = []
        order = (request.sort_order or "newest_to_oldest").lower()
        if order in {"oldest", "oldest_to_newest"} and cfg.get("sort_oldest"):
            extras.append(str(cfg["sort_oldest"]))
        elif cfg.get("sort_newest"):
            extras.append(str(cfg["sort_newest"]))
        if request.date_from:
            extras.append(f"date:>={_safe_date(request.date_from)}")
        if request.date_to:
            extras.append(f"date:<={_safe_date(request.date_to)}")
        ratings = _rating_codes(getattr(request, "rating_filter", []) or [])
        if len(ratings) == 1:
            extras.append(f"rating:{ratings[0]}")
        # Blacklists are disabled by default. This branch exists so future source
        # adapters can explicitly opt into account/source blacklist behavior.
        if bool(getattr(request, "apply_source_blacklists", False)) and cfg.get("blacklist_query"):
            extras.append(str(cfg["blacklist_query"]))
        if not bool(getattr(request, "allow_animated", True)):
            extras.append("-animated")
        if not bool(getattr(request, "allow_3d", True)):
            extras.append("-3d")
        if not bool(getattr(request, "allow_blender", True)):
            extras.append("-blender")
        if not bool(getattr(request, "allow_render", True)):
            extras.append("-render")
        return [x for x in extras if x]

    def _download_item_compat(self, item: dict[str, Any], cfg: dict[str, Any], output_dir: Path, preset: dict[str, Any], progress=None) -> str | None:
        try:
            return self._download_item(item, cfg, output_dir, preset, progress=progress)
        except TypeError as exc:
            # Preserve compatibility with tests/plugins that monkeypatch the
            # older _download_item signature without the cooperative progress arg.
            if "progress" not in str(exc):
                raise
            _raise_if_cancelled(progress)
            result = self._download_item(item, cfg, output_dir, preset)
            _raise_if_cancelled(progress)
            return result

    def _download_item(self, item: dict[str, Any], cfg: dict[str, Any], output_dir: Path, preset: dict[str, Any], progress=None) -> str | None:
        _raise_if_cancelled(progress)
        file_url = _nested_get(item, cfg.get("file_url_key"))
        if not file_url and cfg.get("large_file_url_key"):
            file_url = _nested_get(item, cfg.get("large_file_url_key"))
        if not file_url:
            return None
        name = _download_filename_for_item(item, cfg, str(file_url))
        subdir = (preset.get("options") or {}).get("output_subdir")
        target_dir = output_dir / str(subdir) if subdir else output_dir
        target = target_dir / name
        if bool(cfg.get("force_download")) and target.exists():
            target.unlink()
        if not target.exists():
            _raise_if_cancelled(progress)
            with self._request_with_retries(
                "GET",
                str(file_url),
                headers={"User-Agent": self.user_agent},
                stream=True,
                timeout=int(cfg.get("timeout_seconds", 90) or 90),
                max_retries=int(cfg.get("max_retries", 3) or 0),
                backoff_seconds=float(cfg.get("retry_backoff_seconds", 2.0) or 0.0),
                progress=progress,
            ) as r:
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_suffix(target.suffix + ".part")
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        _raise_if_cancelled(progress)
                        if chunk:
                            f.write(chunk)
                tmp.replace(target)
            delay = float(cfg.get("file_delay_seconds", 0.0) or 0.0)
            if delay > 0:
                _cancelable_sleep(delay, progress)
        self._write_metadata_sidecars(target, item, cfg, preset)
        return str(target)

    def _request_with_retries(self, method: str, url: str, *, timeout: int = 60, max_retries: int = 3, backoff_seconds: float = 2.0, progress=None, **kwargs):
        attempts = max(1, int(max_retries or 0) + 1)
        last_error: Exception | None = None
        for attempt in range(attempts):
            _raise_if_cancelled(progress)
            try:
                response = requests.request(method, url, timeout=timeout, **kwargs)
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                if attempt >= attempts - 1:
                    raise
                sleep_for = float(backoff_seconds or 0.0) * (2 ** attempt)
                if sleep_for > 0:
                    _cancelable_sleep(sleep_for, progress)
        raise RuntimeError(f"Request failed after {attempts} attempt(s): {last_error}")

    def _write_metadata_sidecars(self, target: Path, item: dict[str, Any], cfg: dict[str, Any], preset: dict[str, Any]) -> None:
        tags = _extract_tags(item, cfg.get("tags_key"))
        if bool(cfg.get("write_tag_txt_sidecar", True)) and tags:
            write_text(target.with_suffix(".txt"), tag_string(tags))
        if not bool(cfg.get("write_metadata_json_sidecar", True)):
            return
        meta = {
            "source": preset.get("source"),
            "preset": preset.get("name"),
            "positive_tags": preset.get("positive_tags") or [],
            "negative_tags": preset.get("negative_tags") or [],
            "filename_mode": cfg.get("filename_mode") or "hash_original",
            "logic_query": (preset.get("options") or {}).get("logic_query") or "",
            "logic_mode": (preset.get("options") or {}).get("logic_mode") or "",
            "logic_clause": (preset.get("options") or {}).get("_logic_clause") or None,
            "item": item,
        }
        write_text(target.with_suffix(".download.json"), json.dumps(meta, indent=2, ensure_ascii=False))


    def _write_membership_index(self, output_dir: Path, membership: dict[str, dict[str, Any]]) -> None:
        index_dir = output_dir / "_download_index"
        index_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": now_iso(),
            "note": "Membership index records which expanded categories/tags matched each unique downloaded URL. Media files are not duplicated into category folders by default.",
            "items": sorted(membership.values(), key=lambda row: (row.get("path") or "", row.get("url") or "")),
        }
        write_text(index_dir / "download_membership.json", json.dumps(payload, indent=2, ensure_ascii=False))
        # Also write per-category JSON files for quick inspection.
        by_category: dict[str, list[dict[str, Any]]] = {}
        for row in payload["items"]:
            for hit in row.get("matches", []):
                category = str(hit.get("category") or "uncategorized")
                by_category.setdefault(category, []).append({
                    "url": row.get("url"),
                    "path": row.get("path"),
                    "tag": hit.get("tag"),
                    "preset": hit.get("preset"),
                    "source": hit.get("source"),
                })
        for category, rows in by_category.items():
            write_text(index_dir / f"category_{_safe_dir(category)}.json", json.dumps(rows, indent=2, ensure_ascii=False))


def _record_membership(membership: dict[str, dict[str, Any]], url: str, source: str, preset: dict[str, Any], path: str | None) -> None:
    if not url:
        return
    options = dict(preset.get("options") or {})
    row = membership.setdefault(url, {"url": url, "path": path, "matches": []})
    if path and not row.get("path"):
        row["path"] = path
    hit = {
        "source": source,
        "preset": preset.get("name"),
        "category": options.get("_expanded_category") or options.get("category"),
        "tag": options.get("_expanded_category_tag") or options.get("category_tag"),
        "positive_tags": preset.get("positive_tags") or [],
        "negative_tags": preset.get("negative_tags") or [],
        "logic_query": options.get("logic_query") or "",
        "logic_mode": options.get("logic_mode") or "",
        "logic_clause": options.get("_logic_clause") or None,
    }
    key = json.dumps(hit, sort_keys=True, ensure_ascii=False)
    existing = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in row.get("matches", [])}
    if key not in existing:
        row.setdefault("matches", []).append(hit)



def _dedupe_keys_for_item(item: dict[str, Any], cfg: dict[str, Any], source: str, url: str) -> list[str]:
    keys: list[str] = []
    if url:
        keys.append(f"url:{url}")
    candidate_fields = [
        "id", "post_id", "md5", "hash", "file.md5", "file.hash", "file.id",
        "media_asset.id", "media_asset.md5", "large_file_url", "file_url",
    ]
    for field in candidate_fields:
        try:
            value = _nested_get(item, field)
        except Exception:
            value = None
        if value not in (None, "", [], {}):
            keys.append(f"{source}:{field}:{value}")
    file_key = cfg.get("file_url_key")
    if file_key:
        try:
            value = _nested_get(item, file_key)
        except Exception:
            value = None
        if value not in (None, "", [], {}):
            keys.append(f"{source}:{file_key}:{value}")
    seen: set[str] = set()
    ordered: list[str] = []
    for key in keys:
        key = str(key)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered or ([f"url:{url}"] if url else [])

def _nested_get(obj: Any, dotted: str | None) -> Any:
    if not dotted:
        return None
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _extract_tags(item: dict[str, Any], key: str | None) -> list[str]:
    raw = _nested_get(item, key) if key else None
    tags: list[str] = []
    if isinstance(raw, str):
        tags = re.split(r"[\s,]+", raw)
    elif isinstance(raw, dict):
        for value in raw.values():
            if isinstance(value, list):
                tags.extend(str(x) for x in value)
            elif isinstance(value, str):
                tags.extend(re.split(r"[\s,]+", value))
    elif isinstance(raw, list):
        tags = [str(x) for x in raw]
    return [normalize_tag(tag) for tag in tags if normalize_tag(tag)]


def _download_filename_for_item(item: dict[str, Any], cfg: dict[str, Any], file_url: str) -> str:
    """Return a stable, safe media filename for a downloader item.

    hash_original preserves the historical behavior: sha1(url)_original_name.ext.
    post_id and post_id_original are opt-in because some generic JSON sources do
    not expose a durable post id and because changing filenames can affect user
    scripts that depend on previous hash-prefixed names.
    """
    original_name = _safe_filename(urlparse(str(file_url)).path) or "download.bin"
    mode = str(cfg.get("filename_mode") or "hash_original").strip().lower()
    if mode not in {"hash_original", "post_id", "post_id_original", "original"}:
        mode = "hash_original"
    if mode == "original":
        return original_name

    post_id = _item_post_id(item)
    if post_id and mode in {"post_id", "post_id_original"}:
        ext = _item_file_extension(item, original_name)
        base = _safe_filename(str(post_id)) or "post"
        if mode == "post_id":
            return f"{base}{ext}"
        suffix = original_name
        if suffix.lower().startswith((base + "_").lower()):
            return suffix
        return _safe_filename(f"{base}_{suffix}") or f"{base}{ext}"

    url_hash = hashlib.sha1(str(file_url).encode("utf-8", errors="ignore")).hexdigest()[:12]
    if not original_name.startswith(url_hash + "_"):
        return f"{url_hash}_{original_name}"
    return original_name


def _item_post_id(item: dict[str, Any]) -> str | None:
    for field in ("id", "post_id", "post.id", "media_asset.id", "file.id"):
        value = _nested_get(item, field)
        if value not in (None, "", [], {}):
            return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._-") or None
    return None


def _item_file_extension(item: dict[str, Any], original_name: str) -> str:
    ext = ""
    for field in ("file.ext", "ext", "extension", "file_extension"):
        value = _nested_get(item, field)
        if value not in (None, "", [], {}):
            text = str(value).strip().lstrip(".")
            if text:
                ext = "." + re.sub(r"[^A-Za-z0-9]+", "", text)[:12].lower()
                break
    if not ext:
        ext = Path(original_name).suffix
    return ext or ".bin"


def _safe_filename(path: str) -> str:
    name = Path(path).name
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip(" .")
    return name[:220]


def _safe_dir(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", str(text)).strip(" ._")[:96] or "group"


def _safe_date(text: str) -> str:
    value = str(text or "").strip()
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception as exc:
        raise ValueError(f"Invalid date; expected YYYY-MM-DD, got {text!r}") from exc

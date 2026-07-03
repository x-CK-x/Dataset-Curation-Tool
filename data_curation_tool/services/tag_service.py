from __future__ import annotations

import csv
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from pathlib import Path
from typing import Any, Iterable

from ..database import Database, now_iso
from ..jobs import CancelledJobError
from ..paths import AppPaths
from ..schemas import BulkTagRequest, TagPruneRequest, TagPruneResult
from ..utils import load_json, normalize_tag, parse_tag_string, save_json, tag_string, write_text

DEFAULT_IMPLICATIONS = {"1girl": ["girl"], "1boy": ["boy"], "solo": ["single_person"], "portrait": ["face", "upper_body"]}
# Guardrail for real booru startup syncs: if a generic export URL only imports
# a small partial tag table, keep trying dated/full candidates instead of
# treating the partial table as the successful dictionary. Tests/local custom
# imports bypass this guardrail.
MIN_EXPECTED_TAG_ROWS = {"e621": 1_000_000, "e926": 1_000_000}
# Canonical tags exports can be smaller than the full searchable dictionary
# because alias/implication exports contain additional user-typed terms.  This
# threshold only rejects error pages, placeholder files, or wrong-role files
# before the real dictionary gets promoted.
MIN_CANONICAL_TAG_ROWS = {"e621": 1_000_000, "e926": 1_000_000}
CATEGORY_KEYWORDS = {
    "artist": ["artist:", "by_"],
    "character": ["character:", "char:", "oc", "protagonist"],
    "copyright": ["copyright:", "series:", "franchise:"],
    "rating": ["safe", "questionable", "explicit", "rating_safe", "rating_questionable", "rating_explicit"],
    "meta": ["highres", "lowres", "absurdres", "transparent_background", "watermark"],
    "species": ["human", "animal", "creature", "robot", "anthro"],
    "style": ["style", "artstyle", "art_style", "painting", "sketch", "lineart"],
    "concept": ["concept", "pose", "composition", "lighting"],
}
CATEGORY_ALIASES = {
    "0": "general", "1": "artist", "2": "rating", "3": "copyright", "4": "character", "5": "species", "6": "invalid", "7": "meta", "8": "lore",
    "general": "general", "tag": "general", "artist": "artist", "copy": "copyright", "copyright": "copyright", "series": "copyright",
    "character": "character", "species": "species", "meta": "meta", "invalid": "invalid", "deprecated": "invalid", "rating": "rating",
    "custom": "custom", "unknown": "unknown", "style": "style", "artstyle": "style", "art_style": "style", "concept": "concept", "trigger": "trigger",
    "quality": "quality", "negative": "negative", "lore": "lore",
}
BASE_CATEGORIES = [
    {"key": "rating", "label": "Rating", "css_class": "cat-rating"},
    {"key": "artist", "label": "Artist", "css_class": "cat-artist"},
    {"key": "copyright", "label": "Copyright / Series", "css_class": "cat-copyright"},
    {"key": "character", "label": "Character", "css_class": "cat-character"},
    {"key": "species", "label": "Species", "css_class": "cat-species"},
    {"key": "style", "label": "Style / Artstyle", "css_class": "cat-style"},
    {"key": "concept", "label": "Concept / Subject", "css_class": "cat-concept"},
    {"key": "trigger", "label": "Trigger Tokens", "css_class": "cat-trigger"},
    {"key": "quality", "label": "Quality / Score", "css_class": "cat-quality"},
    {"key": "general", "label": "General", "css_class": "cat-general"},
    {"key": "meta", "label": "Meta", "css_class": "cat-meta"},
    {"key": "negative", "label": "Negative / Exclusion", "css_class": "cat-negative"},
    {"key": "lore", "label": "Lore", "css_class": "cat-lore"},
    {"key": "invalid", "label": "Invalid / Deprecated", "css_class": "cat-invalid"},
    {"key": "custom", "label": "Custom / User-defined", "css_class": "cat-custom"},
    {"key": "unknown", "label": "Unknown / Needs Category", "css_class": "cat-unknown"},
]

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


LORA_CATEGORIES = [
    {"key": "style", "label": "Style / Artstyle", "css_class": "cat-style"},
    {"key": "character", "label": "Character", "css_class": "cat-character"},
    {"key": "concept", "label": "Concept / Subject", "css_class": "cat-concept"},
    {"key": "trigger", "label": "Trigger Tokens", "css_class": "cat-trigger"},
    {"key": "quality", "label": "Quality / Score", "css_class": "cat-quality"},
    {"key": "negative", "label": "Negative / Exclusion", "css_class": "cat-negative"},
    {"key": "general", "label": "General", "css_class": "cat-general"},
    {"key": "meta", "label": "Meta", "css_class": "cat-meta"},
    {"key": "custom", "label": "Custom / User-defined", "css_class": "cat-custom"},
    {"key": "unknown", "label": "Unknown / Needs Category", "css_class": "cat-unknown"},
]
DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
    "e621": {"label": "e621 / e926", "categories": BASE_CATEGORIES, "precedence": ["character", "species", "invalid", "artist", "copyright", "general", "meta", "rating", "lore", "style", "concept", "trigger", "quality", "custom", "unknown", "negative"], "db_export_url": "https://e621.net/db_exports/"},
    "e926": {"label": "e926", "categories": BASE_CATEGORIES, "precedence": ["character", "species", "invalid", "artist", "copyright", "general", "meta", "rating", "lore", "style", "concept", "trigger", "quality", "custom", "unknown", "negative"], "db_export_url": "https://e926.net/db_exports/"},
    "danbooru": {"label": "Danbooru", "categories": BASE_CATEGORIES, "precedence": ["rating", "artist", "copyright", "character", "style", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown", "invalid"], "db_export_url": "https://danbooru.donmai.us/wiki_pages/help:database_export"},
    "gelbooru": {"label": "Gelbooru", "categories": BASE_CATEGORIES, "precedence": ["rating", "artist", "copyright", "character", "style", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown", "invalid"], "db_export_url": ""},
    "safebooru": {"label": "Safebooru", "categories": BASE_CATEGORIES, "precedence": ["rating", "artist", "copyright", "character", "style", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown", "invalid"], "db_export_url": ""},
    "rule34": {"label": "Rule34", "categories": BASE_CATEGORIES, "precedence": ["rating", "artist", "copyright", "character", "style", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown", "invalid"], "db_export_url": ""},
    "konachan": {"label": "Konachan", "categories": BASE_CATEGORIES, "precedence": ["rating", "artist", "copyright", "character", "style", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown", "invalid"], "db_export_url": ""},
    "yandere": {"label": "Yande.re", "categories": BASE_CATEGORIES, "precedence": ["rating", "artist", "copyright", "character", "style", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown", "invalid"], "db_export_url": ""},
    "lora-purpose": {"label": "LoRA / Model Purpose", "categories": LORA_CATEGORIES, "precedence": ["style", "character", "concept", "trigger", "quality", "general", "meta", "negative", "custom", "unknown"], "db_export_url": ""},
    "custom": {"label": "Custom Dataset", "categories": BASE_CATEGORIES, "precedence": ["rating", "style", "artist", "copyright", "character", "concept", "species", "trigger", "quality", "general", "meta", "custom", "unknown", "invalid", "negative"], "db_export_url": ""},
}

class TagService:
    def __init__(self, db: Database, paths: AppPaths | None = None, separator: str = ", "):
        self.db = db
        self.paths = paths
        self.separator = separator
        self._cache_lock = threading.RLock()
        self._suggest_cache: dict[str, dict[str, Any]] = {}
        self._custom_tags_path = (paths.runtime if paths else db.path.parent) / "custom_tags.json"
        self.ensure_tag_tables()
        self.ensure_default_profiles()
        self._load_custom_tags_file_into_db()

    def ensure_tag_tables(self) -> None:
        self.db.execute("""CREATE TABLE IF NOT EXISTS tag_profiles (key TEXT PRIMARY KEY, label TEXT NOT NULL, categories_json TEXT NOT NULL DEFAULT '[]', precedence_json TEXT NOT NULL DEFAULT '[]', db_export_url TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS tag_dictionary_entries (source TEXT NOT NULL, tag TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'general', post_count INTEGER NOT NULL DEFAULT 0, aliases_json TEXT NOT NULL DEFAULT '[]', implications_json TEXT NOT NULL DEFAULT '[]', is_custom INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL, PRIMARY KEY(source, tag))""")
        # The PRIMARY KEY(source, tag) already provides source/tag lookup.
        # Extra broad indexes on hundreds of thousands of rows made SQLite imports
        # memory-heavy on constrained machines, so old redundant indexes are removed.
        self.db.execute("DROP INDEX IF EXISTS idx_tag_entries_source_tag")
        self.db.execute("DROP INDEX IF EXISTS idx_tag_entries_source_count")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_entries_source_category ON tag_dictionary_entries(source, category)")

        # Search table used by the live HUD autocomplete.  It intentionally mirrors
        # tag_dictionary_entries with a pre-normalized lowercase column so prefix
        # lookups can use a B-tree instead of rebuilding slow Python structures while
        # the user is typing.
        self.db.execute("""CREATE TABLE IF NOT EXISTS tag_dictionary_search (
            source TEXT NOT NULL,
            tag TEXT NOT NULL,
            tag_lower TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            post_count INTEGER NOT NULL DEFAULT 0,
            is_custom INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(source, tag)
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_search_source_lower ON tag_dictionary_search(source, tag_lower)")
        self.db.execute("DROP INDEX IF EXISTS idx_tag_search_source_count")
        self.db.execute("""CREATE TABLE IF NOT EXISTS tag_export_files (
            profile_key TEXT NOT NULL,
            role TEXT NOT NULL,
            url TEXT NOT NULL,
            local_path TEXT NOT NULL DEFAULT '',
            sha256 TEXT NOT NULL DEFAULT '',
            downloaded_at TEXT NOT NULL DEFAULT '',
            imported_at TEXT NOT NULL DEFAULT '',
            row_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'unknown',
            error TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(profile_key, role, url)
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_export_files_profile_role ON tag_export_files(profile_key, role)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS tag_aliases (
            source TEXT NOT NULL,
            alias TEXT NOT NULL,
            target TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            updated_at TEXT NOT NULL,
            PRIMARY KEY(source, alias, target)
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_aliases_source_alias ON tag_aliases(source, alias)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_aliases_source_target ON tag_aliases(source, target)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS artist_aliases (
            source TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            alias TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(source, artist_name, alias)
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_artist_aliases_source_alias ON artist_aliases(source, alias)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_artist_aliases_source_artist ON artist_aliases(source, artist_name)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS tag_implications (
            source TEXT NOT NULL,
            antecedent TEXT NOT NULL,
            consequent TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            updated_at TEXT NOT NULL,
            PRIMARY KEY(source, antecedent, consequent)
        )""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_implications_source_antecedent ON tag_implications(source, antecedent)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_tag_implications_source_consequent ON tag_implications(source, consequent)")
        self._ensure_search_table_populated()
        self._migrate_alias_placeholders_out_of_dictionary()

    def _migrate_alias_placeholders_out_of_dictionary(self) -> None:
        """Remove legacy alias-placeholder rows from dictionary/search tables.

        Older builds inserted every alias as an ``invalid`` dictionary entry with
        ``aliases_json`` populated.  If the real tags export failed, the UI could
        misleadingly show roughly the alias count (about 69k) as the loaded tag
        dictionary.  Alias data belongs in ``tag_aliases``; it should not be
        counted as real tag-category dictionary data.
        """
        self.db.execute(
            """DELETE FROM tag_dictionary_search
               WHERE source IN (SELECT source FROM tag_dictionary_entries
                                WHERE is_custom=0 AND post_count=0 AND category='invalid'
                                  AND aliases_json IS NOT NULL AND aliases_json NOT IN ('', '[]'))
                 AND tag IN (SELECT tag FROM tag_dictionary_entries
                             WHERE is_custom=0 AND post_count=0 AND category='invalid'
                               AND aliases_json IS NOT NULL AND aliases_json NOT IN ('', '[]'))"""
        )
        self.db.execute(
            """DELETE FROM tag_dictionary_entries
               WHERE is_custom=0 AND post_count=0 AND category='invalid'
                 AND aliases_json IS NOT NULL AND aliases_json NOT IN ('', '[]')"""
        )

    def _ensure_search_table_populated(self) -> None:
        # Migration path for databases that already have dictionaries but not the
        # fast autocomplete mirror.  This is cheap when the search table is already
        # populated.
        count = self.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_search") or {"n": 0}
        if int(count.get("n") or 0) > 0:
            return
        rows = self.db.query("SELECT source, tag, category, post_count, is_custom, updated_at FROM tag_dictionary_entries")
        if rows:
            self.db.executemany(
                """INSERT OR REPLACE INTO tag_dictionary_search(source, tag, tag_lower, category, post_count, is_custom, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (r["source"], r["tag"], str(r["tag"]).lower(), r.get("category") or "general", int(r.get("post_count") or 0), int(r.get("is_custom") or 0), r.get("updated_at") or now_iso())
                    for r in rows
                    if normalize_tag(r.get("tag"))
                ],
            )
            return
        legacy = self.db.query("SELECT tag, category, post_count, updated_at FROM tag_dictionary")
        if legacy:
            self.db.executemany(
                """INSERT OR REPLACE INTO tag_dictionary_search(source, tag, tag_lower, category, post_count, is_custom, updated_at)
                   VALUES ('legacy', ?, ?, ?, ?, 0, ?)""",
                [(r["tag"], str(r["tag"]).lower(), r.get("category") or "general", int(r.get("post_count") or 0), r.get("updated_at") or now_iso()) for r in legacy if normalize_tag(r.get("tag"))],
            )

    def ensure_default_profiles(self) -> None:
        for key, profile in DEFAULT_PROFILES.items():
            existing = self.db.query_one("SELECT * FROM tag_profiles WHERE key=?", (key,))
            if existing:
                current_categories = _json_loads(existing.get("categories_json"), [])
                by_key = {item.get("key"): dict(item) for item in current_categories if item.get("key")}
                changed = False
                for item in profile["categories"]:
                    if item.get("key") not in by_key:
                        by_key[item["key"]] = item
                        changed = True
                current_precedence = _json_loads(existing.get("precedence_json"), [])
                if key in {"e621", "e926"}:
                    # Keep the selected booru profile aligned with the explicit
                    # user/category ordering config instead of only appending
                    # missing categories to an old order.
                    merged_precedence = list(profile["precedence"])
                    if current_precedence != merged_precedence:
                        changed = True
                else:
                    merged_precedence = list(current_precedence)
                    for category in profile["precedence"]:
                        if category not in merged_precedence:
                            merged_precedence.append(category)
                            changed = True
                default_url = profile.get("db_export_url") or ""
                existing_url = (existing.get("db_export_url") or "").rstrip("/")
                next_url = existing.get("db_export_url") or ""
                if key in {"e621", "e926"} and default_url and existing_url in {"", f"https://{key}.net/db_export"}:
                    next_url = default_url
                    changed = True
                if changed:
                    self.db.execute("UPDATE tag_profiles SET categories_json=?, precedence_json=?, db_export_url=?, updated_at=? WHERE key=?", (json.dumps(list(by_key.values())), json.dumps(merged_precedence), next_url, now_iso(), key))
                continue
            self.db.execute("""INSERT INTO tag_profiles(key, label, categories_json, precedence_json, db_export_url, updated_at) VALUES (?, ?, ?, ?, ?, ?)""", (key, profile["label"], json.dumps(profile["categories"]), json.dumps(profile["precedence"]), profile.get("db_export_url") or "", now_iso()))

    def list_profiles(self) -> list[dict[str, Any]]:
        rows = self.db.query("SELECT * FROM tag_profiles ORDER BY CASE key WHEN 'e621' THEN 0 WHEN 'danbooru' THEN 1 WHEN 'custom' THEN 98 ELSE 50 END, label")
        return [{"key": r["key"], "label": r["label"], "categories": _json_loads(r.get("categories_json"), []), "precedence": _json_loads(r.get("precedence_json"), []), "db_export_url": r.get("db_export_url") or ""} for r in rows]

    def get_profile(self, profile_key: str | None) -> dict[str, Any]:
        key = profile_key or "e621"
        row = self.db.query_one("SELECT * FROM tag_profiles WHERE key=?", (key,)) or self.db.query_one("SELECT * FROM tag_profiles WHERE key='custom'")
        if not row:
            return {"key": "custom", **DEFAULT_PROFILES["custom"]}
        return {"key": row["key"], "label": row["label"], "categories": _json_loads(row.get("categories_json"), []), "precedence": _json_loads(row.get("precedence_json"), []), "db_export_url": row.get("db_export_url") or ""}

    def upsert_profile(self, key: str, label: str | None = None, categories: list[dict[str, Any]] | None = None, precedence: list[str] | None = None, db_export_url: str | None = None) -> dict[str, Any]:
        clean_key = normalize_tag(key).lower().replace(":", "")
        if not clean_key:
            raise ValueError("Profile key cannot be empty.")
        base = self.get_profile(clean_key) if self.db.query_one("SELECT key FROM tag_profiles WHERE key=?", (clean_key,)) else DEFAULT_PROFILES.get("custom", {})
        next_categories = categories or base.get("categories") or BASE_CATEGORIES
        next_precedence = precedence or base.get("precedence") or [c.get("key") for c in next_categories if c.get("key")]
        next_label = label or base.get("label") or clean_key
        next_url = db_export_url if db_export_url is not None else base.get("db_export_url", "")
        self.db.execute(
            """INSERT INTO tag_profiles(key, label, categories_json, precedence_json, db_export_url, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET label=excluded.label, categories_json=excluded.categories_json, precedence_json=excluded.precedence_json, db_export_url=excluded.db_export_url, updated_at=excluded.updated_at""",
            (clean_key, next_label, json.dumps(next_categories), json.dumps(next_precedence), next_url, now_iso()),
        )
        self.invalidate_cache(clean_key)
        return self.get_profile(clean_key)

    def update_precedence(self, profile_key: str, precedence: list[str]) -> dict[str, Any]:
        profile = self.get_profile(profile_key)
        category_keys = [c.get("key") for c in profile.get("categories") or [] if c.get("key")]
        cleaned = []
        for item in precedence:
            key = normalize_tag(item).lower().replace(":", "")
            if key and key in category_keys and key not in cleaned:
                cleaned.append(key)
        for key in category_keys:
            if key not in cleaned:
                cleaned.append(key)
        self.db.execute("UPDATE tag_profiles SET precedence_json=?, updated_at=? WHERE key=?", (json.dumps(cleaned), now_iso(), profile.get("key")))
        self.invalidate_cache(profile.get("key"))
        return self.get_profile(profile.get("key"))

    def reconcile_export_cache(self, profile_key: str | None = None) -> dict[str, Any]:
        """Register already-present tag export files without downloading them."""
        if not self.paths:
            return {"profiles": {}, "files": 0}
        profiles = [profile_key] if profile_key else [p["key"] for p in self.list_profiles()]
        summary: dict[str, Any] = {"profiles": {}, "files": 0}
        root = self.paths.runtime / "tag_exports"
        if not root.exists():
            return summary
        for raw_key in profiles:
            key = raw_key or "e621"
            profile_dir = root / normalize_tag(key)
            if not profile_dir.exists():
                continue
            rows = []
            for path in sorted(profile_dir.rglob("*")):
                if not path.is_file() or path.name.endswith((".part", ".tmp", ".lock")):
                    continue
                if not self._looks_like_export_file(path.name):
                    continue
                existing = self.db.query_one(
                    "SELECT row_count, status FROM tag_export_files WHERE profile_key=? AND local_path=? ORDER BY imported_at DESC, downloaded_at DESC LIMIT 1",
                    (key, str(path)),
                )
                if existing and int(existing.get("row_count") or 0) > 0:
                    continue
                role = self._infer_export_role(path.name)
                try:
                    count = self.count_dictionary_csv_rows(path, key) if role == "tags" else self._line_count_export(path)
                    status = "found"
                    error = ""
                except Exception as exc:
                    count = 0
                    status = "found_unreadable"
                    error = str(exc)
                url = f"local-cache:{path.name}"
                self._record_export_file(key, role, url, path, "", int(count or 0), status=status, error=error)
                rows.append({"role": role, "path": str(path), "rows": int(count or 0), "status": status, "error": error})
                summary["files"] += 1
            summary["profiles"][key] = rows
        return summary

    def dictionary_status(self, profile_key: str | None = None) -> dict[str, Any]:
        self.reconcile_export_cache(profile_key)
        profiles = [profile_key] if profile_key else [p["key"] for p in self.list_profiles()]
        result: dict[str, Any] = {}
        for key in profiles:
            key = key or "e621"
            total_row = self.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source=?", (key,)) or {"n": 0}
            total = int(total_row.get("n") or 0)
            rows = self.db.query(
                "SELECT category, COUNT(*) AS n FROM tag_dictionary_entries WHERE source=? GROUP BY category ORDER BY n DESC",
                (key,),
            ) if total else []
            profile = self.get_profile(key)
            export_rows = self.db.query(
                "SELECT role, url, local_path, downloaded_at, imported_at, row_count, status, error FROM tag_export_files WHERE profile_key=? ORDER BY role, imported_at DESC, url",
                (key,),
            )
            latest_by_role: dict[str, dict[str, Any]] = {}
            latest_imported = None
            cached_tag_rows = 0
            downloaded_export_rows = 0
            for row in export_rows:
                role = row.get("role") or "tags"
                latest_by_role.setdefault(role, dict(row))
                count = int(row.get("row_count") or 0)
                if role == "tags":
                    cached_tag_rows = max(cached_tag_rows, count)
                downloaded_export_rows += max(0, count)
                value = row.get("imported_at") or row.get("downloaded_at")
                if value and (latest_imported is None or str(value) > str(latest_imported)):
                    latest_imported = value
            effective_found_total = max(total, cached_tag_rows)
            stale_after_hours = 336
            min_expected = MIN_EXPECTED_TAG_ROWS.get((key or "").lower(), 0)
            incomplete = bool(min_expected and effective_found_total < min_expected)
            stale = effective_found_total <= 0 or incomplete
            if latest_imported and not stale:
                try:
                    dt = datetime.fromisoformat(str(latest_imported).replace("Z", "+00:00"))
                    stale = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0 >= stale_after_hours
                except Exception:
                    stale = True
            missing_roles = [role for role in ("tags", "aliases", "implications", "artists") if role not in latest_by_role]
            # On million-row official dictionaries this count intentionally uses
            # a direct query rather than scanning category rows again.
            custom_total = int((self.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source=? AND is_custom=1", (key,)) or {"n": 0}).get("n") or 0)
            result[key] = {
                "profile_key": key,
                "label": profile.get("label"),
                "total": total,
                "cached_tag_rows": cached_tag_rows,
                "downloaded_export_rows": downloaded_export_rows,
                "effective_found_total": effective_found_total,
                "by_category": rows,
                "db_export_url": profile.get("db_export_url") or "",
                "custom_total": custom_total,
                "exports": export_rows,
                "latest_exports": latest_by_role,
                "latest_imported_at": latest_imported,
                "stale": bool(stale),
                "incomplete": incomplete,
                "minimum_expected_tags": min_expected,
                "missing_roles": missing_roles,
                "stale_after_hours": stale_after_hours,
            }
        return result[profiles[0]] if profile_key else result

    def default_export_urls(self, profile_key: str) -> list[str]:
        key = (profile_key or "e621").lower()
        profile = self.get_profile(key)
        base = (profile.get("db_export_url") or "").rstrip("/")
        if key in {"e621", "e926"}:
            host = "https://e926.net" if key == "e926" else "https://e621.net"
            # Original-tool behavior: hit the export page first, parse the newest
            # tags*.gz filename from the listing, then download that advertised
            # file. Direct undated names are fallbacks for mirrors only.
            return [
                f"{host}/db_exports/",
                f"{host}/db_export/",
                f"{host}/db_exports/tags.csv.gz",
                f"{host}/db_exports/tag_aliases.csv.gz",
                f"{host}/db_exports/tag_implications.csv.gz",
                f"{host}/db_exports/artists.csv.gz",
                f"{host}/db_export/tags.csv.gz",
                f"{host}/db_export/tag_aliases.csv.gz",
                f"{host}/db_export/tag_implications.csv.gz",
                f"{host}/db_export/artists.csv.gz",
            ]
        if key == "danbooru":
            return ["https://danbooru.donmai.us/db_exports/", "https://danbooru.donmai.us/db_export/", "https://danbooru.donmai.us/wiki_pages/help:database_export"]
        if base:
            return self._dedupe_urls([base, *self._export_page_candidates(base)])
        return []

    def categories(self, profile_key: str | None = None) -> list[dict[str, Any]]:
        categories = self.get_profile(profile_key).get("categories") or BASE_CATEGORIES
        if "unknown" not in {c.get("key") for c in categories}:
            categories = [*categories, {"key": "unknown", "label": "Unknown / Needs Category", "css_class": "cat-unknown"}]
        return categories

    def normalize_category(self, category: str | int | None, profile_key: str | None = None) -> str:
        if category is None:
            return "unknown"
        raw = str(category).strip().lower().replace(" ", "_")
        mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
        allowed = {item["key"] for item in self.categories(profile_key)}
        if mapped in allowed:
            return mapped
        if mapped in {"deprecated"}:
            return "invalid"
        return "custom" if mapped else "unknown"

    def add_category(self, profile_key: str, key: str, label: str | None = None, css_class: str | None = None) -> dict[str, Any]:
        profile_key = profile_key or "custom"
        clean_key = normalize_tag(key).lower().replace(":", "")
        if not clean_key:
            raise ValueError("Category key cannot be empty.")
        profile = self.get_profile(profile_key)
        categories = list(profile.get("categories") or [])
        if not any(item.get("key") == clean_key for item in categories):
            categories.append({"key": clean_key, "label": label or clean_key.replace("_", " ").title(), "css_class": css_class or "cat-custom"})
        precedence = list(profile.get("precedence") or [])
        if clean_key not in precedence:
            insert_at = next((i for i, cat in enumerate(precedence) if cat in {"custom", "unknown", "invalid", "negative"}), len(precedence))
            precedence.insert(insert_at, clean_key)
        self.db.execute("UPDATE tag_profiles SET categories_json=?, precedence_json=?, updated_at=? WHERE key=?", (json.dumps(categories), json.dumps(precedence), now_iso(), profile_key))
        return {"profile_key": profile_key, "key": clean_key, "label": label or clean_key.replace("_", " ").title(), "css_class": css_class or "cat-custom"}

    def categorize(self, tag: str, profile_key: str | None = None) -> str:
        tag = normalize_tag(tag); profile_key = profile_key or "e621"
        if not tag: return "unknown"
        # Global user-defined category config always has priority over the selected booru profile.
        custom = self.db.query_one("SELECT category FROM tag_dictionary_entries WHERE source='custom' AND tag=?", (tag,))
        if custom: return self.normalize_category(custom["category"], profile_key)
        row = self.db.query_one("SELECT category FROM tag_dictionary_entries WHERE source=? AND tag=?", (profile_key, tag))
        if row: return self.normalize_category(row["category"], profile_key)
        legacy = self.db.query_one("SELECT category FROM tag_dictionary WHERE tag=?", (tag,))
        if legacy: return self.normalize_category(legacy["category"], profile_key)
        alias = self.db.query_one("SELECT target FROM tag_aliases WHERE source=? AND alias=?", (profile_key, tag))
        if alias: return self.normalize_category("invalid", profile_key)
        low = tag.lower()
        for cat, needles in CATEGORY_KEYWORDS.items():
            if any(low == n or low.startswith(n) or n in low for n in needles):
                return self.normalize_category(cat, profile_key)
        return "unknown"

    def resolve_category(self, tag: str, profile_key: str | None = None, override: str | int | None = None) -> str:
        """Resolve one tag category with global custom config priority.

        Priority order:
        1. Global user custom tag config (source='custom')
        2. Explicit sidecar/category override, such as JSON sidecar category maps
        3. Selected booru/profile dictionary
        4. Legacy dictionary + lightweight heuristics
        """
        tag = normalize_tag(tag)
        profile_key = profile_key or "e621"
        if not tag:
            return "unknown"
        custom = self.db.query_one("SELECT category FROM tag_dictionary_entries WHERE source='custom' AND tag=?", (tag,))
        if custom:
            return self.normalize_category(custom.get("category"), profile_key)
        if override is not None and str(override).strip() != "":
            return self.normalize_category(override, profile_key)
        return self.categorize(tag, profile_key)

    def set_tags(
        self,
        media_id: int,
        tags: Iterable[str],
        source: str = "manual",
        save_sidecar: bool = True,
        profile_key: str | None = None,
        order_strategy: str = "retain",
        category_overrides: dict[str, str] | None = None,
    ) -> list[str]:
        """Persist tags for one media item.

        ``category_overrides`` is used for imported JSON sidecars and booru
        metadata that already contain authoritative tag categories.  The old
        flow re-categorized every imported tag from the active dictionary, which
        made correctly categorized JSON sidecars render as unknown/general until
        the user imported a dictionary.  Overrides are normalized through the
        selected profile so numeric booru IDs and textual categories both map to
        stable UI CSS classes.
        """
        pairs = self.prepare_tag_pairs(tags, profile_key=profile_key, order_strategy=order_strategy, category_overrides=category_overrides)
        ordered = [tag for tag, _ in pairs]
        self.db.replace_tags(media_id, pairs, source=source)
        if save_sidecar:
            row = self.db.query_one("SELECT path, tag_path FROM media WHERE id=?", (media_id,))
            if row:
                write_text(Path(row["tag_path"] or Path(row["path"]).with_suffix(".txt")), tag_string(ordered, self.separator))
        return ordered

    def set_tags_with_categories(
        self,
        media_id: int,
        tags: Iterable[str],
        categories: dict[str, str],
        source: str = "json_sidecar",
        save_sidecar: bool = False,
        profile_key: str | None = None,
        order_strategy: str = "retain",
    ) -> list[str]:
        return self.set_tags(
            media_id,
            tags,
            source=source,
            save_sidecar=save_sidecar,
            profile_key=profile_key,
            order_strategy=order_strategy,
            category_overrides=categories,
        )

    def set_tag_string(self, media_id: int, raw: str, separator: str | None = None, source: str = "manual", save_sidecar: bool = True, profile_key: str | None = None, order_strategy: str = "retain") -> list[str]:
        return self.set_tags(media_id, parse_tag_string(raw, separator or self.separator), source=source, save_sidecar=save_sidecar, profile_key=profile_key, order_strategy=order_strategy)

    def get_tags(self, media_id: int) -> list[str]:
        return [r["tag"] for r in self.db.query("SELECT tag FROM tags WHERE media_id=? ORDER BY ordinal, tag", (media_id,))]

    def get_categories(self, media_id: int) -> dict[str, str]:
        return {r["tag"]: r["category"] for r in self.db.query("SELECT tag, category FROM tags WHERE media_id=? ORDER BY ordinal, tag", (media_id,))}

    def bulk(self, request: BulkTagRequest) -> dict[str, int | list[int]]:
        changed: list[int] = []
        source_tags = self.get_tags(request.source_media_id) if request.source_media_id else []
        profile_key = getattr(request, "tag_profile", None) or "e621"
        order_strategy = getattr(request, "order_strategy", "retain") or "retain"
        for media_id in request.media_ids:
            current = self.get_tags(media_id); updated = list(current)
            if request.operation == "add":
                for tag in request.tags:
                    tag = normalize_tag(tag)
                    if tag and tag not in updated: updated.append(tag)
            elif request.operation == "remove":
                remove = {normalize_tag(t) for t in request.tags}; updated = [tag for tag in updated if tag not in remove]
            elif request.operation == "replace" and request.replace_from is not None and request.replace_to is not None:
                src = normalize_tag(request.replace_from); dst = normalize_tag(request.replace_to); updated = [dst if tag == src else tag for tag in updated]
            elif request.operation == "set":
                updated = [normalize_tag(tag) for tag in request.tags if normalize_tag(tag)]
            elif request.operation == "copy":
                updated = list(source_tags)
            if updated != current or order_strategy != "retain":
                self.set_tags(media_id, updated, source="bulk", save_sidecar=request.save_sidecars, profile_key=profile_key, order_strategy=order_strategy)
                changed.append(media_id)
        return {"changed": len(changed), "media_ids": changed}

    def prune(self, request: TagPruneRequest) -> list[TagPruneResult]:
        implications = dict(DEFAULT_IMPLICATIONS)
        implications.update({normalize_tag(k): [normalize_tag(v) for v in vals] for k, vals in request.implications.items()})
        media_ids = list(request.media_ids)
        if request.dataset_id and not media_ids:
            media_ids = [r["id"] for r in self.db.query("SELECT id FROM media WHERE dataset_id=? AND active=1", (request.dataset_id,))]
        results: list[TagPruneResult] = []
        for media_id in media_ids:
            tags = self.get_tags(media_id); tag_set = set(tags); remove: set[str] = set()
            for specific, broader in implications.items():
                if specific in tag_set: remove.update(tag for tag in broader if tag in tag_set)
            kept = [tag for tag in tags if tag not in remove]
            if remove and not request.dry_run: self.set_tags(media_id, kept, source="prune", save_sidecar=True)
            results.append(TagPruneResult(media_id=media_id, removed=sorted(remove), kept=kept))
        return results

    def _csv_header(self, path: Path) -> list[str]:
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open
        try:
            with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
                line = f.readline()
        except Exception:
            return []
        return [part.strip().lower() for part in next(csv.reader([line]))] if line else []

    def _arrow_read_csv(self, path: Path, include_columns: list[str] | None = None):
        """Return a PyArrow table or ``None`` when Arrow is unavailable/unsuitable."""
        try:
            import pyarrow as pa
            from pyarrow import csv as pa_csv
        except Exception:
            return None
        try:
            # Arrow's CSV reader is multi-threaded by default.  Make the large
            # booru exports chunky enough to keep CPU overhead low while still
            # not requiring streaming complexity for files that fit comfortably in RAM.
            try:
                pa.set_cpu_count(max(1, min(8, os.cpu_count() or 1)))
            except Exception:
                pass
            read_options = pa_csv.ReadOptions(use_threads=True, block_size=1 << 24)
            convert_options = pa_csv.ConvertOptions(include_columns=include_columns) if include_columns else None
            return pa_csv.read_csv(str(path), read_options=read_options, convert_options=convert_options)
        except Exception:
            return None

    def _arrow_tag_rows(self, path: Path, profile_key: str, updated_at: str) -> list[tuple[Any, ...]] | None:
        header = self._csv_header(path)
        # The official booru tags export is exactly id,name,category,post_count.
        # Use Arrow only when the file exposes real tag columns; fallback keeps
        # custom/headerless CSV behavior.
        if "name" not in header or "category" not in header:
            return None
        include = [c for c in ("name", "category", "post_count") if c in header]
        table = self._arrow_read_csv(path, include)
        if table is None or "name" not in table.column_names:
            return None
        names = table.column("name").to_pylist()
        categories = table.column("category").to_pylist() if "category" in table.column_names else ["general"] * len(names)
        counts = table.column("post_count").to_pylist() if "post_count" in table.column_names else [0] * len(names)
        allowed_categories = {item["key"] for item in self.categories(profile_key)}

        def norm_category(value: Any) -> str:
            raw = str(value if value is not None else "unknown").strip().lower().replace(" ", "_")
            mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
            if mapped in allowed_categories:
                return mapped
            if mapped == "deprecated":
                return "invalid"
            return "custom" if mapped else "unknown"

        rows: list[tuple[Any, ...]] = []
        for raw_tag, raw_category, raw_count in zip(names, categories, counts):
            tag = normalize_tag(raw_tag)
            if not tag or tag.lower() == "nan":
                continue
            try:
                post_count = int(float(raw_count or 0))
            except (TypeError, ValueError):
                post_count = 0
            if post_count < 0:
                post_count = 0
            rows.append((profile_key, tag, norm_category(raw_category), post_count, "[]", "[]", updated_at))
        return rows

    def _arrow_pair_rows(self, path: Path, profile_key: str, left_key: str = "antecedent_name", right_key: str = "consequent_name", updated_at: str | None = None) -> list[tuple[Any, ...]] | None:
        header = self._csv_header(path)
        if left_key not in header or right_key not in header:
            return None
        include = [left_key, right_key]
        if "status" in header:
            include.append("status")
        table = self._arrow_read_csv(path, include)
        if table is None or left_key not in table.column_names or right_key not in table.column_names:
            return None
        left_values = table.column(left_key).to_pylist()
        right_values = table.column(right_key).to_pylist()
        statuses = table.column("status").to_pylist() if "status" in table.column_names else ["active"] * len(left_values)
        rows: list[tuple[Any, ...]] = []
        ts = updated_at or now_iso()
        for left_raw, right_raw, status_raw in zip(left_values, right_values, statuses):
            status = str(status_raw or "active").strip().lower()
            if status in {"deleted", "rejected", "pending", "retired"}:
                continue
            left = normalize_tag(left_raw)
            right = normalize_tag(right_raw)
            if left and right:
                rows.append((profile_key, left, right, status or "active", ts))
        return rows

    def _parse_artist_other_names(self, value: Any) -> list[str]:
        text = str(value or "").strip()
        if not text or text in {"{}", "[]"}:
            return []
        if text.startswith("{") and text.endswith("}"):
            text = text[1:-1]
        aliases: list[str] = []
        for part in text.split(","):
            alias = normalize_tag(part.strip().strip('"\''))
            if alias:
                aliases.append(alias)
        return list(dict.fromkeys(aliases))

    def _arrow_artist_rows(self, path: Path, profile_key: str, updated_at: str) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]], list[tuple[Any, ...]]] | None:
        header = self._csv_header(path)
        if "name" not in header or "other_names" not in header:
            return None
        include = [c for c in ("name", "other_names", "is_active") if c in header]
        table = self._arrow_read_csv(path, include)
        if table is None or "name" not in table.column_names or "other_names" not in table.column_names:
            return None
        names = table.column("name").to_pylist()
        other_names = table.column("other_names").to_pylist()
        active_values = table.column("is_active").to_pylist() if "is_active" in table.column_names else [True] * len(names)
        dict_rows: list[tuple[Any, ...]] = []
        alias_rows: list[tuple[Any, ...]] = []
        artist_alias_rows: list[tuple[Any, ...]] = []
        for raw_name, raw_aliases, raw_active in zip(names, other_names, active_values):
            artist = normalize_tag(raw_name)
            if not artist:
                continue
            active_text = str(raw_active).strip().lower()
            is_active = active_text not in {"0", "false", "f", "no", "n", "deleted", "inactive"}
            if not is_active:
                continue
            dict_rows.append((profile_key, artist, "artist", 0, "[]", "[]", updated_at))
            for alias in self._parse_artist_other_names(raw_aliases):
                if alias and alias != artist:
                    alias_rows.append((profile_key, alias, artist, "artist_alias", updated_at))
                    artist_alias_rows.append((profile_key, artist, alias, 1, updated_at))
        return dict_rows, alias_rows, artist_alias_rows

    def _line_count_export(self, path: Path) -> int:
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open
        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
            try:
                next(f)
            except StopIteration:
                return 0
            return sum(1 for line in f if line.strip())

    def _fast_official_tag_row_count(self, path: Path) -> int | None:
        """Count official id,name,category,post_count tag exports cheaply.

        Official booru tag exports have one tag per line after the header.
        Counting lines is far faster and avoids materializing millions of tag
        names just to decide whether a remote candidate is complete.
        """
        header = self._csv_header(path)
        if not {"id", "name", "category", "post_count"}.issubset(set(header)):
            return None
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open
        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
            try:
                next(f)
            except StopIteration:
                return 0
            return sum(1 for line in f if line.strip())

    def count_dictionary_csv_rows(self, path: Path, profile_key: str = "e621") -> int:
        """Count valid tag rows without mutating the database.

        Official DB-export tag files use ``id,name,category,post_count`` and can
        be counted by lines. PyArrow is no longer used for this preflight count
        because converting a million-plus tag column to Python objects just to
        count it is unnecessary.
        """
        fast_count = self._fast_official_tag_row_count(path)
        if fast_count is not None:
            return fast_count
        now = now_iso()
        arrow_rows = self._arrow_tag_rows(path, profile_key, now)
        if arrow_rows is not None:
            return len(arrow_rows)
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open
        count = 0
        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
            sample = f.read(8192)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
            except csv.Error:
                dialect = csv.excel_tab if "\t" in sample and "," not in sample else csv.excel
            reader = csv.reader(f, dialect=dialect)
            try:
                first = next(reader)
            except StopIteration:
                return 0
            header = [str(x or "").strip().lower() for x in first]
            headerless = not any(name in header for name in ("name", "tag", "tag_name", "label", "category", "post_count", "count", "posts"))
            if headerless:
                rows_iter = [first]
                name_idx = 0
            else:
                rows_iter = []
                name_idx = 0
                for candidate in ("name", "tag", "tag_name", "label"):
                    if candidate in header:
                        name_idx = header.index(candidate)
                        break
            for row in rows_iter:
                if name_idx < len(row) and normalize_tag(row[name_idx]) and normalize_tag(row[name_idx]).lower() != "nan":
                    count += 1
            for row in reader:
                if name_idx < len(row) and normalize_tag(row[name_idx]) and normalize_tag(row[name_idx]).lower() != "nan":
                    count += 1
        return count

    def _import_dictionary_csv_pyarrow(self, path: Path, profile_key: str = "e621", *, replace_existing: bool = False, keep_custom: bool = True, progress=None, rebuild_mirrors: bool = True) -> int:
        """PyArrow-first streaming import for official booru tags CSV/GZ files.

        Expected official header: ``id,name,category,post_count``.  This uses
        ``pyarrow.csv.open_csv`` so large compressed exports are read in record
        batches instead of materializing the entire table in Python before SQLite
        insertion.
        """
        try:
            import pyarrow as pa
            from pyarrow import csv as pa_csv
        except Exception as exc:
            raise RuntimeError("pyarrow is not installed") from exc
        now = now_iso()
        header = self._csv_header(path)
        if "name" not in header or "category" not in header:
            raise RuntimeError("file does not expose the official tags CSV columns")
        include = [c for c in ("name", "category", "post_count") if c in header]
        allowed_categories = {item["key"] for item in self.categories(profile_key)}

        def norm_category(value: Any) -> str:
            raw = str(value if value is not None else "unknown").strip().lower().replace(" ", "_")
            mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
            if mapped in allowed_categories:
                return mapped
            if mapped == "deprecated":
                return "invalid"
            return "custom" if mapped else "unknown"

        try:
            pa.set_cpu_count(max(1, min(8, os.cpu_count() or 1)))
        except Exception:
            pass
        read_options = pa_csv.ReadOptions(use_threads=True, block_size=1 << 22)
        convert_options = pa_csv.ConvertOptions(include_columns=include)
        # PyArrow can infer gzip from the .gz suffix when passed a path.
        # This avoids version-specific input_stream(compression=...) behavior.
        reader = pa_csv.open_csv(str(path), read_options=read_options, convert_options=convert_options)
        insert_sql = """INSERT INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 0, ?)""" if replace_existing else """INSERT INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                        ON CONFLICT(source, tag) DO UPDATE SET category=excluded.category, post_count=excluded.post_count,
                        aliases_json=excluded.aliases_json, implications_json=excluded.implications_json, is_custom=0, updated_at=excluded.updated_at"""
        count = 0
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            if replace_existing:
                if keep_custom:
                    conn.execute("DELETE FROM tag_dictionary_entries WHERE source=? AND is_custom=0", (profile_key,))
                    conn.execute("DELETE FROM tag_dictionary_search WHERE source=? AND is_custom=0", (profile_key,))
                else:
                    conn.execute("DELETE FROM tag_dictionary_entries WHERE source=?", (profile_key,))
                    conn.execute("DELETE FROM tag_dictionary_search WHERE source=?", (profile_key,))
            if rebuild_mirrors:
                conn.execute("DELETE FROM tag_dictionary")
            while True:
                try:
                    batch = reader.read_next_batch()
                except StopIteration:
                    break
                names = batch.column(batch.schema.get_field_index("name")).to_pylist()
                categories = batch.column(batch.schema.get_field_index("category")).to_pylist() if "category" in batch.schema.names else ["general"] * len(names)
                counts = batch.column(batch.schema.get_field_index("post_count")).to_pylist() if "post_count" in batch.schema.names else [0] * len(names)
                rows: list[tuple[Any, ...]] = []
                for raw_tag, raw_category, raw_count in zip(names, categories, counts):
                    tag = normalize_tag(raw_tag)
                    if not tag or tag.lower() == "nan":
                        continue
                    try:
                        post_count = int(float(raw_count or 0))
                    except (TypeError, ValueError):
                        post_count = 0
                    if post_count < 0:
                        post_count = 0
                    rows.append((profile_key, tag, norm_category(raw_category), post_count, "[]", "[]", now))
                if rows:
                    conn.executemany(insert_sql, rows)
                    count += len(rows)
            if rebuild_mirrors:
                self._rebuild_profile_dictionary_mirrors(conn, profile_key)
        self.invalidate_cache(profile_key)
        return count

    def import_dictionary_csv(self, path: Path, profile_key: str = "e621", *, replace_existing: bool = False, keep_custom: bool = True, progress=None, rebuild_mirrors: bool = True) -> int:
        """Fast import for tag dictionary CSV/TSV/DB-export files.

        The previous implementation parsed each row into multiple Python lists and
        committed every small flush through ``Database.executemany``.  It also
        mirrored every tag into multiple tables during parsing.  This version keeps
        one SQLite transaction open, inserts only the canonical profile rows while
        streaming the CSV, then rebuilds the autocomplete and legacy mirror tables
        with set-based SQL.  That is much faster for large ``tags-YYYY-MM-DD.csv.gz``
        exports while preserving the same columns from the original tool:
        ``name``, ``category`` and ``post_count``.

        v5.10 fix: zero-count tags are now retained.  The earlier fast importer
        skipped ``post_count == 0`` rows, which made the dictionary appear to
        contain only active/high-count tags and dropped hundreds of thousands of
        valid category/aliasable tags from booru exports.  Suggestions still sort
        high-count tags first, but category/color/compare/editor features can now
        resolve every tag present in the CSV.
        """
        profile_key = profile_key or "e621"
        if os.environ.get("DCT_DISABLE_PYARROW_TAG_IMPORT") != "1":
            try:
                return self._import_dictionary_csv_pyarrow(path, profile_key, replace_existing=replace_existing, keep_custom=keep_custom, progress=progress, rebuild_mirrors=rebuild_mirrors)
            except Exception as exc:
                if os.environ.get("DCT_REQUIRE_PYARROW_TAG_IMPORT") == "1":
                    raise
                if progress:
                    progress(0, f"PyArrow tag import unavailable/fell back to Python CSV: {exc}. Run update.bat/update.sh to install pyarrow for the fast path.")
        count = 0
        now = now_iso()
        if replace_existing:
            self.clear_profile_dictionary(profile_key, keep_custom=keep_custom)
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open

        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
            sample = f.read(8192)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
            except csv.Error:
                dialect = csv.excel_tab if "\t" in sample and "," not in sample else csv.excel
            reader = csv.reader(f, dialect=dialect)
            try:
                first = next(reader)
            except StopIteration:
                return 0
            header = [str(x or "").strip().lower() for x in first]
            headerless = not any(name in header for name in ("name", "tag", "tag_name", "label", "category", "post_count", "count", "posts"))
            if headerless:
                rows_iter = [first]
                name_idx, category_idx, count_idx = 0, 1, 2
            else:
                rows_iter = []
                def find(names: tuple[str, ...], default: int) -> int:
                    for name in names:
                        if name in header:
                            return header.index(name)
                    return default
                name_idx = find(("name", "tag", "tag_name", "label"), 0)
                category_idx = find(("category", "type", "tag_category", "category_id"), 1)
                count_idx = find(("post_count", "count", "posts", "post_count_total"), 2)

            batch: list[tuple[Any, ...]] = []
            batch_size = 50000
            allowed_categories = {item["key"] for item in self.categories(profile_key)}

            def normalize_category_fast(value: Any) -> str:
                raw = str(value or "unknown").strip().lower().replace(" ", "_")
                mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
                if mapped in allowed_categories:
                    return mapped
                if mapped == "deprecated":
                    return "invalid"
                return "custom" if mapped else "unknown"

            def convert_row(row: list[Any]) -> tuple[Any, ...] | None:
                try:
                    raw_tag = row[name_idx] if name_idx < len(row) else ""
                    tag = normalize_tag(raw_tag)
                    if not tag or tag.lower() == "nan":
                        return None
                    raw_category = row[category_idx] if category_idx < len(row) else "general"
                    category = normalize_category_fast(raw_category)
                    raw_count = row[count_idx] if count_idx < len(row) else 0
                    try:
                        post_count = int(float(raw_count or 0))
                    except (TypeError, ValueError):
                        post_count = 0
                    # Keep zero-count rows.  They are still part of the tag
                    # dictionary and are required for category colors, aliases,
                    # implications, autocomplete completeness, and custom dataset
                    # cleanup.  Sorting continues to prefer higher post_count.
                    if post_count < 0:
                        post_count = 0
                    return (profile_key, tag, category, post_count, "[]", "[]", now)
                except Exception:
                    return None

            def flush(conn) -> None:
                nonlocal batch
                if not batch:
                    return
                conn.executemany(
                    """INSERT INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                       ON CONFLICT(source, tag) DO UPDATE SET category=excluded.category, post_count=excluded.post_count,
                       aliases_json=excluded.aliases_json, implications_json=excluded.implications_json, is_custom=0, updated_at=excluded.updated_at""",
                    batch,
                )
                batch = []

            with self.db._lock, self.db.connect() as conn:
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA synchronous=NORMAL")
                for row in rows_iter:
                    item = convert_row(list(row))
                    if item:
                        batch.append(item); count += 1
                for row in reader:
                    item = convert_row(list(row))
                    if item:
                        batch.append(item); count += 1
                    if len(batch) >= batch_size:
                        flush(conn)
                flush(conn)
                if rebuild_mirrors:
                    self._rebuild_profile_dictionary_mirrors(conn, profile_key)
        self.invalidate_cache(profile_key)
        return count

    def verified_import_dictionary_csv(self, path: Path, profile_key: str = "e621", *, replace_existing: bool = True, keep_custom: bool = True, min_expected: int = 0, progress=None) -> int:
        """Import a tag export without letting a failed/partial import damage the live dictionary.

        Replacement imports are always staged under a temporary source first.  The
        live profile is replaced only after the staged import has completed and
        passed the expected row-count check.  This avoids leaving the app with an
        empty dictionary if the process is interrupted during a multi-million-row
        DB-export import.
        """
        if not replace_existing:
            count = self.import_dictionary_csv(path, profile_key, replace_existing=False, keep_custom=keep_custom, progress=None)
            if min_expected and count < min_expected:
                raise ValueError(f"Imported only {count:,} tag rows from {Path(path).name}; expected at least {min_expected:,}.")
            if progress:
                progress(0.95, f"Imported {count:,} tag rows from {Path(path).name}")
            return count

        staging_source = f"__staging_{normalize_tag(profile_key or 'e621')}_{int(time.time() * 1000)}"
        try:
            if progress:
                progress(0.20, f"Staging tag export {Path(path).name} before replacing the live dictionary")
            count = self.import_dictionary_csv(path, staging_source, replace_existing=True, keep_custom=False, progress=None, rebuild_mirrors=False)
            if min_expected and count < min_expected:
                raise ValueError(f"Candidate {Path(path).name} contains only {count:,} valid tag rows; expected at least {min_expected:,}.")
            if progress:
                progress(0.75, f"Promoting verified dictionary with {count:,} rows")
            self._promote_staged_dictionary(staging_source, profile_key, keep_custom=keep_custom)
            if progress:
                progress(0.95, f"Imported and promoted {count:,} tag rows from {Path(path).name}")
            return count
        finally:
            self.clear_profile_dictionary(staging_source, keep_custom=False)

    def _promote_staged_dictionary(self, staging_source: str, profile_key: str, keep_custom: bool = True) -> None:
        now = now_iso()
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("BEGIN IMMEDIATE")
            if keep_custom:
                conn.execute("DELETE FROM tag_dictionary_entries WHERE source=? AND is_custom=0", (profile_key,))
            else:
                conn.execute("DELETE FROM tag_dictionary_entries WHERE source=?", (profile_key,))
            conn.execute(
                """INSERT OR REPLACE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                   SELECT ?, tag, category, post_count, aliases_json, implications_json, 0, ?
                   FROM tag_dictionary_entries WHERE source=?""",
                (profile_key, now, staging_source),
            )
            self._rebuild_profile_dictionary_mirrors(conn, profile_key)
        # Force a WAL checkpoint after the atomic promotion so a later crash
        # or terminal close has less state sitting in the WAL file.
        try:
            with self.db.connect() as checkpoint_conn:
                checkpoint_conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except Exception:
            pass
        self.invalidate_cache(profile_key)

    def should_auto_sync_default_export(self, profile_key: str | None = None, empty_only: bool = False, cache_hours: int = 336) -> bool:
        key = profile_key or "e621"
        if not self.default_export_urls(key):
            return False
        row = self.db.query_one("SELECT COUNT(*) AS n, MAX(updated_at) AS updated_at FROM tag_dictionary_entries WHERE source=?", (key,)) or {"n": 0}
        total = int(row.get("n") or 0)
        status = self.dictionary_status(key)
        if total <= 0:
            return True
        if empty_only:
            return False
        min_expected = MIN_EXPECTED_TAG_ROWS.get((key or "").lower(), 0)
        if min_expected and total < min_expected:
            return True
        if status.get("missing_roles"):
            return True
        latest = status.get("latest_imported_at") or row.get("updated_at")
        if not latest:
            return True
        try:
            dt = datetime.fromisoformat(str(latest).replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
            return age_hours >= max(1, int(cache_hours or 336))
        except Exception:
            return True

    def import_default_exports(self, profile_key: str = "e621", url: str | None = None, user_agent: str = "DataCurationTool/5.36.0", cache_hours: int = 336, progress=None, replace_existing: bool = True, force_download: bool = False) -> dict[str, Any]:
        """Download and parse the selected profile's DB-export files.

        For booru export directories this resolves the newest export for each
        role: tags, tag aliases, and tag implications. Manual direct file URLs
        are still accepted.
        """
        _raise_if_cancelled(progress)
        requested = [url] if url else self.default_export_urls(profile_key)
        requested = [u for u in requested if u]
        if not requested:
            raise ValueError("No default DB exports URL is configured for this tag profile.")
        direct_urls: list[str] = []
        discovered_pages: list[str] = []
        for candidate in requested:
            _raise_if_cancelled(progress)
            if self._looks_like_export_file(candidate):
                direct_urls.append(candidate)
            else:
                discovered = self.discover_export_urls(candidate, user_agent=user_agent)
                if discovered:
                    direct_urls.extend(discovered)
                    discovered_pages.append(candidate)
        if not url and (profile_key or "").lower() in {"e621", "e926"}:
            # Always add dated candidates.  Current export pages can be blocked,
            # cached, or not parseable from a local environment; fixed filenames
            # like tags.csv.gz can also be partial.  Dated candidates sort ahead
            # of undated candidates and prevent silently importing only a small
            # fraction of the tag dictionary.
            direct_urls.extend(self._recent_dated_export_candidates(profile_key, days=45))
        direct_urls = self._select_latest_exports_by_role(self._dedupe_urls(direct_urls))
        direct_urls.sort(key=lambda u: ({"tags": 0, "aliases": 1, "implications": 2, "artists": 3}.get(self._infer_export_role(u), 4), -self._extract_export_date_key(u)[0], 0 if "/db_exports/" in u else 1, u))
        imported_total = 0
        files: list[dict[str, Any]] = []
        total = max(len(direct_urls), 1)
        successful_roles: set[str] = set()
        replaced = False
        for idx, source_url in enumerate(direct_urls, start=1):
            _raise_if_cancelled(progress)
            role = self._infer_export_role(source_url)
            if role in successful_roles:
                files.append({"url": source_url, "role": role, "imported": 0, "skipped": "older duplicate role not needed"})
                continue
            try:
                if progress:
                    progress((idx - 1) / total, f"Downloading {role} export {idx}/{total}")
                local_path = self.download_export_file(source_url, profile_key, user_agent=user_agent, cache_hours=cache_hours, progress=progress, force_download=force_download)
                sha = self._file_sha256(local_path)
                if progress:
                    progress((idx - 0.4) / total, f"Importing {local_path.name}")
                final_min_expected = MIN_EXPECTED_TAG_ROWS.get((profile_key or "").lower(), 0)
                canonical_min_expected = 0 if final_min_expected <= 0 else MIN_CANONICAL_TAG_ROWS.get((profile_key or "").lower(), 1)
                if role == "tags":
                    pre_count = self.count_dictionary_csv_rows(local_path, profile_key)
                    low_partial = canonical_min_expected > 0 and pre_count < canonical_min_expected
                    if low_partial:
                        self._record_export_file(profile_key, role, source_url, local_path, sha, pre_count, status="partial", error=f"Candidate has {pre_count} valid canonical tag rows, below expected minimum {canonical_min_expected}; refusing to replace dictionary")
                        files.append({"url": source_url, "path": str(local_path), "role": role, "sha256": sha, "imported": 0, "candidate_rows": pre_count, "partial": True, "warning": f"below canonical minimum {canonical_min_expected}; trying next candidate"})
                        try:
                            local_path.unlink(missing_ok=True)
                        except TypeError:  # Python < 3.8 safety, kept harmless for compatibility
                            if local_path.exists():
                                local_path.unlink()
                        continue
                    count = self.verified_import_dictionary_csv(local_path, profile_key, replace_existing=replace_existing, keep_custom=True, min_expected=canonical_min_expected, progress=(lambda rows, msg, _idx=idx, _total=total: progress((_idx - 0.15) / _total, msg) if progress else None))
                    files.append({"url": source_url, "path": str(local_path), "role": role, "sha256": sha, "candidate_rows": pre_count, "canonical_import": True})
                    replaced = bool(replace_existing)
                elif role == "aliases":
                    count = self.import_aliases_csv(local_path, profile_key)
                elif role == "implications":
                    count = self.import_implications_csv(local_path, profile_key)
                elif role == "artists":
                    count = self.import_artists_csv(local_path, profile_key)
                else:
                    count = 0
                imported_total += count
                successful_roles.add(role)
                self._record_export_file(profile_key, role, source_url, local_path, sha, count, status="imported")
                files.append({"url": source_url, "path": str(local_path), "role": role, "sha256": sha, "imported": count})
            except Exception as exc:
                self._record_export_file(profile_key, role, source_url, None, "", 0, status="failed", error=str(exc))
                files.append({"url": source_url, "role": role, "imported": 0, "error": str(exc)})
        if "tags" in successful_roles:
            _raise_if_cancelled(progress)
            expanded = self.expand_dictionary_from_relations(profile_key)
            imported_total += int(expanded.get("added", 0) or 0)
            files.append({"role": "dictionary_expansion", **expanded})
        self.invalidate_cache(profile_key)
        final_min_expected = MIN_EXPECTED_TAG_ROWS.get((profile_key or "").lower(), 0)
        final_status = self.dictionary_status(profile_key)
        final_total = int(final_status.get("total") or 0)
        if final_min_expected and final_total < final_min_expected:
            attempted = [f.get("url") for f in files if f.get("role") == "tags"]
            raise RuntimeError(
                f"No complete searchable tag dictionary was imported for {profile_key}. "
                f"The final dictionary has {final_total:,} rows, below the expected minimum {final_min_expected:,}. "
                f"Attempted {len(attempted)} canonical tag candidate(s). Check the Tag Dictionaries job details for partial/error rows."
            )
        return {"profile_key": profile_key, "imported": imported_total, "replaced_existing": replaced, "files": files, "discovered_pages": discovered_pages, "status": final_status}

    def expand_dictionary_from_relations(self, profile_key: str = "e621") -> dict[str, Any]:
        """Add searchable alias/implication terms after canonical tags import.

        Some booru exports keep the canonical tag table relatively small while
        aliases and implications contain many additional strings that users type
        or encounter in older sidecars.  The HUD autocomplete/coloring layer must
        know about those terms too.  Canonical tags are imported first; then alias
        and implication terms that are not already canonical are inserted with the
        category/post_count of their resolved canonical target when available.
        """
        profile_key = profile_key or "e621"
        now = now_iso()
        before = int((self.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source=?", (profile_key,)) or {"n": 0}).get("n") or 0)
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            # Alias terms should be searchable and colorable. Prefer the target
            # tag's category/count when the target exists; otherwise mark the
            # alias as invalid so it is still visible and editable.
            conn.execute(
                """INSERT OR IGNORE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                   SELECT a.source, a.alias,
                          COALESCE(t.category, 'invalid') AS category,
                          COALESCE(t.post_count, 0) AS post_count,
                          json_array(a.target), '[]', 0, ?
                   FROM tag_aliases a
                   LEFT JOIN tag_dictionary_entries t ON t.source=a.source AND t.tag=a.target
                   WHERE a.source=? AND a.alias <> ''""",
                (now, profile_key),
            )
            # Implication antecedents/consequents are also user-visible terms.
            # If a relation endpoint is not in the canonical tag table, keep it
            # searchable as general so it no longer appears as an uncolored hole.
            conn.execute(
                """INSERT OR IGNORE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                   SELECT i.source, i.antecedent,
                          COALESCE(t.category, 'general') AS category,
                          COALESCE(t.post_count, 0) AS post_count,
                          '[]', json_array(i.consequent), 0, ?
                   FROM tag_implications i
                   LEFT JOIN tag_dictionary_entries t ON t.source=i.source AND t.tag=i.antecedent
                   WHERE i.source=? AND i.antecedent <> ''""",
                (now, profile_key),
            )
            conn.execute(
                """INSERT OR IGNORE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                   SELECT i.source, i.consequent,
                          COALESCE(t.category, 'general') AS category,
                          COALESCE(t.post_count, 0) AS post_count,
                          '[]', '[]', 0, ?
                   FROM tag_implications i
                   LEFT JOIN tag_dictionary_entries t ON t.source=i.source AND t.tag=i.consequent
                   WHERE i.source=? AND i.consequent <> ''""",
                (now, profile_key),
            )
            self._rebuild_profile_dictionary_mirrors(conn, profile_key)
        after = int((self.db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source=?", (profile_key,)) or {"n": 0}).get("n") or 0)
        added = max(0, after - before)
        self.invalidate_cache(profile_key)
        return {"profile_key": profile_key, "before": before, "after": after, "added": added}

    def _rebuild_profile_dictionary_mirrors(self, conn, profile_key: str) -> None:
        """Rebuild autocomplete/search and legacy dictionary mirrors for a profile.

        The canonical table is ``tag_dictionary_entries``.  The HUD autocomplete
        uses ``tag_dictionary_search`` for fast lower-case prefix/substring lookup,
        so it must be repopulated after PyArrow imports and relation expansion.
        For million-row dictionaries the legacy mirror and old autocomplete
        mirror are intentionally not fully duplicated because doing so can triple
        import time and disk use. Modern autocomplete and category lookup read
        ``tag_dictionary_entries`` directly, whose primary key indexes
        ``(source, tag)`` for prefix lookups.
        """
        total = int(conn.execute("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source=?", (profile_key,)).fetchone()["n"] or 0)
        conn.execute("DELETE FROM tag_dictionary_search WHERE source=? AND is_custom=0", (profile_key,))
        conn.execute("DELETE FROM tag_dictionary")
        if total <= 250000:
            conn.execute("DROP INDEX IF EXISTS idx_tag_search_source_lower")
            conn.execute(
                """INSERT OR REPLACE INTO tag_dictionary_search(source, tag, tag_lower, category, post_count, is_custom, updated_at)
                   SELECT source, tag, lower(tag), category, post_count, is_custom, updated_at
                   FROM tag_dictionary_entries WHERE source=?""",
                (profile_key,),
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tag_search_source_lower ON tag_dictionary_search(source, tag_lower)")
            conn.execute(
                """INSERT OR REPLACE INTO tag_dictionary(tag, category, post_count, aliases_json, implications_json, updated_at)
                   SELECT tag, category, post_count, aliases_json, implications_json, updated_at
                   FROM tag_dictionary_entries WHERE source=?""",
                (profile_key,),
            )

    def discover_export_urls(self, page_url: str, user_agent: str = "DataCurationTool/5.36.0") -> list[str]:
        if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("DCT_SKIP_STARTUP_TAG_SYNC") == "1":
            return []
        urls: list[str] = []
        for candidate_page in self._export_page_candidates(page_url):
            text = self._download_text(candidate_page, user_agent=user_agent)
            if not text:
                continue
            # Keep compatibility with the original tool's permissive page scan: it
            # read the export listing and searched each line for tags\S*?\.gz.
            # This handles plain directory listings, HTML hrefs, and bare text.
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I)
            raw_matches = re.findall(
                r'(?:https?://[^\s"\'<>]+/)?(?:tag_aliases|tag_alias|tag_implications|tag_implication|artists|tags)\S*?\.gz',
                text,
                flags=re.I,
            )
            for raw in [*hrefs, *raw_matches]:
                cleaned = html.unescape(str(raw or "")).strip().strip('"\'<>')
                cleaned = re.split(r'[\s<>]', cleaned, maxsplit=1)[0].strip().strip('"\',;')
                if not cleaned:
                    continue
                absolute = urljoin(candidate_page, cleaned)
                low = absolute.lower().split("?", 1)[0]
                if any(token in low for token in ("tags", "tag_alias", "tag_aliases", "tag_implication", "tag_implications", "artists")) and low.endswith((".csv", ".csv.gz", ".tsv", ".tsv.gz", ".txt", ".txt.gz", ".gz")):
                    urls.append(absolute)
            if urls:
                break
        return self._dedupe_urls(urls)

    def _download_text(self, url: str, user_agent: str = "DataCurationTool/5.36.0") -> str:
        headers = {"User-Agent": user_agent, "Accept": "text/html,text/plain,*/*"}
        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.text
        except Exception:
            pass
        # Same Windows-friendly fallback style as the original tool: curl with
        # --ssl-no-revoke avoids certificate revocation failures that can block
        # export-page downloads on some Windows setups.
        curl = shutil.which("curl")
        if not curl:
            return ""
        cmd = [curl, "-L", "--fail", "--silent", "--show-error", "--ssl-no-revoke", "-A", user_agent, url]
        try:
            completed = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            return completed.stdout.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _export_page_candidates(self, url: str) -> list[str]:
        raw = (url or "").strip()
        if not raw:
            return []
        base = raw.rstrip("/")

        def as_directory(page: str) -> str:
            # ``urljoin('https://host/db_exports', 'tags.csv.gz')`` incorrectly
            # resolves to ``https://host/tags.csv.gz``.  DB-export page URLs must
            # keep their trailing slash so discovered relative hrefs stay inside
            # /db_exports/.  This bug was the cause of zero-row dictionaries when
            # page discovery succeeded but every discovered file URL 404'd.
            return page if self._looks_like_export_file(page) else page.rstrip("/") + "/"

        candidates = [as_directory(base)]
        # Current e621/e926 export pages use /db_exports.  Preserve support for
        # stale configs and older booru mirrors that still use /db_export.
        if base.endswith("/db_export"):
            candidates.insert(0, as_directory(base[:-len("/db_export")] + "/db_exports"))
        elif base.endswith("/db_exports"):
            candidates.append(as_directory(base[:-len("/db_exports")] + "/db_export"))
        return self._dedupe_urls(candidates)

    def _dedupe_urls(self, urls: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for url in urls:
            if not url or url in seen:
                continue
            seen.add(url)
            result.append(url)
        return result

    def download_export_file(self, url: str, profile_key: str, user_agent: str = "DataCurationTool/5.36.0", cache_hours: int = 336, progress=None, force_download: bool = False) -> Path:
        _raise_if_cancelled(progress)
        if not self.paths:
            raise RuntimeError("Tag export downloads require AppPaths.")
        parsed = urlparse(url)
        filename = Path(parsed.path).name or "tags.csv.gz"
        target = self.paths.runtime / "tag_exports" / normalize_tag(profile_key or "custom") / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if force_download:
            try:
                target.unlink(missing_ok=True)
            except TypeError:
                if target.exists():
                    target.unlink()
        if target.exists() and target.stat().st_size > 0:
            if cache_hours > 0:
                age_hours = (time.time() - target.stat().st_mtime) / 3600.0
                if age_hours < cache_hours:
                    return target
            known_cached = self.db.query_one(
                "SELECT row_count FROM tag_export_files WHERE profile_key=? AND local_path=? AND row_count > 0 ORDER BY imported_at DESC, downloaded_at DESC LIMIT 1",
                (profile_key, str(target)),
            )
            if known_cached:
                return target
        tmp = target.with_suffix(target.suffix + ".part")
        headers = {"User-Agent": user_agent, "Accept": "text/csv,application/gzip,application/octet-stream,*/*"}
        last_error: Exception | None = None
        try:
            with requests.get(url, headers=headers, timeout=180, stream=True) as response:
                response.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        _raise_if_cancelled(progress)
                        if chunk:
                            f.write(chunk)
            if tmp.exists() and tmp.stat().st_size > 0:
                tmp.replace(target)
                return target
            raise RuntimeError("Downloaded tag export was empty")
        except Exception as exc:
            last_error = exc
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass

        curl = shutil.which("curl")
        if curl:
            _raise_if_cancelled(progress)
            cmd = [curl, "-L", "--fail", "--silent", "--show-error", "--ssl-no-revoke", "-A", user_agent, "-o", str(tmp), url]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240)
                _raise_if_cancelled(progress)
                if tmp.exists() and tmp.stat().st_size > 0:
                    tmp.replace(target)
                    return target
                raise RuntimeError("curl downloaded an empty tag export")
            except Exception as exc:
                last_error = exc
                try:
                    if tmp.exists():
                        tmp.unlink()
                except Exception:
                    pass
        raise RuntimeError(f"Failed to download tag export {url}: {last_error}")

    def clear_profile_dictionary(self, profile_key: str, keep_custom: bool = True) -> None:
        if keep_custom:
            self.db.execute("DELETE FROM tag_dictionary_entries WHERE source=? AND is_custom=0", (profile_key,))
            self.db.execute("DELETE FROM tag_dictionary_search WHERE source=? AND is_custom=0", (profile_key,))
        else:
            self.db.execute("DELETE FROM tag_dictionary_entries WHERE source=?", (profile_key,))
            self.db.execute("DELETE FROM tag_dictionary_search WHERE source=?", (profile_key,))
        self.db.execute("DELETE FROM tag_aliases WHERE source=?", (profile_key,))
        self.db.execute("DELETE FROM tag_implications WHERE source=?", (profile_key,))
        self.db.execute("DELETE FROM artist_aliases WHERE source=?", (profile_key,))
        self.invalidate_cache(profile_key)

    def reapply_categories(self, media_ids: list[int] | None = None, dataset_id: int | None = None, profile_key: str = "e621", save_sidecars: bool = False) -> dict[str, Any]:
        where = ["active=1"]
        params: list[Any] = []
        if media_ids:
            placeholders = ",".join("?" for _ in media_ids)
            where.append(f"id IN ({placeholders})")
            params.extend(media_ids)
        if dataset_id is not None:
            where.append("dataset_id=?")
            params.append(dataset_id)
        rows = self.db.query(f"SELECT id FROM media WHERE {' AND '.join(where)}", params)
        changed = 0
        for row in rows:
            media_id = int(row["id"])
            tags = self.get_tags(media_id)
            if tags:
                self.set_tags(media_id, tags, source="category_reapply", save_sidecar=save_sidecars, profile_key=profile_key, order_strategy="retain")
                changed += 1
        return {"profile_key": profile_key, "changed": changed, "media_ids": [int(r["id"]) for r in rows]}

    def _extract_export_date_key(self, url_or_name: str) -> tuple[int, str]:
        text = str(url_or_name)
        matches = re.findall(r"(20\d{2})[-_](\d{2})[-_](\d{2})", text)
        if matches:
            y, m, d = matches[-1]
            return (int(f"{y}{m}{d}"), text)
        return (0, text)

    def _select_latest_exports_by_role(self, urls: Iterable[str]) -> list[str]:
        # Keep all discovered candidates but order each role newest-first. The
        # importer stops downloading a role once one candidate succeeds. This
        # handles sites where today's dated file is listed but not yet populated.
        by_role: dict[str, list[str]] = {"tags": [], "aliases": [], "implications": [], "artists": []}
        other: list[str] = []
        for url in urls:
            role = self._infer_export_role(url)
            if role in by_role:
                by_role[role].append(url)
            else:
                other.append(url)
        result: list[str] = []
        for role in ("tags", "aliases", "implications", "artists"):
            result.extend(sorted(by_role[role], key=lambda u: self._extract_export_date_key(u), reverse=True))
        result.extend(other)
        return self._dedupe_urls(result)

    def _recent_dated_export_candidates(self, profile_key: str, days: int = 21) -> list[str]:
        from datetime import timedelta
        key = (profile_key or "e621").lower()
        host = "https://e926.net" if key == "e926" else "https://e621.net"
        roles = ("tags", "tag_aliases", "tag_implications", "artists")
        urls: list[str] = []
        today = datetime.now(timezone.utc).date()
        for offset in range(max(1, int(days or 21))):
            stamp = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
            for role in roles:
                urls.append(f"{host}/db_exports/{role}-{stamp}.csv.gz")
        return urls

    def _file_sha256(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _record_export_file(self, profile_key: str, role: str, url: str, local_path: Path | None, sha256: str, row_count: int, status: str = "imported", error: str = "") -> None:
        now = now_iso()
        self.db.execute(
            """INSERT INTO tag_export_files(profile_key, role, url, local_path, sha256, downloaded_at, imported_at, row_count, status, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(profile_key, role, url) DO UPDATE SET local_path=excluded.local_path, sha256=excluded.sha256,
               downloaded_at=excluded.downloaded_at, imported_at=excluded.imported_at, row_count=excluded.row_count,
               status=excluded.status, error=excluded.error""",
            (profile_key, role, url, str(local_path or ""), sha256 or "", now if local_path else "", now if status == "imported" else "", int(row_count or 0), status, error or ""),
        )

    def import_aliases_csv(self, path: Path, profile_key: str = "e621") -> int:
        """Import alias pairs in bulk into the normalized alias table."""
        now = now_iso()
        arrow_rows = self._arrow_pair_rows(path, profile_key, "antecedent_name", "consequent_name", now)
        if arrow_rows is not None:
            with self.db._lock, self.db.connect() as conn:
                conn.execute("PRAGMA temp_store=MEMORY")
                for start in range(0, len(arrow_rows), 100000):
                    self._flush_alias_batch(conn, arrow_rows[start:start + 100000])
            self.invalidate_cache(profile_key)
            return len(arrow_rows)
        count = 0
        batch_pairs: list[tuple[Any, ...]] = []
        batch_size = 25000
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            for alias, target in self._iter_pair_export(path, "antecedent_name", "consequent_name"):
                batch_pairs.append((profile_key, alias, target, "active", now))
                count += 1
                if len(batch_pairs) >= batch_size:
                    self._flush_alias_batch(conn, batch_pairs)
                    batch_pairs = []
            self._flush_alias_batch(conn, batch_pairs)
        self.invalidate_cache(profile_key)
        return count

    def _flush_alias_batch(self, conn, alias_rows: list[tuple[Any, ...]]) -> None:
        if alias_rows:
            conn.executemany(
                """INSERT OR REPLACE INTO tag_aliases(source, alias, target, status, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                alias_rows,
            )

    def import_implications_csv(self, path: Path, profile_key: str = "e621") -> int:
        """Import implication pairs in bulk into a normalized table."""
        now = now_iso()
        arrow_rows = self._arrow_pair_rows(path, profile_key, "antecedent_name", "consequent_name", now)
        if arrow_rows is not None:
            with self.db._lock, self.db.connect() as conn:
                conn.execute("PRAGMA temp_store=MEMORY")
                for start in range(0, len(arrow_rows), 100000):
                    conn.executemany(
                        """INSERT OR REPLACE INTO tag_implications(source, antecedent, consequent, status, updated_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        arrow_rows[start:start + 100000],
                    )
            self.invalidate_cache(profile_key)
            return len(arrow_rows)
        count = 0
        batch: list[tuple[Any, ...]] = []
        batch_size = 25000
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            for source, implied in self._iter_pair_export(path, "antecedent_name", "consequent_name"):
                batch.append((profile_key, source, implied, "active", now))
                count += 1
                if len(batch) >= batch_size:
                    conn.executemany(
                        """INSERT OR REPLACE INTO tag_implications(source, antecedent, consequent, status, updated_at)
                           VALUES (?, ?, ?, ?, ?)""",
                        batch,
                    )
                    batch = []
            if batch:
                conn.executemany(
                    """INSERT OR REPLACE INTO tag_implications(source, antecedent, consequent, status, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    batch,
                )
        self.invalidate_cache(profile_key)
        return count

    def import_artists_csv(self, path: Path, profile_key: str = "e621") -> int:
        """Import artists.csv as artist-category tags plus artist-only aliases.

        e621/e926 artists.csv exposes ``name`` and ``other_names``. ``other_names``
        is a braced comma-separated alias list such as ``{alias1,alias2}``.
        The canonical artist name is inserted as an artist tag and every alias is
        inserted into both ``artist_aliases`` and ``tag_aliases`` so autocomplete
        can surface alias -> canonical corrections.
        """
        now = now_iso()
        parsed = self._arrow_artist_rows(path, profile_key, now)
        if parsed is None:
            return self._import_artists_csv_python(path, profile_key, now)
        dict_rows, alias_rows, artist_alias_rows = parsed
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            for start in range(0, len(dict_rows), 100000):
                conn.executemany(
                    """INSERT INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                       ON CONFLICT(source, tag) DO UPDATE SET category=excluded.category, post_count=excluded.post_count, updated_at=excluded.updated_at""",
                    dict_rows[start:start + 100000],
                )
            for start in range(0, len(alias_rows), 100000):
                self._flush_alias_batch(conn, alias_rows[start:start + 100000])
            for start in range(0, len(artist_alias_rows), 100000):
                conn.executemany(
                    """INSERT OR REPLACE INTO artist_aliases(source, artist_name, alias, is_active, updated_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    artist_alias_rows[start:start + 100000],
                )
        self.invalidate_cache(profile_key)
        return len(dict_rows) + len(alias_rows)

    def _import_artists_csv_python(self, path: Path, profile_key: str, now: str) -> int:
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open
        dict_rows: list[tuple[Any, ...]] = []
        alias_rows: list[tuple[Any, ...]] = []
        artist_alias_rows: list[tuple[Any, ...]] = []
        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = {str(x or "").strip().lower() for x in (reader.fieldnames or [])}
            if "name" not in fieldnames or "other_names" not in fieldnames:
                return 0
            for row in reader:
                artist = normalize_tag(row.get("name"))
                if not artist:
                    continue
                active_text = str(row.get("is_active", "true")).strip().lower()
                if active_text in {"0", "false", "f", "no", "n", "deleted", "inactive"}:
                    continue
                dict_rows.append((profile_key, artist, "artist", 0, "[]", "[]", now))
                for alias in self._parse_artist_other_names(row.get("other_names")):
                    if alias and alias != artist:
                        alias_rows.append((profile_key, alias, artist, "artist_alias", now))
                        artist_alias_rows.append((profile_key, artist, alias, 1, now))
        with self.db._lock, self.db.connect() as conn:
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.executemany(
                """INSERT INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, 0, ?)
                   ON CONFLICT(source, tag) DO UPDATE SET category=excluded.category, post_count=excluded.post_count, updated_at=excluded.updated_at""",
                dict_rows,
            )
            self._flush_alias_batch(conn, alias_rows)
            conn.executemany(
                """INSERT OR REPLACE INTO artist_aliases(source, artist_name, alias, is_active, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                artist_alias_rows,
            )
        self.invalidate_cache(profile_key)
        return len(dict_rows) + len(alias_rows)

    def _read_pair_export(self, path: Path, left_key: str, right_key: str) -> list[tuple[str, str]]:
        return list(self._iter_pair_export(path, left_key, right_key))

    def _iter_pair_export(self, path: Path, left_key: str, right_key: str):
        opener = gzip.open if any(str(path).lower().endswith(ext) for ext in (".gz", ".gzip")) else open
        with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as f:
            sample = f.read(8192)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
            except csv.Error:
                dialect = csv.excel_tab if "\t" in sample and "," not in sample else csv.excel
            reader = csv.reader(f, dialect=dialect)
            try:
                first = next(reader)
            except StopIteration:
                return
            header = [str(x or "").strip().lower() for x in first]
            headerless = left_key not in header and right_key not in header and "antecedent_name" not in header and "consequent_name" not in header
            if headerless:
                rows_iter = [first]
                left_idx, right_idx, status_idx = 0, 1, None
            else:
                rows_iter = []
                def find(names: tuple[str, ...], default: int | None = None) -> int | None:
                    for name in names:
                        if name in header:
                            return header.index(name)
                    return default
                left_idx = find((left_key, "antecedent_name", "from", "alias", "old_name"), 0) or 0
                right_idx = find((right_key, "consequent_name", "to", "tag", "new_name"), 1) or 1
                status_idx = find(("status", "state"), None)
            for row in rows_iter:
                left, right = self._pair_from_row(list(row), left_idx, right_idx, status_idx)
                if left and right:
                    yield left, right
            for row in reader:
                left, right = self._pair_from_row(list(row), left_idx, right_idx, status_idx)
                if left and right:
                    yield left, right

    def _pair_from_row(self, row: list[Any], left_idx: int, right_idx: int, status_idx: int | None) -> tuple[str, str]:
        if status_idx is not None and status_idx < len(row):
            status = str(row[status_idx] or "active").lower()
            if status in {"deleted", "rejected", "pending", "retired"}:
                return "", ""
        left = normalize_tag(row[left_idx] if left_idx < len(row) else "")
        right = normalize_tag(row[right_idx] if right_idx < len(row) else "")
        return left, right

    def _looks_like_export_file(self, url: str) -> bool:
        low = url.lower().split("?", 1)[0]
        return low.endswith((".csv", ".csv.gz", ".tsv", ".tsv.gz", ".txt", ".txt.gz", ".gz"))

    def _infer_export_role(self, url_or_name: str) -> str:
        low = str(url_or_name).lower()
        if "artist" in low:
            return "artists"
        if "alias" in low:
            return "aliases"
        if "implication" in low:
            return "implications"
        return "tags"

    def upsert_dictionary_entry(self, profile_key: str, tag: str, category: str, post_count: int = 0, aliases: list[str] | None = None, implications: list[str] | None = None, is_custom: bool = False) -> None:
        profile_key = profile_key or "custom"; tag = normalize_tag(tag); category = self.normalize_category(category, profile_key)
        if not tag: return
        ts = now_iso()
        self.db.execute("""INSERT INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(source, tag) DO UPDATE SET category=excluded.category, post_count=excluded.post_count, aliases_json=excluded.aliases_json, implications_json=excluded.implications_json, is_custom=excluded.is_custom, updated_at=excluded.updated_at""", (profile_key, tag, category, int(post_count or 0), json.dumps(aliases or []), json.dumps(implications or []), 1 if is_custom else 0, ts))
        self.db.execute("""INSERT INTO tag_dictionary_search(source, tag, tag_lower, category, post_count, is_custom, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(source, tag) DO UPDATE SET tag_lower=excluded.tag_lower, category=excluded.category, post_count=excluded.post_count, is_custom=excluded.is_custom, updated_at=excluded.updated_at""", (profile_key, tag, tag.lower(), category, int(post_count or 0), 1 if is_custom else 0, ts))
        self.invalidate_cache(profile_key)

    def upsert_dictionary_tag(self, profile_key: str, tag: str, category: str, post_count: int = 0, aliases: list[str] | None = None, implications: list[str] | None = None, is_custom: bool = False) -> None:
        """Backward-compatible alias for tests/plugins that used the older helper name."""
        self.upsert_dictionary_entry(profile_key, tag, category, post_count=post_count, aliases=aliases, implications=implications, is_custom=is_custom)

    def add_custom_tag(self, profile_key: str, tag: str, category: str, note: str | None = None, color: str | None = None) -> dict[str, Any]:
        profile_key = profile_key or "custom"; tag = normalize_tag(tag)
        raw_category = str(category or "custom").strip().lower().replace(" ", "_")
        mapped = CATEGORY_ALIASES.get(raw_category, raw_category or "custom")
        if mapped not in {item["key"] for item in self.categories(profile_key)} and mapped not in {"0","1","2","3","4","5","6","7","8"}:
            self.add_category(profile_key, mapped, label=str(category or mapped).replace("_", " ").title())
        if mapped not in {item["key"] for item in self.categories("custom")}:  # ensure global category exists too
            self.add_category("custom", mapped, label=str(category or mapped).replace("_", " ").title())
        category = self.normalize_category(mapped, profile_key)
        if not tag: raise ValueError("Custom tag cannot be empty.")
        # Global custom entry has priority no matter which booru profile is active.
        self.upsert_dictionary_entry("custom", tag, category, post_count=0, aliases=[], implications=[], is_custom=True)
        if profile_key != "custom":
            self.upsert_dictionary_entry(profile_key, tag, category, post_count=0, aliases=[], implications=[], is_custom=True)
        payload = load_json(self._custom_tags_path, {}) or {}
        record = {"category": category, "note": note or "", "color": color or "", "updated_at": now_iso()}
        payload.setdefault("custom", {})[tag] = record
        if profile_key != "custom":
            payload.setdefault(profile_key, {})[tag] = record
        save_json(self._custom_tags_path, payload)
        return {"profile_key": profile_key, "tag": tag, "category": category, "color": color or "", "path": str(self._custom_tags_path)}

    def custom_tags(self, profile_key: str | None = None) -> dict[str, Any]:
        payload = load_json(self._custom_tags_path, {}) or {}
        return payload.get(profile_key, {}) if profile_key else payload

    def _load_custom_tags_file_into_db(self) -> None:
        for profile_key, tags in (load_json(self._custom_tags_path, {}) or {}).items():
            if isinstance(tags, dict):
                for tag, item in tags.items():
                    category = item.get("category") if isinstance(item, dict) else str(item or "custom")
                    self.upsert_dictionary_entry(profile_key, tag, category or "custom", is_custom=True)

    def suggest(self, prefix: str, limit: int = 50, profile_key: str | None = None, include_custom: bool = True) -> list[dict[str, str | int | bool]]:
        """Return fast profile-aware autocomplete suggestions.

        Prefix matches are resolved with SQLite indexes and only fall back to a
        bounded contains search when needed.  This avoids the laggy Python-side
        full scans that made the older tag dropdowns feel sluggish.
        """
        profile_key = profile_key or "e621"
        clean = normalize_tag(prefix).lower()
        limit = max(1, min(int(limit or 50), 500))
        sources = [profile_key]
        if include_custom and profile_key != "custom":
            sources.append("custom")
        placeholders = ",".join("?" for _ in sources)
        allowed_categories = {item["key"] for item in self.categories(profile_key)}
        def norm_fast(value: Any) -> str:
            raw = str(value or "unknown").strip().lower().replace(" ", "_")
            mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
            if mapped in allowed_categories:
                return mapped
            if mapped == "deprecated":
                return "invalid"
            return "custom" if mapped else "unknown"
        rows: list[dict[str, Any]] = []
        if not clean:
            rows = self.db.query(
                f"""SELECT source, tag, category, post_count, is_custom, aliases_json, implications_json FROM tag_dictionary_entries
                    WHERE source IN ({placeholders})
                    ORDER BY CASE WHEN source=? THEN 0 ELSE 1 END, post_count DESC, tag ASC
                    LIMIT ?""",
                (*sources, profile_key, limit),
            )
        else:
            upper = clean + chr(0x10FFFF)
            rows = self.db.query(
                f"""SELECT source, tag, category, post_count, is_custom, aliases_json, implications_json FROM tag_dictionary_entries
                    WHERE source IN ({placeholders}) AND tag >= ? AND tag < ?
                    ORDER BY CASE WHEN source=? THEN 0 ELSE 1 END, post_count DESC, tag ASC
                    LIMIT ?""",
                (*sources, clean, upper, profile_key, limit * 4),
            )
            if len(rows) < limit:
                seen = {r["tag"] for r in rows}
                contains = self.db.query(
                    f"""SELECT source, tag, category, post_count, is_custom, aliases_json, implications_json FROM tag_dictionary_entries
                        WHERE source IN ({placeholders}) AND tag LIKE ?
                        ORDER BY CASE WHEN source=? THEN 0 ELSE 1 END, post_count DESC, tag ASC
                        LIMIT ?""",
                    (*sources, f"%{clean}%", profile_key, limit * 2),
                )
                for row in contains:
                    if row["tag"] not in seen:
                        rows.append(row)
                        seen.add(row["tag"])
                    if len(rows) >= limit * 4:
                        break
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows:
            tag = normalize_tag(row.get("tag"))
            if not tag:
                continue
            rec = {
                "tag": tag,
                "category": norm_fast(row.get("category")),
                "post_count": int(row.get("post_count") or 0),
                "source": row.get("source") or profile_key,
                "custom": bool(row.get("is_custom")),
            }
            alias_targets = _json_loads(row.get("aliases_json"), []) or []
            implication_targets = _json_loads(row.get("implications_json"), []) or []
            if alias_targets:
                rec["alias_target"] = str(alias_targets[0])
                rec["alias_targets"] = [str(x) for x in alias_targets]
            if implication_targets:
                rec["implications"] = [str(x) for x in implication_targets]
            existing = deduped.get(tag)
            if not existing:
                deduped[tag] = rec
            elif rec.get("source") == "custom" or rec.get("custom"):
                deduped[tag] = rec
            elif not (existing.get("source") == "custom" or existing.get("custom")) and rec["post_count"] > int(existing.get("post_count") or 0):
                deduped[tag] = rec
        matches = list(deduped.values())
        if clean:
            matches.sort(key=lambda r: (0 if str(r["tag"]).lower().startswith(clean) else 1, -int(r["post_count"]), str(r["tag"])))
        else:
            matches.sort(key=lambda r: (-int(r["post_count"]), str(r["tag"])))
        return [dict(r) for r in matches[:limit]]

    def invalidate_cache(self, profile_key: str | None = None) -> None:
        with self._cache_lock:
            if profile_key is None: self._suggest_cache.clear()
            else:
                for key in list(self._suggest_cache):
                    if key.startswith(f"{profile_key}|") or key.startswith("custom|"): self._suggest_cache.pop(key, None)

    def metadata_bulk(self, tags: Iterable[str], profile_key: str | None = None) -> dict[str, dict[str, Any]]:
        """Resolve metadata for many tags with a handful of indexed queries."""
        profile_key = profile_key or "e621"
        cleaned = _dedupe_clean(tags)
        result: dict[str, dict[str, Any]] = {}
        if not cleaned:
            return result
        allowed_categories = {item["key"] for item in self.categories(profile_key)}
        def norm_fast(value: Any) -> str:
            raw = str(value or "unknown").strip().lower().replace(" ", "_")
            mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
            if mapped in allowed_categories:
                return mapped
            if mapped == "deprecated":
                return "invalid"
            return "custom" if mapped else "unknown"

        def query_source(source: str, wanted: list[str]) -> dict[str, dict[str, Any]]:
            found: dict[str, dict[str, Any]] = {}
            for start in range(0, len(wanted), 800):
                chunk = wanted[start:start + 800]
                placeholders = ",".join("?" for _ in chunk)
                rows = self.db.query(
                    f"SELECT tag, category, post_count, is_custom, aliases_json, implications_json FROM tag_dictionary_entries WHERE source=? AND tag IN ({placeholders})",
                    (source, *chunk),
                )
                for row in rows:
                    tag = row["tag"]
                    info = {
                        "tag": tag,
                        "category": norm_fast(row.get("category")),
                        "post_count": int(row.get("post_count") or 0),
                        "known": True,
                        "custom": bool(row.get("is_custom")),
                    }
                    alias_targets = _json_loads(row.get("aliases_json"), []) or []
                    implication_targets = _json_loads(row.get("implications_json"), []) or []
                    if alias_targets:
                        info["alias_target"] = str(alias_targets[0])
                        info["alias_targets"] = [str(x) for x in alias_targets]
                    if implication_targets:
                        info["implications"] = [str(x) for x in implication_targets]
                    found[tag] = info
            return found

        custom_rows = query_source("custom", cleaned)
        result.update(custom_rows)
        remaining = [tag for tag in cleaned if tag not in result]
        result.update(query_source(profile_key, remaining))
        remaining = [tag for tag in cleaned if tag not in result]
        # Alias rows are kept in their normalized table so they do not inflate the
        # real tag dictionary count.  They still resolve as known/invalid for
        # editor coloring and cleanup workflows.
        for start in range(0, len(remaining), 800):
            chunk = remaining[start:start + 800]
            if not chunk:
                continue
            placeholders = ",".join("?" for _ in chunk)
            rows = self.db.query(f"SELECT alias, target FROM tag_aliases WHERE source=? AND alias IN ({placeholders})", (profile_key, *chunk))
            for row in rows:
                alias = row["alias"]
                result[alias] = {"tag": alias, "category": norm_fast("invalid"), "post_count": 0, "known": True, "custom": False, "alias_target": row.get("target") or ""}
        remaining = [tag for tag in cleaned if tag not in result]
        for start in range(0, len(remaining), 800):
            chunk = remaining[start:start + 800]
            if not chunk:
                continue
            placeholders = ",".join("?" for _ in chunk)
            rows = self.db.query(f"SELECT tag, category, post_count FROM tag_dictionary WHERE tag IN ({placeholders})", chunk)
            for row in rows:
                tag = row["tag"]
                result[tag] = {"tag": tag, "category": norm_fast(row.get("category")), "post_count": int(row.get("post_count") or 0), "known": True, "custom": False}
        allowed_categories = {item["key"] for item in self.categories(profile_key)}
        def heuristic_category(tag: str) -> str:
            low = tag.lower()
            for cat, needles in CATEGORY_KEYWORDS.items():
                if any(low == n or low.startswith(n) or n in low for n in needles):
                    mapped = CATEGORY_ALIASES.get(cat, cat)
                    return mapped if mapped in allowed_categories else "custom"
            return "unknown"
        for tag in cleaned:
            if tag not in result:
                result[tag] = {"tag": tag, "category": heuristic_category(tag), "post_count": 0, "known": False, "custom": False}
        return result

    def prepare_tag_pairs(self, tags: Iterable[str], profile_key: str | None = None, order_strategy: str = "retain", category_overrides: dict[str, str] | None = None, metadata_map: dict[str, dict[str, Any]] | None = None) -> list[tuple[str, str]]:
        profile_key = profile_key or "e621"
        overrides = {normalize_tag(k): v for k, v in (category_overrides or {}).items() if normalize_tag(k)}
        cleaned = _dedupe_clean(tags)
        meta = metadata_map or self.metadata_bulk(cleaned, profile_key)
        allowed_categories = {item["key"] for item in self.categories(profile_key)}
        def norm_fast(value: Any) -> str:
            raw = str(value or "unknown").strip().lower().replace(" ", "_")
            mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
            if mapped in allowed_categories:
                return mapped
            if mapped == "deprecated":
                return "invalid"
            return "custom" if mapped else "unknown"
        strategy = (order_strategy or "retain").replace("-", "_")
        ordered = list(cleaned)
        if strategy not in {"retain", "custom", "none", "source"}:
            effective_profile = "lora-purpose" if strategy == "lora_purpose" else profile_key
            profile = self.get_profile(effective_profile)
            rank = {cat: idx for idx, cat in enumerate(profile.get("precedence") or [])}
            ordered = [tag for _, tag in sorted(enumerate(cleaned), key=lambda item: (rank.get(str(meta.get(item[1], {}).get("category") or "unknown"), len(rank) + 1), item[0]))]
        pairs: list[tuple[str, str]] = []
        for tag in ordered:
            info = meta.get(tag) or {}
            if info.get("custom"):
                category = norm_fast(info.get("category"))
            elif tag in overrides:
                category = norm_fast(overrides[tag])
            else:
                category = norm_fast(info.get("category") or "unknown")
            pairs.append((tag, category))
        return pairs

    def set_tags_many(self, items: dict[int, dict[str, Any]], source: str = "import", profile_key: str | None = None, order_strategy: str = "retain") -> None:
        """Replace tags for many media IDs using batched category lookups."""
        if not items:
            return
        profile_key = profile_key or "e621"
        all_tags: list[str] = []
        for item in items.values():
            all_tags.extend(item.get("tags") or [])
        meta = self.metadata_bulk(all_tags, profile_key)
        allowed_categories = {item["key"] for item in self.categories(profile_key)}
        def norm_fast(value: Any) -> str:
            raw = str(value or "unknown").strip().lower().replace(" ", "_")
            mapped = CATEGORY_ALIASES.get(raw, raw or "unknown")
            if mapped in allowed_categories:
                return mapped
            if mapped == "deprecated":
                return "invalid"
            return "custom" if mapped else "unknown"
        profile = self.get_profile(profile_key)
        rank = {cat: idx for idx, cat in enumerate(profile.get("precedence") or [])}
        prepared: dict[int, list[tuple[str, str]]] = {}
        for media_id, item in items.items():
            cleaned = _dedupe_clean(item.get("tags") or [])
            if not cleaned:
                continue
            strategy = (item.get("order_strategy") or order_strategy or "retain").replace("-", "_")
            ordered = list(cleaned)
            if strategy not in {"retain", "custom", "none", "source"}:
                ordered = [tag for _, tag in sorted(enumerate(cleaned), key=lambda pair: (rank.get(str(meta.get(pair[1], {}).get("category") or "unknown"), len(rank) + 1), pair[0]))]
            overrides = {normalize_tag(k): v for k, v in (item.get("categories") or {}).items() if normalize_tag(k)}
            pairs: list[tuple[str, str]] = []
            for tag in ordered:
                info = meta.get(tag) or {}
                if info.get("custom"):
                    category = norm_fast(info.get("category"))
                elif tag in overrides:
                    category = norm_fast(overrides[tag])
                else:
                    category = norm_fast(info.get("category") or "unknown")
                pairs.append((tag, category))
            prepared[int(media_id)] = pairs
        self.db.replace_tags_many(prepared, source=source)

    def metadata(self, tags: Iterable[str], profile_key: str | None = None) -> dict[str, dict[str, Any]]:
        return self.metadata_bulk(tags, profile_key)

    def order_tags(self, tags: Iterable[str], profile_key: str | None = None, strategy: str = "retain") -> list[str]:
        cleaned = _dedupe_clean(tags); strategy = (strategy or "retain").replace("-", "_")
        if strategy in {"retain", "custom", "none", "source"}: return cleaned
        if strategy == "lora_purpose": profile_key = "lora-purpose"
        profile = self.get_profile(profile_key); rank = {cat: idx for idx, cat in enumerate(profile.get("precedence") or [])}; meta = self.metadata_bulk(cleaned, profile.get("key"))
        return [tag for _, tag in sorted(enumerate(cleaned), key=lambda item: (rank.get(meta[item[1]]["category"], len(rank) + 1), item[0]))]

def _dedupe_clean(tags: Iterable[str]) -> list[str]:
    cleaned: list[str] = []; seen: set[str] = set()
    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized and normalized.lower() != "nan" and normalized not in seen:
            cleaned.append(normalized); seen.add(normalized)
    return cleaned

def _json_loads(value: Any, default: Any) -> Any:
    if value is None: return default
    if isinstance(value, (dict, list)): return value
    try: return json.loads(value)
    except Exception: return default

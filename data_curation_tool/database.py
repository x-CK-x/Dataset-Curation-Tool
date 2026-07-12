from __future__ import annotations

import json
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._runtime_recovery_used = False
        # A previous process can be killed while a very large tag export is being
        # imported. SQLite is normally robust, but unsafe PRAGMAs or multiple app
        # instances can leave a malformed database. Do an integrity check before
        # schema creation so the app can quarantine the broken file and start
        # cleanly instead of crashing at CREATE INDEX.
        self.recover_if_needed()
        try:
            self.initialize()
        except sqlite3.DatabaseError as exc:
            if self._is_corruption_error(exc):
                quarantine_dir = self._quarantine_corrupt_files(str(exc))
                print(f"[Data Curation Tool] Corrupt SQLite database was quarantined at: {quarantine_dir}")
                self.initialize()
            else:
                raise

    @staticmethod
    def _is_corruption_error(exc: BaseException) -> bool:
        text = str(exc).lower()
        return any(marker in text for marker in (
            "database disk image is malformed",
            "file is not a database",
            "database schema is corrupt",
            "malformed database schema",
        ))

    def _quarantine_corrupt_files(self, reason: str = "malformed") -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        quarantine_dir = self.path.parent / "corrupt_databases" / stamp
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        manifest = {"database": str(self.path), "reason": reason, "created_at": now_iso(), "moved": []}
        for candidate in (self.path, Path(f"{self.path}-wal"), Path(f"{self.path}-shm")):
            if candidate.exists():
                target = quarantine_dir / candidate.name
                try:
                    shutil.move(str(candidate), str(target))
                    manifest["moved"].append(str(target))
                except Exception as exc:  # keep recovery best-effort
                    manifest.setdefault("errors", []).append({"path": str(candidate), "error": str(exc)})
        (quarantine_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return quarantine_dir

    def recover_if_needed(self) -> None:
        if not self.path.exists():
            return
        try:
            conn = sqlite3.connect(self.path, timeout=30.0)
            try:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA busy_timeout=30000")
                # Use the full integrity check here.  It is slower than quick_check,
                # but it catches malformed index/table pages before startup DDL
                # touches those objects and crashes at CREATE INDEX.
                result = conn.execute("PRAGMA integrity_check").fetchone()
                status = str(result[0] if result else "")
                if status.lower() != "ok":
                    raise sqlite3.DatabaseError(f"SQLite integrity_check failed: {status}")
                try:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except sqlite3.DatabaseError:
                    pass
            finally:
                conn.close()
        except sqlite3.DatabaseError as exc:
            if self._is_corruption_error(exc) or "integrity_check failed" in str(exc) or "quick_check failed" in str(exc):
                quarantine_dir = self._quarantine_corrupt_files(str(exc))
                print(f"[Data Curation Tool] Corrupt SQLite database was quarantined at: {quarantine_dir}")
                return
            raise

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=60.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA wal_autocheckpoint=1000")
            conn.execute("PRAGMA temp_store=MEMORY")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._lock, self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    settings_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    ext TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    sha256 TEXT,
                    phash TEXT,
                    tag_path TEXT,
                    caption_path TEXT,
                    duplicate_of INTEGER REFERENCES media(id) ON DELETE SET NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(dataset_id, path)
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    source TEXT NOT NULL DEFAULT 'manual',
                    confidence REAL,
                    ordinal INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(media_id, tag)
                );

                CREATE TABLE IF NOT EXISTS captions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    caption TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'manual',
                    confidence REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(media_id)
                );

                CREATE TABLE IF NOT EXISTS tag_dictionary (
                    tag TEXT PRIMARY KEY,
                    category TEXT NOT NULL DEFAULT 'general',
                    post_count INTEGER NOT NULL DEFAULT 0,
                    aliases_json TEXT NOT NULL DEFAULT '[]',
                    implications_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS duplicates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                    media_a_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    media_b_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    reason TEXT NOT NULL,
                    distance INTEGER,
                    created_at TEXT NOT NULL,
                    UNIQUE(media_a_id, media_b_id, reason)
                );

                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(dataset_id, name)
                );

                CREATE TABLE IF NOT EXISTS group_items (
                    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(group_id, media_id)
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER REFERENCES media(id) ON DELETE CASCADE,
                    run_id INTEGER,
                    model_name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tag_prediction_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
                    run_id INTEGER,
                    model_name TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'tag',
                    tag TEXT NOT NULL,
                    score REAL NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(media_id, model_name, kind, tag)
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    message TEXT NOT NULL DEFAULT '',
                    params_json TEXT NOT NULL DEFAULT '{}',
                    result_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    source TEXT NOT NULL,
                    positive_tags_json TEXT NOT NULL DEFAULT '[]',
                    negative_tags_json TEXT NOT NULL DEFAULT '[]',
                    options_json TEXT NOT NULL DEFAULT '{}',
                    archived INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS download_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    preset_name TEXT,
                    status TEXT NOT NULL,
                    output_dir TEXT,
                    params_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS global_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sha256 TEXT NOT NULL UNIQUE,
                    path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    media_type TEXT NOT NULL DEFAULT 'unknown',
                    ext TEXT NOT NULL DEFAULT '',
                    width INTEGER,
                    height INTEGER,
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    phash TEXT,
                    original_filename TEXT,
                    source_site TEXT,
                    source_post_id TEXT,
                    source_url TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS global_asset_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    global_asset_id INTEGER NOT NULL REFERENCES global_assets(id) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    source TEXT NOT NULL DEFAULT 'manual',
                    ordinal INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(global_asset_id, tag, source)
                );

                CREATE TABLE IF NOT EXISTS global_asset_captions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    global_asset_id INTEGER NOT NULL REFERENCES global_assets(id) ON DELETE CASCADE,
                    caption TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'manual',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(global_asset_id, source)
                );

                CREATE TABLE IF NOT EXISTS global_asset_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    global_asset_id INTEGER NOT NULL REFERENCES global_assets(id) ON DELETE CASCADE,
                    source_site TEXT,
                    source_post_id TEXT,
                    source_url TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dataset_branches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    root_path TEXT NOT NULL,
                    purpose TEXT NOT NULL DEFAULT '',
                    settings_json TEXT NOT NULL DEFAULT '{}',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dataset_branch_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    branch_id INTEGER NOT NULL REFERENCES dataset_branches(id) ON DELETE CASCADE,
                    global_asset_id INTEGER NOT NULL REFERENCES global_assets(id) ON DELETE CASCADE,
                    include INTEGER NOT NULL DEFAULT 1,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    role TEXT NOT NULL DEFAULT 'original',
                    media_path TEXT,
                    tag_path TEXT,
                    caption_path TEXT,
                    item_config_json TEXT NOT NULL DEFAULT '{}',
                    ordinal INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(branch_id, global_asset_id, role, media_path)
                );

                CREATE TABLE IF NOT EXISTS global_asset_variants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    global_asset_id INTEGER NOT NULL REFERENCES global_assets(id) ON DELETE CASCADE,
                    branch_id INTEGER REFERENCES dataset_branches(id) ON DELETE SET NULL,
                    branch_item_id INTEGER REFERENCES dataset_branch_items(id) ON DELETE SET NULL,
                    variant_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    variant_sha256 TEXT,
                    variant_kind TEXT NOT NULL DEFAULT 'augmentation',
                    transform_json TEXT NOT NULL DEFAULT '{}',
                    tag_path TEXT,
                    caption_path TEXT,
                    media_type TEXT NOT NULL DEFAULT 'unknown',
                    ext TEXT NOT NULL DEFAULT '',
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(global_asset_id, branch_id, variant_path)
                );

                CREATE INDEX IF NOT EXISTS idx_media_dataset ON media(dataset_id);
                CREATE INDEX IF NOT EXISTS idx_media_sha ON media(sha256);
                CREATE INDEX IF NOT EXISTS idx_media_phash ON media(phash);
                CREATE INDEX IF NOT EXISTS idx_tags_media ON tags(media_id);
                CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
                CREATE INDEX IF NOT EXISTS idx_predictions_media ON predictions(media_id);
                CREATE INDEX IF NOT EXISTS idx_tag_prediction_scores_media_tag ON tag_prediction_scores(media_id, tag);
                CREATE INDEX IF NOT EXISTS idx_tag_prediction_scores_model ON tag_prediction_scores(model_name, kind);
                CREATE INDEX IF NOT EXISTS idx_global_assets_sha ON global_assets(sha256);
                CREATE INDEX IF NOT EXISTS idx_global_assets_source ON global_assets(source_site, source_post_id);
                CREATE INDEX IF NOT EXISTS idx_global_asset_tags_tag ON global_asset_tags(tag);
                CREATE INDEX IF NOT EXISTS idx_global_asset_tags_asset ON global_asset_tags(global_asset_id);
                CREATE INDEX IF NOT EXISTS idx_global_asset_sources_lookup ON global_asset_sources(source_site, source_post_id, source_url);
                CREATE INDEX IF NOT EXISTS idx_dataset_branch_items_branch ON dataset_branch_items(branch_id);
                CREATE INDEX IF NOT EXISTS idx_dataset_branch_items_asset ON dataset_branch_items(global_asset_id);
                CREATE INDEX IF NOT EXISTS idx_global_asset_variants_asset ON global_asset_variants(global_asset_id);
                CREATE INDEX IF NOT EXISTS idx_global_asset_variants_branch ON global_asset_variants(branch_id);
                """
            )

    def _recover_after_runtime_corruption(self, exc: BaseException) -> bool:
        if self._runtime_recovery_used or not self._is_corruption_error(exc):
            return False
        self._runtime_recovery_used = True
        quarantine_dir = self._quarantine_corrupt_files(str(exc))
        print(f"[Data Curation Tool] Runtime SQLite corruption was quarantined at: {quarantine_dir}")
        self.initialize()
        return True

    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        try:
            with self._lock, self.connect() as conn:
                cur = conn.execute(sql, tuple(params))
                return int(cur.lastrowid or 0)
        except sqlite3.DatabaseError as exc:
            if self._recover_after_runtime_corruption(exc):
                with self._lock, self.connect() as conn:
                    cur = conn.execute(sql, tuple(params))
                    return int(cur.lastrowid or 0)
            raise

    def executemany(self, sql: str, params: Iterable[Iterable[Any]]) -> None:
        cached = list(params)
        try:
            with self._lock, self.connect() as conn:
                conn.executemany(sql, cached)
        except sqlite3.DatabaseError as exc:
            if self._recover_after_runtime_corruption(exc):
                with self._lock, self.connect() as conn:
                    conn.executemany(sql, cached)
                return
            raise

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        try:
            with self._lock, self.connect() as conn:
                cur = conn.execute(sql, tuple(params))
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.DatabaseError as exc:
            if self._recover_after_runtime_corruption(exc):
                with self._lock, self.connect() as conn:
                    cur = conn.execute(sql, tuple(params))
                    return [dict(row) for row in cur.fetchall()]
            raise

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def insert_dataset(self, name: str, root_path: str, settings: dict[str, Any] | None = None) -> int:
        return self.execute(
            "INSERT INTO datasets(name, root_path, settings_json, created_at) VALUES (?, ?, ?, ?)",
            (name, root_path, json.dumps(settings or {}), now_iso()),
        )

    def upsert_media(self, payload: dict[str, Any]) -> int:
        with self._lock, self.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM media WHERE dataset_id=? AND path=?",
                (payload["dataset_id"], payload["path"]),
            ).fetchone()
            now = now_iso()
            if existing:
                media_id = int(existing["id"])
                conn.execute(
                    """
                    UPDATE media SET relative_path=?, media_type=?, ext=?, width=?, height=?, size_bytes=?,
                        sha256=?, phash=?, tag_path=?, caption_path=?, duplicate_of=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        payload.get("relative_path", ""),
                        payload.get("media_type", "unknown"),
                        payload.get("ext", ""),
                        payload.get("width"),
                        payload.get("height"),
                        payload.get("size_bytes", 0),
                        payload.get("sha256"),
                        payload.get("phash"),
                        payload.get("tag_path"),
                        payload.get("caption_path"),
                        payload.get("duplicate_of"),
                        now,
                        media_id,
                    ),
                )
                return media_id
            cur = conn.execute(
                """
                INSERT INTO media(dataset_id, path, relative_path, media_type, ext, width, height, size_bytes,
                                  sha256, phash, tag_path, caption_path, duplicate_of, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    payload["dataset_id"],
                    payload["path"],
                    payload.get("relative_path", ""),
                    payload.get("media_type", "unknown"),
                    payload.get("ext", ""),
                    payload.get("width"),
                    payload.get("height"),
                    payload.get("size_bytes", 0),
                    payload.get("sha256"),
                    payload.get("phash"),
                    payload.get("tag_path"),
                    payload.get("caption_path"),
                    payload.get("duplicate_of"),
                    now,
                    now,
                ),
            )
            return int(cur.lastrowid)


    def bulk_upsert_media(self, payloads: list[dict[str, Any]]) -> list[int]:
        """Insert/update many media rows in one SQLite transaction and return IDs.

        Importing one file at a time previously opened and committed one SQLite
        connection per media item.  For large datasets that dominates import time.
        This keeps the exact same upsert semantics but amortizes the transaction
        and WAL sync cost across an import batch.
        """
        if not payloads:
            return []
        ids: list[int] = []
        now = now_iso()
        with self._lock, self.connect() as conn:
            for payload in payloads:
                row = conn.execute(
                    "SELECT id FROM media WHERE dataset_id=? AND path=?",
                    (payload["dataset_id"], payload["path"]),
                ).fetchone()
                if row:
                    media_id = int(row["id"])
                    conn.execute(
                        """
                        UPDATE media SET relative_path=?, media_type=?, ext=?, width=?, height=?, size_bytes=?,
                            sha256=?, phash=?, tag_path=?, caption_path=?, duplicate_of=?, updated_at=?
                        WHERE id=?
                        """,
                        (
                            payload.get("relative_path", ""),
                            payload.get("media_type", "unknown"),
                            payload.get("ext", ""),
                            payload.get("width"),
                            payload.get("height"),
                            payload.get("size_bytes", 0),
                            payload.get("sha256"),
                            payload.get("phash"),
                            payload.get("tag_path"),
                            payload.get("caption_path"),
                            payload.get("duplicate_of"),
                            now,
                            media_id,
                        ),
                    )
                else:
                    cur = conn.execute(
                        """
                        INSERT INTO media(dataset_id, path, relative_path, media_type, ext, width, height, size_bytes,
                                          sha256, phash, tag_path, caption_path, duplicate_of, active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        """,
                        (
                            payload["dataset_id"],
                            payload["path"],
                            payload.get("relative_path", ""),
                            payload.get("media_type", "unknown"),
                            payload.get("ext", ""),
                            payload.get("width"),
                            payload.get("height"),
                            payload.get("size_bytes", 0),
                            payload.get("sha256"),
                            payload.get("phash"),
                            payload.get("tag_path"),
                            payload.get("caption_path"),
                            payload.get("duplicate_of"),
                            now,
                            now,
                        ),
                    )
                    media_id = int(cur.lastrowid)
                ids.append(media_id)
        return ids

    def replace_tags(self, media_id: int, tags: list[tuple[str, str]], source: str = "manual") -> None:
        with self._lock, self.connect() as conn:
            conn.execute("DELETE FROM tags WHERE media_id=?", (media_id,))
            now = now_iso()
            conn.executemany(
                """
                INSERT OR IGNORE INTO tags(media_id, tag, category, source, confidence, ordinal, created_at)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                """,
                [(media_id, tag, category, source, idx, now) for idx, (tag, category) in enumerate(tags)],
            )


    def replace_tags_many(self, items: dict[int, list[tuple[str, str]]], source: str = "manual") -> None:
        """Replace tags for many media rows in one transaction."""
        if not items:
            return
        now = now_iso()
        media_ids = [int(mid) for mid in items.keys()]
        with self._lock, self.connect() as conn:
            for start in range(0, len(media_ids), 900):
                chunk = media_ids[start:start + 900]
                placeholders = ",".join("?" for _ in chunk)
                conn.execute(f"DELETE FROM tags WHERE media_id IN ({placeholders})", chunk)
            rows: list[tuple[Any, ...]] = []
            for media_id, tags in items.items():
                for idx, (tag, category) in enumerate(tags):
                    rows.append((int(media_id), tag, category, source, idx, now))
            conn.executemany(
                """
                INSERT OR IGNORE INTO tags(media_id, tag, category, source, confidence, ordinal, created_at)
                VALUES (?, ?, ?, ?, NULL, ?, ?)
                """,
                rows,
            )

    def upsert_captions_many(self, captions: dict[int, tuple[str, str]]) -> None:
        """Upsert captions for many media rows in one transaction."""
        if not captions:
            return
        now = now_iso()
        rows = [(int(media_id), caption, source, None, now, now) for media_id, (caption, source) in captions.items() if caption]
        if not rows:
            return
        with self._lock, self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO captions(media_id, caption, source, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(media_id) DO UPDATE SET caption=excluded.caption, source=excluded.source,
                    confidence=excluded.confidence, updated_at=excluded.updated_at
                """,
                rows,
            )

    def upsert_caption(self, media_id: int, caption: str, source: str = "manual", confidence: float | None = None) -> None:
        now = now_iso()
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO captions(media_id, caption, source, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(media_id) DO UPDATE SET caption=excluded.caption, source=excluded.source,
                    confidence=excluded.confidence, updated_at=excluded.updated_at
                """,
                (media_id, caption, source, confidence, now, now),
            )

    def create_job(self, job_type: str, params: dict[str, Any] | None = None) -> int:
        now = now_iso()
        return self.execute(
            """
            INSERT INTO jobs(type, status, progress, message, params_json, created_at, updated_at)
            VALUES (?, 'queued', 0, '', ?, ?, ?)
            """,
            (job_type, json.dumps(params or {}), now, now),
        )

    def update_job(
        self,
        job_id: int,
        *,
        status: str | None = None,
        progress: float | None = None,
        message: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        finished: bool = False,
    ) -> None:
        current = self.query_one("SELECT * FROM jobs WHERE id=?", (job_id,))
        if not current:
            return
        fields = {
            "status": status if status is not None else current["status"],
            "progress": progress if progress is not None else current["progress"],
            "message": message if message is not None else current["message"],
            "result_json": json.dumps(result) if result is not None else current["result_json"],
            "error": error if error is not None else current["error"],
            "updated_at": now_iso(),
            "finished_at": now_iso() if finished else current["finished_at"],
        }
        self.execute(
            """
            UPDATE jobs SET status=?, progress=?, message=?, result_json=?, error=?, updated_at=?, finished_at=?
            WHERE id=?
            """,
            (
                fields["status"],
                fields["progress"],
                fields["message"],
                fields["result_json"],
                fields["error"],
                fields["updated_at"],
                fields["finished_at"],
                job_id,
            ),
        )

    def set_setting(self, key: str, value: Any) -> None:
        now = now_iso()
        self.execute(
            """
            INSERT INTO settings(key, value_json, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at
            """,
            (key, json.dumps(value), now),
        )

    def get_setting(self, key: str, default: Any = None) -> Any:
        row = self.query_one("SELECT value_json FROM settings WHERE key=?", (key,))
        if not row:
            return default
        try:
            return json.loads(row["value_json"])
        except Exception:
            return default

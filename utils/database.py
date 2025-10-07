import sqlite3
import os
import threading
from datetime import datetime
import hashlib
import json

import time

import shutil
from typing import Any, Dict, List, Optional

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True) if os.path.dirname(db_path) else None
        # allow access from different threads
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self.create_tables()

    def create_tables(self):
        """Create the necessary tables if they don't already exist."""
        with self.lock:
            cur = self.conn.cursor()
            # websites that data can be downloaded from
            cur.execute(
                """CREATE TABLE IF NOT EXISTS websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    base_url TEXT,
                    config_json TEXT,
                    created_at TEXT
                )"""
            )
            # global unique images tracked by hash
            cur.execute(
                """CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE,
                    file_path TEXT,
                    added_at TEXT
                )"""
            )
            # configs table stores path and json for readability
            cur.execute(
                """CREATE TABLE IF NOT EXISTS configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT,
                    json TEXT,
                    created_at TEXT
                )"""
            )
            # store individual config key/value pairs for readability
            cur.execute(
                """CREATE TABLE IF NOT EXISTS config_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER,
                    key TEXT,
                    value TEXT,
                    FOREIGN KEY(config_id) REFERENCES configs(id)
                )"""
            )
            # main download records
            cur.execute(
                """CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    website TEXT,
                    config_id INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    downloaded_count INTEGER DEFAULT 0,
                    has_new INTEGER DEFAULT 0,
                    new_available INTEGER DEFAULT 0,
                    FOREIGN KEY(config_id) REFERENCES configs(id)
                )"""
            )
            # individual files belonging to a download record
            cur.execute(
                """CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    download_id INTEGER,
                    image_id INTEGER,
                    post_tags TEXT,
                    post_created_at TEXT,
                    downloaded_at TEXT,
                    cdn_url TEXT,
                    local_path TEXT,
                    tag_local_path TEXT,
                    tag_cdn_url TEXT,
                    FOREIGN KEY(download_id) REFERENCES downloads(id),
                    FOREIGN KEY(image_id) REFERENCES images(id)
                )"""
            )
            # table to track user modified copies of downloaded files
            cur.execute(
                """CREATE TABLE IF NOT EXISTS modified_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    mod_image_path TEXT,
                    mod_tag_path TEXT,
                    modified_at TEXT,
                    FOREIGN KEY(file_id) REFERENCES files(id)
                )"""
            )
            # optional table to track duplicates
            cur.execute(
                """CREATE TABLE IF NOT EXISTS duplicates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER,
                    duplicate_of INTEGER,
                    reason TEXT,
                    FOREIGN KEY(file_id) REFERENCES files(id),
                    FOREIGN KEY(duplicate_of) REFERENCES files(id)
                )"""
            )
            cur.execute(
                """CREATE TABLE IF NOT EXISTS preset_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preset_path TEXT UNIQUE,
                    preset_name TEXT,
                    last_scan_at TEXT,
                    last_download_at TEXT,
                    media_file_count INTEGER DEFAULT 0,
                    media_file_types TEXT,
                    has_media INTEGER DEFAULT 0,
                    download_record_count INTEGER DEFAULT 0,
                    total_files_downloaded INTEGER DEFAULT 0,
                    new_media_available INTEGER DEFAULT 0,
                    extra_metadata TEXT
                )"""
            )

            cur.execute("PRAGMA table_info(downloads)")
            download_columns = [row[1] for row in cur.fetchall()]
            if "config_path" not in download_columns:
                cur.execute("ALTER TABLE downloads ADD COLUMN config_path TEXT")
            if "preset_name" not in download_columns:
                cur.execute("ALTER TABLE downloads ADD COLUMN preset_name TEXT")
            if "last_completed_at" not in download_columns:
                cur.execute("ALTER TABLE downloads ADD COLUMN last_completed_at TEXT")
            if "total_files" not in download_columns:
                cur.execute("ALTER TABLE downloads ADD COLUMN total_files INTEGER DEFAULT 0")
            self.conn.commit()

    def add_config(self, json_content=None, path=None):
        """Insert a new config and return its id.

        If no path is supplied, the JSON is written to a file in
        ``data/configs`` and that path stored.  The table is expanded with
        columns matching the JSON keys so values can be queried directly.
        """
        now = datetime.utcnow().isoformat()
        data = None
        if json_content:
            data = json.loads(json_content) if isinstance(json_content, str) else json_content
        if path is None and data is not None:
            config_dir = os.path.join(os.getcwd(), "data", "configs")
            os.makedirs(config_dir, exist_ok=True)
            fname = f"config_{int(time.time()*1000)}.json"
            path = os.path.join(config_dir, fname)
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(data, indent=2))

        with self.lock:
            cur = self.conn.cursor()
            if data:
                cur.execute("PRAGMA table_info(configs)")
                existing = [r[1] for r in cur.fetchall()]
                for k in data.keys():
                    if k not in existing:
                        cur.execute(f"ALTER TABLE configs ADD COLUMN {k} TEXT")
            columns = ["path", "json", "created_at"]
            values = [path, json.dumps(data) if data is not None else None, now]
            if data:
                for k in data.keys():
                    columns.append(k)
                    v = data[k]
                    values.append(json.dumps(v) if isinstance(v, (dict, list)) else str(v))
            placeholders = ",".join(["?"] * len(columns))
            cur.execute(
                f"INSERT INTO configs ({','.join(columns)}) VALUES ({placeholders})",
                values,
            )
            config_id = cur.lastrowid
            if data:
                for k, v in data.items():
                    cur.execute(
                        "INSERT INTO config_entries (config_id, key, value) VALUES (?, ?, ?)",
                        (config_id, k, json.dumps(v) if isinstance(v, (dict, list)) else str(v)),
                    )
            self.conn.commit()
            return config_id

    def add_download_record(
        self,
        website,
        config_json=None,
        config_path=None,
        preset_name=None,
    ):
        """Create a new download entry."""
        now = datetime.utcnow().isoformat()
        config_id = None
        stored_path = config_path
        if config_json is not None or config_path is not None:
            config_id = self.add_config(config_json, config_path)
            if stored_path is None and config_id is not None:
                stored_path = self.get_config_path(config_id)
        normalized_path = os.path.abspath(stored_path) if stored_path else None
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                INSERT INTO downloads (
                    website,
                    config_id,
                    config_path,
                    preset_name,
                    created_at,
                    updated_at,
                    last_completed_at,
                    total_files
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (website, config_id, normalized_path, preset_name, now, now, None, 0),
            )
            self.conn.commit()
            return cur.lastrowid

    def add_website(self, name, base_url=None, config_json=None):
        """Insert a new website configuration or return existing id."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT id FROM websites WHERE name=?",
                (name,),
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                "INSERT INTO websites (name, base_url, config_json, created_at) VALUES (?, ?, ?, ?)",
                (name, base_url, config_json, datetime.utcnow().isoformat()),
            )
            self.conn.commit()
            return cur.lastrowid

    def get_websites(self):
        """Return list of known websites."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id, name FROM websites")
            rows = cur.fetchall()
            return rows

    def get_latest_config(self):
        """Return the most recently added config as a dictionary or None."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT json FROM configs ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            cur.close()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except Exception:
                return None
        return None

    def list_config_options(self):
        """Return dropdown options and mapping from name to path for configs."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id, path FROM configs ORDER BY id")
            rows = cur.fetchall()
            cur.close()
        options = []
        mapping = {}
        for cid, path in rows:
            name = os.path.basename(path) if path else f"config_{cid}.json"
            options.append(name)
            mapping[name] = path
        return options, mapping

    def get_config_path(self, config_id: Optional[int]):
        """Return the filesystem path for a stored config id."""

        if not config_id:
            return None
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT path FROM configs WHERE id=?", (config_id,))
            row = cur.fetchone()
            cur.close()
        if row:
            return row[0]
        return None

    def remove_config_by_path(self, path):
        """Remove config rows matching the provided path."""
        if not path:
            return
        normalized = os.path.abspath(path)
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id, path FROM configs")
            rows = cur.fetchall()
            ids_to_remove = [cid for cid, row_path in rows if row_path and os.path.abspath(row_path) == normalized]
            if not ids_to_remove:
                return
            for cid in ids_to_remove:
                cur.execute("DELETE FROM config_entries WHERE config_id=?", (cid,))
                cur.execute("UPDATE downloads SET config_id=NULL WHERE config_id=?", (cid,))
                cur.execute("DELETE FROM configs WHERE id=?", (cid,))
            self.conn.commit()

    def summarize_preset_downloads(
        self,
        preset_path: str,
        preset_name: Optional[str] = None,
        fallback_last_download: Optional[str] = None,
        file_count: int = 0,
        file_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Aggregate database stats for the given preset path.

        Returns a dictionary describing download totals and updates the
        ``preset_stats`` table so historical information is persisted.
        """

        if not preset_path:
            return {}

        normalized = os.path.abspath(preset_path)
        scan_time = datetime.utcnow().isoformat()
        last_download_at = fallback_last_download
        media_types = sorted(set(file_types or []))

        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                """
                SELECT id, updated_at, downloaded_count, has_new, new_available, total_files, last_completed_at
                FROM downloads
                WHERE config_path=?
                """,
                (normalized,),
            )
            rows = cur.fetchall()
            download_ids = [row[0] for row in rows]
            total_files_db = 0
            new_media_available = 0
            for row in rows:
                _, updated_at, downloaded_count, has_new, new_available, total_files, last_completed = row
                total_files_db = max(
                    total_files_db,
                    downloaded_count or 0,
                    total_files or 0,
                )
                if has_new or new_available:
                    new_media_available = 1
                for candidate in (last_completed, updated_at):
                    if candidate and (not last_download_at or candidate > last_download_at):
                        last_download_at = candidate

            if download_ids:
                placeholders = ",".join(["?"] * len(download_ids))
                cur.execute(
                    f"SELECT COUNT(*), MAX(downloaded_at) FROM files WHERE download_id IN ({placeholders})",
                    download_ids,
                )
                result = cur.fetchone()
                if result:
                    file_total, file_last = result
                    if file_total and file_total > total_files_db:
                        total_files_db = file_total
                    if file_last and (not last_download_at or file_last > last_download_at):
                        last_download_at = file_last
            total_files = max(total_files_db, file_count)
            has_media_flag = 1 if total_files > 0 else 0
            extra_metadata = json.dumps({
                "download_ids": download_ids,
                "db_file_total": total_files_db,
            })
            cur.execute(
                """
                INSERT INTO preset_stats (
                    preset_path,
                    preset_name,
                    last_scan_at,
                    last_download_at,
                    media_file_count,
                    media_file_types,
                    has_media,
                    download_record_count,
                    total_files_downloaded,
                    new_media_available,
                    extra_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(preset_path) DO UPDATE SET
                    preset_name=excluded.preset_name,
                    last_scan_at=excluded.last_scan_at,
                    last_download_at=COALESCE(excluded.last_download_at, preset_stats.last_download_at),
                    media_file_count=excluded.media_file_count,
                    media_file_types=excluded.media_file_types,
                    has_media=excluded.has_media,
                    download_record_count=excluded.download_record_count,
                    total_files_downloaded=excluded.total_files_downloaded,
                    new_media_available=excluded.new_media_available,
                    extra_metadata=excluded.extra_metadata
                """,
                (
                    normalized,
                    preset_name,
                    scan_time,
                    last_download_at,
                    file_count,
                    json.dumps(media_types) if media_types else None,
                    has_media_flag,
                    len(download_ids),
                    total_files,
                    new_media_available,
                    extra_metadata,
                ),
            )
            self.conn.commit()

        return {
            "download_ids": download_ids,
            "last_download_at": last_download_at,
            "total_files_downloaded": total_files,
            "new_media_available": new_media_available,
            "media_file_count": file_count,
        }

    def _compute_hash(self, file_path):
        """Return SHA1 hash for the given file."""
        h = hashlib.sha1()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
        except FileNotFoundError:
            return None
        return h.hexdigest()

    def add_image(self, file_path):
        """Insert image hash if not already present and return image_id."""
        img_hash = self._compute_hash(file_path)
        if img_hash is None:
            return None
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM images WHERE hash=?", (img_hash,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                "INSERT INTO images (hash, file_path, added_at) VALUES (?, ?, ?)",
                (img_hash, file_path, datetime.utcnow().isoformat()),
            )
            self.conn.commit()
            return cur.lastrowid

    def add_file(self, download_id, post_tags, post_created_at, downloaded_at, cdn_url, local_path, tag_local_path, tag_cdn_url):
        """Record a file that was downloaded as part of a download entry.
        Deduplicates based on image hash."""
        image_id = self.add_image(local_path)
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO files (download_id, image_id, post_tags, post_created_at, downloaded_at, cdn_url, local_path, tag_local_path, tag_cdn_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (download_id, image_id, post_tags, post_created_at, downloaded_at, cdn_url, local_path, tag_local_path, tag_cdn_url),
            )
            file_id = cur.lastrowid
            # check for duplicates
            if image_id is not None:
                cur.execute(
                    "SELECT id FROM files WHERE image_id=? AND id<>?", (image_id, file_id)
                )
                dup = cur.fetchone()
                if dup:
                    self.mark_duplicate(file_id, dup[0], reason="hash")
            self.conn.commit()


    def mark_duplicate(self, file_id, duplicate_of, reason=""):
        """Record that one file is a duplicate of another."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO duplicates (file_id, duplicate_of, reason) VALUES (?, ?, ?)",
                (file_id, duplicate_of, reason),
            )
            self.conn.commit()

    def get_file_id(self, local_path):
        """Return the database id for a file path or ``None`` if not found."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM files WHERE local_path=?", (local_path,))
            row = cur.fetchone()
            cur.close()
        return row[0] if row else None

    def add_modified_file(self, file_id, mod_image_path=None, mod_tag_path=None):
        """Record an edited copy of a downloaded file."""
        now = datetime.utcnow().isoformat()
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO modified_files (file_id, mod_image_path, mod_tag_path, modified_at) VALUES (?, ?, ?, ?)",
                (file_id, mod_image_path, mod_tag_path, now),
            )
            self.conn.commit()
            return cur.lastrowid

    def merge_database(self, other_path):
        """Merge another dataset_curation.db into this one."""
        if not os.path.exists(other_path):
            return
        other = sqlite3.connect(other_path)
        other.row_factory = sqlite3.Row
        with other:
            oc = other.cursor()
            oc.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in oc.fetchall()]
            # merge websites
            if "websites" in tables:
                for row in oc.execute("SELECT name, base_url, config_json FROM websites"):
                    self.add_website(row[0], row[1], row[2])
            # merge configs
            config_map = {}
            if "configs" in tables:
                for row in oc.execute("SELECT * FROM configs"):
                    new_id = self.add_config(row["json"], row["path"])
                    config_map[row["id"]] = new_id
            # merge downloads and files
            download_map = {}
            if "downloads" in tables:
                for row in oc.execute("SELECT * FROM downloads"):
                    cfg_id = config_map.get(row["config_id"]) if "config_id" in row.keys() else None
                    # backward compatibility: older db may store config_json
                    if cfg_id is None and "config_json" in row.keys() and row["config_json"]:
                        cfg_id = self.add_config(row["config_json"], None)
                    new_id = self.add_download_record(row["website"], None, None)
                    # update to set config
                    with self.lock:
                        cur2 = self.conn.cursor()
                        cur2.execute(
                            "UPDATE downloads SET config_id=? WHERE id=?",
                            (cfg_id, new_id),
                        )
                        self.conn.commit()
                    download_map[row["id"]] = new_id
            if "files" in tables:
                for row in oc.execute("SELECT * FROM files"):
                    did = download_map.get(row["download_id"]) if download_map else None
                    self.add_file(
                        did or row["download_id"],
                        row["post_tags"],
                        row["post_created_at"],
                        row["downloaded_at"],
                        row["cdn_url"],
                        row["local_path"],
                        row["tag_local_path"],
                        row["tag_cdn_url"],
                    )
        other.close()

    def run_query(self, query, params=None):
        """Execute an arbitrary SQL query and return the results.

        Parameters
        ----------
        query: str
            Any valid SQL statement. SELECT queries return rows while
            modification queries commit changes.
        """
        with self.lock:
            cur = self.conn.cursor()
            try:
                if params is None:
                    cur.execute(query)
                else:
                    cur.execute(query, params)
                if query.strip().lower().startswith("select"):
                    rows = cur.fetchall()
                    headers = [description[0] for description in cur.description]
                    return headers, rows
                else:
                    self.conn.commit()
                    return [], []
            finally:
                cur.close()

    def get_table_names(self):
        """Return list of table names in the database."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            rows = [r[0] for r in cur.fetchall()]
            return rows

    def fetch_table(self, table_name, limit=None):
        """Return contents of a table.

        Parameters
        ----------
        table_name : str
            Name of the table to fetch.
        limit : int or None, optional
            Maximum number of rows to return. ``None`` returns all rows.
        """
        with self.lock:
            cur = self.conn.cursor()
            if limit is None:
                query = f"SELECT * FROM {table_name}"
                cur.execute(query)
            else:
                try:
                    lim = int(limit)
                except (TypeError, ValueError):
                    raise ValueError("limit must be an integer or None")
                query = f"SELECT * FROM {table_name} LIMIT {lim}"
                cur.execute(query)
            rows = cur.fetchall()
            headers = [description[0] for description in cur.description]
            return headers, rows

    def search_files(self, required_tags, blacklist_tags):
        """Search files containing required tags and not containing blacklist."""
        conditions = []
        params = []
        for tag in required_tags:
            conditions.append("post_tags LIKE ?")
            params.append(f"%{tag}%")
        for tag in blacklist_tags:
            conditions.append("post_tags NOT LIKE ?")
            params.append(f"%{tag}%")
        where = " AND ".join(conditions) if conditions else "1"
        query = f"SELECT * FROM files WHERE {where}"
        return self.run_query(query, params)

    def count_rows(self, table_name):
        """Return the number of rows in a table."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            result = cur.fetchone()
            return result[0] if result else 0

    def copy_files_from_table(self, table_name, dest_dir):
        """Copy images referenced in a table to dest_dir."""
        os.makedirs(dest_dir, exist_ok=True)
        headers, rows = self.fetch_table(table_name, limit=1000000)
        if "local_path" not in headers:
            return 0
        idx = headers.index("local_path")
        count = 0
        for row in rows:
            src = row[idx]
            if src and os.path.isfile(src):
                fname = os.path.basename(src)
                dst = os.path.join(dest_dir, fname)
                try:
                    shutil.copy2(src, dst)
                    count += 1
                except Exception:
                    pass
        return count

    def close(self):
        with self.lock:
            self.conn.close()

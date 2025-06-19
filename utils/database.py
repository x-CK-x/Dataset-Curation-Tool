import sqlite3
import os
import threading
from datetime import datetime
import hashlib
import json

import time

import shutil

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

    def add_download_record(self, website, config_json=None, config_path=None):
        """Create a new download entry."""
        now = datetime.utcnow().isoformat()
        config_id = None
        if config_json is not None or config_path is not None:
            config_id = self.add_config(config_json, config_path)
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO downloads (website, config_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (website, config_id, now, now),
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

    def fetch_table(self, table_name, limit=100):
        """Return contents of a table."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
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

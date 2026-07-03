from __future__ import annotations

import csv
import gzip
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def _serve_directory(root: Path):
    class Handler(_QuietHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_v516_pyarrow_download_import_categories_aliases_implications_and_artists(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "0")
    import data_curation_tool.services.tag_service as tag_module
    monkeypatch.setitem(tag_module.MIN_EXPECTED_TAG_ROWS, "e621", 100_000)
    monkeypatch.setitem(tag_module.MIN_CANONICAL_TAG_ROWS, "e621", 100_000)
    total_rows = 125_000
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    export_root = tmp_path / "mirror" / "db_exports"
    export_root.mkdir(parents=True)
    tags_path = export_root / f"tags-{stamp}.csv.gz"
    aliases_path = export_root / f"tag_aliases-{stamp}.csv.gz"
    implications_path = export_root / f"tag_implications-{stamp}.csv.gz"
    artists_path = export_root / f"artists-{stamp}.csv.gz"

    with gzip.open(tags_path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "category", "post_count"])
        for i in range(total_rows):
            # Exercise the user-provided numeric category mapping, including
            # category 2 => rating and category 4 => character.
            category = [0, 1, 2, 3, 4, 5, 6, 7, 8][i % 9]
            writer.writerow([i + 1, f"pyarrow_tag_{i:06d}", category, i % 10000])

    with gzip.open(aliases_path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "antecedent_name", "consequent_name", "created_at", "status"])
        writer.writerow([1, "old_pyarrow_alias", "pyarrow_tag_000001", stamp, "active"])
        writer.writerow([2, "rejected_alias", "pyarrow_tag_000002", stamp, "deleted"])

    with gzip.open(implications_path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "antecedent_name", "consequent_name", "created_at", "status"])
        writer.writerow([1, "pyarrow_tag_000004", "pyarrow_tag_000005", stamp, "active"])

    with gzip.open(artists_path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "other_names", "group_name", "linked_user_id", "is_active", "is_locked", "creator_id", "created_at", "updated_at", "urls"])
        writer.writerow([1, "artist_main", "{artist_alias_one,artist_alias_two}", "", "", "true", "false", "", stamp, stamp, ""])
        writer.writerow([2, "inactive_artist", "{inactive_alias}", "", "", "false", "false", "", stamp, stamp, ""])

    (export_root / "index.html").write_text("\n".join([tags_path.name, aliases_path.name, implications_path.name, artists_path.name]), encoding="utf-8")

    with gzip.open(tags_path, "rt", encoding="utf-8", newline="") as f:
        assert sum(1 for _ in csv.DictReader(f)) == total_rows

    server = _serve_directory(tmp_path / "mirror")
    try:
        paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
        db = Database(paths.database)
        tags = TagService(db, paths)
        result = tags.import_default_exports(
            "e621",
            url=f"http://127.0.0.1:{server.server_port}/db_exports/",
            cache_hours=0,
            replace_existing=True,
        )
    finally:
        server.shutdown()
        server.server_close()

    status = tags.dictionary_status("e621")
    assert status["total"] >= total_rows
    assert status["total"] > 100_000
    assert status["incomplete"] is False
    assert result["status"]["total"] == status["total"]

    by_category = {row["category"]: row["n"] for row in status["by_category"]}
    assert int(by_category.get("rating", 0)) > 0
    assert int(by_category.get("character", 0)) > 0
    assert int(by_category.get("invalid", 0)) > 0

    meta = tags.metadata_bulk(["old_pyarrow_alias", "artist_alias_one", "rejected_alias"], "e621")
    assert meta["old_pyarrow_alias"]["alias_target"] == "pyarrow_tag_000001"
    assert meta["artist_alias_one"]["alias_target"] == "artist_main"
    assert meta["artist_alias_one"]["category"] == "artist"
    assert meta["rejected_alias"]["known"] is False

    artist_alias_rows = db.query("SELECT artist_name, alias FROM artist_aliases WHERE source='e621' ORDER BY alias")
    assert {row["alias"] for row in artist_alias_rows} == {"artist_alias_one", "artist_alias_two"}

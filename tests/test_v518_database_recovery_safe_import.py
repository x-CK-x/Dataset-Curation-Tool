from __future__ import annotations

import gzip
import csv
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def _write_tags_gz(path: Path, rows: int = 5_000) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "category", "post_count"])
        for i in range(rows):
            writer.writerow([i, f"tag_{i:06d}", i % 9, i])


def test_database_quarantines_malformed_file_and_restarts(tmp_path: Path):
    db_path = tmp_path / "runtime" / "app.db"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"this is not sqlite at all")
    db = Database(db_path)
    row = db.query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
    assert row and row["name"] == "settings"
    quarantines = list((db_path.parent / "corrupt_databases").glob("*/app.db"))
    assert quarantines
    assert quarantines[0].read_bytes() == b"this is not sqlite at all"


def test_verified_tag_import_stages_then_promotes_large_dictionary(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DCT_DISABLE_PYARROW_TAG_IMPORT", "1")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db, paths)
    export_path = tmp_path / "tags.csv.gz"
    _write_tags_gz(export_path, 5_000)
    count = tags.verified_import_dictionary_csv(export_path, "e621", replace_existing=True, min_expected=1_000)
    assert count == 5_000
    status = tags.dictionary_status("e621")
    assert status["total"] >= 5_000
    staging = db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source LIKE '__staging_%'")
    assert int(staging["n"]) == 0

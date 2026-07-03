from __future__ import annotations

import csv
import gzip
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def test_malformed_database_is_quarantined_and_recreated(tmp_path: Path):
    db_path = tmp_path / "runtime" / "app.db"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"this is not a sqlite database")

    db = Database(db_path)

    assert db_path.exists()
    assert db.query_one("SELECT COUNT(*) AS n FROM datasets") is not None
    quarantined = list((db_path.parent / "corrupt_databases").glob("*/app.db"))
    assert quarantined, "malformed database should be moved aside before app startup continues"


def _write_tags_csv(path: Path, rows: int) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "name", "category", "post_count"])
        for idx in range(rows):
            writer.writerow([idx, f"tag_{idx:06d}", idx % 9, idx])


def test_verified_import_uses_staging_and_preserves_live_dictionary_on_bad_candidate(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db, paths)

    tags.upsert_dictionary_entry("e621", "existing_tag", "general", 1, is_custom=False)
    bad = tmp_path / "tags-bad.csv.gz"
    _write_tags_csv(bad, 10)

    try:
        tags.verified_import_dictionary_csv(bad, "e621", replace_existing=True, min_expected=100)
    except ValueError:
        pass
    else:
        raise AssertionError("under-sized candidate should be rejected")

    assert tags.dictionary_status("e621")["total"] == 1
    assert tags.resolve_category("existing_tag", "e621") == "general"


def test_verified_import_promotes_good_staged_dictionary(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db, paths)

    good = tmp_path / "tags-good.csv.gz"
    _write_tags_csv(good, 5_000)
    count = tags.verified_import_dictionary_csv(good, "e621", replace_existing=True, min_expected=1_000)

    assert count == 5_000
    assert tags.dictionary_status("e621")["total"] == 5_000
    assert tags.resolve_category("tag_000004", "e621") == "character"

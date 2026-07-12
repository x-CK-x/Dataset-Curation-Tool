from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

from data_curation_tool import __version__
from data_curation_tool.database import Database, now_iso
from data_curation_tool.config import AppSettings
from data_curation_tool.services.install_migration_service import InstallMigrationService
from data_curation_tool.services.tag_service import TagService


def make_paths(root: Path):
    models = root / "models"
    runtime = root / "runtime"
    outputs = root / "outputs"
    for p in (models, runtime, outputs):
        p.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(root=root, models=models, runtime=runtime, outputs=outputs, settings=runtime / "settings.json")


def seed_tag_tables(db: Database) -> None:
    now = now_iso()
    db.execute(
        """INSERT OR IGNORE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
           VALUES (?, ?, ?, ?, '[]', '[]', 0, ?)""",
        ("e621", "blue_eyes", "general", 123, now),
    )
    db.execute(
        """INSERT OR IGNORE INTO tag_dictionary_search(source, tag, tag_lower, category, post_count, is_custom, updated_at)
           VALUES (?, ?, ?, ?, ?, 0, ?)""",
        ("e621", "blue_eyes", "blue_eyes", "general", 123, now),
    )
    db.execute(
        "INSERT OR IGNORE INTO tag_aliases(source, alias, target, status, updated_at) VALUES (?, ?, ?, 'active', ?)",
        ("e621", "blue eyes", "blue_eyes", now),
    )
    db.execute(
        "INSERT OR IGNORE INTO tag_implications(source, antecedent, consequent, status, updated_at) VALUES (?, ?, ?, 'active', ?)",
        ("e621", "blue_eyes", "eyes", now),
    )
    db.execute(
        "INSERT OR IGNORE INTO artist_aliases(source, artist_name, alias, is_active, updated_at) VALUES (?, ?, ?, 1, ?)",
        ("e621", "artist_a", "artist alias", now),
    )
    db.execute(
        """INSERT OR IGNORE INTO tag_export_files(profile_key, role, url, local_path, sha256, downloaded_at, imported_at, row_count, status, error)
           VALUES (?, ?, ?, ?, '', ?, ?, ?, 'imported', '')""",
        ("e621", "tags", "old-url", "C:/old/runtime/tag_exports/e621/tags.csv.gz", now, now, 196),
    )
    db.execute(
        "INSERT OR IGNORE INTO tag_dictionary(tag, category, post_count, aliases_json, implications_json, updated_at) VALUES (?, ?, ?, '[]', '[]', ?)",
        ("blue_eyes", "general", 123, now),
    )


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"


def test_tag_database_import_skips_stale_export_metadata_and_updates_progress(tmp_path: Path):
    old_paths = make_paths(tmp_path / "old")
    old_db = Database(old_paths.runtime / "app.db")
    TagService(old_db, old_paths)
    seed_tag_tables(old_db)

    current_paths = make_paths(tmp_path / "current")
    current_db = Database(current_paths.runtime / "app.db")
    TagService(current_db, current_paths)
    service = InstallMigrationService(current_paths, db=current_db, app_settings=AppSettings())

    job_id = current_db.create_job("asset_migration", {"test": True})
    progress_messages: list[str] = []

    def progress(value: float, message: str = "") -> None:
        progress_messages.append(message)
        current_db.update_job(job_id, status="running", progress=value, message=message)

    result = service.import_tag_database(old_paths.runtime / "app.db", progress=progress)

    assert result["tables"]["tag_export_files"]["skipped"] == "rebuilt from migrated tag-export cache"
    assert result["tables"]["tag_dictionary"]["skipped"] == "modern normalized tag tables were present"
    assert any("Skipped migrated tag table tag_export_files" in msg for msg in progress_messages)
    assert any("Skipped migrated legacy tag table tag_dictionary" in msg for msg in progress_messages)
    assert current_db.query_one("SELECT tag FROM tag_dictionary_entries WHERE source='e621' AND tag='blue_eyes'")
    # Old export-file local paths should not be imported into the new install.
    assert current_db.query_one("SELECT COUNT(*) AS n FROM tag_export_files WHERE local_path LIKE 'C:/old/%'")["n"] == 0
    job = current_db.query_one("SELECT progress, message FROM jobs WHERE id=?", (job_id,))
    assert job is not None
    assert float(job["progress"]) > 0.0


def test_import_tag_database_does_not_hold_global_database_lock_while_reporting_progress(tmp_path: Path):
    old_paths = make_paths(tmp_path / "old")
    old_db = Database(old_paths.runtime / "app.db")
    TagService(old_db, old_paths)
    seed_tag_tables(old_db)

    current_paths = make_paths(tmp_path / "current")
    current_db = Database(current_paths.runtime / "app.db")
    TagService(current_db, current_paths)
    service = InstallMigrationService(current_paths, db=current_db, app_settings=AppSettings())

    can_query_inside_progress = False

    def progress(_value: float, _message: str = "") -> None:
        nonlocal can_query_inside_progress
        # This would block or time out in the older implementation when progress
        # was emitted while the migration import held a write transaction and the
        # Database._lock around the entire import.
        row = current_db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries")
        can_query_inside_progress = can_query_inside_progress or row is not None

    service.import_tag_database(old_paths.runtime / "app.db", progress=progress)
    assert can_query_inside_progress is True

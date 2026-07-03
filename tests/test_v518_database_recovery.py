from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database


def test_v518_quarantines_malformed_database_before_startup(tmp_path: Path):
    db_path = tmp_path / "app.db"
    db_path.write_bytes(b"this is not a sqlite database")

    db = Database(db_path)

    assert db.query_one("SELECT COUNT(*) AS n FROM settings") is not None
    backups = list((tmp_path / "corrupt_databases").glob("*/app.db"))
    assert backups, "malformed database should be moved aside instead of crashing startup"
    assert backups[0].read_bytes() == b"this is not a sqlite database"


def test_v518_runtime_corruption_recovery_reinitializes_database(tmp_path: Path):
    db_path = tmp_path / "app.db"
    db = Database(db_path)
    db.execute("INSERT INTO settings(key, value_json, updated_at) VALUES (?, ?, ?)", ("demo", "{}", "now"))

    # Simulate a database getting corrupted after startup. The next operation
    # should quarantine the file, create a fresh DB, and retry the statement.
    db_path.write_bytes(b"broken after startup")
    inserted = db.execute("INSERT INTO settings(key, value_json, updated_at) VALUES (?, ?, ?)", ("after_recovery", "{}", "now"))

    assert inserted >= 0
    assert db.query_one("SELECT key FROM settings WHERE key=?", ("after_recovery",))["key"] == "after_recovery"
    backups = list((tmp_path / "corrupt_databases").glob("*/app.db"))
    assert backups


def test_v518_tag_import_no_longer_disables_sqlite_journal():
    source = Path(__file__).resolve().parents[1] / "data_curation_tool" / "services" / "tag_service.py"
    text = source.read_text(encoding="utf-8")
    assert "journal_mode=OFF" not in text
    assert "synchronous=OFF" not in text

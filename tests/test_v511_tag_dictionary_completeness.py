import csv
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def test_v511_large_tag_dictionary_import_keeps_more_than_100k_rows(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs"))
    csv_path = tmp_path / "tags-large.csv"
    total_rows = 125_000
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "category", "post_count"])
        for i in range(total_rows):
            writer.writerow([i + 1, f"large_tag_{i:06d}", i % 9, 0 if i % 3 == 0 else i])
    assert tags.count_dictionary_csv_rows(csv_path, "e621") == total_rows
    imported = tags.import_dictionary_csv(csv_path, "e621", replace_existing=True)
    assert imported == total_rows
    stored = db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source='e621'")
    search = db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_search WHERE source='e621'")
    assert int(stored["n"]) == total_rows
    assert int(search["n"]) == total_rows
    assert int(stored["n"]) > 100_000


def test_v511_alias_exports_do_not_count_as_real_tag_dictionary(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs"))
    alias_csv = tmp_path / "tag_aliases.csv"
    with alias_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["antecedent_name", "consequent_name"])
        for i in range(1000):
            writer.writerow([f"alias_{i}", f"real_tag_{i}"])
    assert tags.import_aliases_csv(alias_csv, "e621") == 1000
    stored = db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_entries WHERE source='e621'")
    aliases = db.query_one("SELECT COUNT(*) AS n FROM tag_aliases WHERE source='e621'")
    assert int(stored["n"] or 0) == 0
    assert int(aliases["n"] or 0) == 1000
    assert tags.metadata(["alias_10"], "e621")["alias_10"]["category"] == "invalid"

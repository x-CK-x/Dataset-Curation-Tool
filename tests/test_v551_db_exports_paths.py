from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def test_e621_defaults_prefer_plural_db_exports(tmp_path: Path):
    tags = TagService(Database(tmp_path / "app.sqlite3"), AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs"))
    urls = tags.default_export_urls("e621")
    assert urls[0] == "https://e621.net/db_exports/"
    assert "https://e621.net/db_exports/tags.csv.gz" in urls
    assert "https://e621.net/db_export/tags.csv.gz" in urls
    assert tags.get_profile("e621")["db_export_url"] == "https://e621.net/db_exports/"


def test_existing_legacy_profile_url_is_migrated_to_plural(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    tags = TagService(db, paths)
    tags.upsert_profile("e621", db_export_url="https://e621.net/db_export/")
    tags = TagService(db, paths)
    assert tags.get_profile("e621")["db_export_url"] == "https://e621.net/db_exports/"


def test_plural_export_download_falls_back_to_legacy_when_needed(tmp_path: Path, monkeypatch):
    import data_curation_tool.services.tag_service as tag_module
    monkeypatch.setitem(tag_module.MIN_EXPECTED_TAG_ROWS, "e621", 0)
    monkeypatch.setitem(tag_module.MIN_CANONICAL_TAG_ROWS, "e621", 0)
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs"))
    tag_csv = tmp_path / "tags.csv"
    tag_csv.write_text("id,name,category,post_count\n1,blue_hair,0,100\n2,alice,4,20\n", encoding="utf-8")
    alias_csv = tmp_path / "tag_aliases.csv"
    alias_csv.write_text("antecedent_name,consequent_name\nblu_hair,blue_hair\n", encoding="utf-8")
    implication_csv = tmp_path / "tag_implications.csv"
    implication_csv.write_text("antecedent_name,consequent_name\nalice,1girl\n", encoding="utf-8")

    def fake_download(url: str, profile_key: str, user_agent: str = "", cache_hours: int = 0):
        if "/db_exports/" in url:
            raise RuntimeError("new path unavailable in this test")
        if "alias" in url:
            return alias_csv
        if "implication" in url:
            return implication_csv
        return tag_csv

    monkeypatch.setattr(tags, "download_export_file", fake_download)
    result = tags.import_default_exports("e621")
    assert result["imported"] >= 4
    assert any("/db_exports/" in item["url"] and item.get("error") for item in result["files"])
    assert any("/db_export/" in item["url"] and item.get("imported") for item in result["files"])
    meta = tags.metadata(["blue_hair", "alice", "blu_hair"], "e621")
    assert meta["blue_hair"]["category"] == "general"
    assert meta["alice"]["category"] == "character"
    assert meta["blu_hair"]["category"] == "general"

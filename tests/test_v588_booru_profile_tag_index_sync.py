from __future__ import annotations

import json
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.downloader_service import source_definitions
from data_curation_tool.services.tag_service import TagService


def _tag_service(tmp_path: Path) -> TagService:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    return TagService(db, paths)


def test_dropdown_booru_sources_advertise_source_specific_tag_sync() -> None:
    rows = {row["key"]: row for row in source_definitions()}
    for key in ("e621", "e926", "danbooru", "gelbooru", "safebooru", "rule34", "konachan", "yandere"):
        assert rows[key]["supports_tag_dictionary_sync"] is True
        assert rows[key]["tag_profile_key"] == key
        assert rows[key]["expected_tag_export_roles"]
    assert rows["gelbooru"]["tag_sync_strategy"] == "tag_index_api"
    assert rows["generic-json"]["supports_tag_dictionary_sync"] is False


def test_non_e621_profiles_have_default_tag_index_urls_and_tags_only_expected_role(tmp_path: Path) -> None:
    svc = _tag_service(tmp_path)
    for key in ("gelbooru", "safebooru", "rule34", "konachan", "yandere"):
        urls = svc.default_export_urls(key)
        assert urls and urls[0].startswith("https://")
        caps = svc.tag_sync_capabilities(key)
        assert caps["supports_tag_index_api"] is True
        assert caps["expected_roles"] == ["tags"]
        status = svc.dictionary_status(key)
        assert status["missing_roles"] == ["tags"]
        assert status["expected_roles"] == ["tags"]


def test_tag_index_jsonl_cache_imports_categories_into_profile_dictionary(tmp_path: Path) -> None:
    svc = _tag_service(tmp_path)
    cache = svc.paths.runtime / "tag_exports" / "gelbooru" / "tags_api.jsonl"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        "\n".join(
            [
                json.dumps({"tag": "blue_hair", "category": 0, "post_count": 100}),
                json.dumps({"tag": "hakurei_reimu", "category": 4, "post_count": 50}),
                json.dumps({"tag": "touhou", "category": 3, "post_count": 75}),
            ]
        ),
        encoding="utf-8",
    )

    result = svc.import_tag_index_jsonl_cache(cache, "gelbooru", replace_existing=True)

    assert result["imported"] == 3
    assert svc.resolve_category("blue_hair", "gelbooru") == "general"
    assert svc.resolve_category("hakurei_reimu", "gelbooru") == "character"
    assert svc.resolve_category("touhou", "gelbooru") == "copyright"
    status = svc.dictionary_status("gelbooru")
    assert status["total"] == 3
    assert status["missing_roles"] == []
    assert status["latest_exports"]["tags"]["status"] == "imported"


def test_import_default_exports_falls_back_to_tag_index_api_when_no_db_export_files(tmp_path: Path, monkeypatch) -> None:
    svc = _tag_service(tmp_path)
    called = {}

    monkeypatch.setattr(svc, "discover_export_urls", lambda *args, **kwargs: [])

    def fake_import_tag_index_api(**kwargs):
        called.update(kwargs)
        return {"profile_key": kwargs["profile_key"], "imported": 12, "files": [{"role": "tags", "imported": 12}], "status": {"total": 12}}

    monkeypatch.setattr(svc, "import_tag_index_api", fake_import_tag_index_api)

    result = svc.import_default_exports("gelbooru", user_agent="test-agent", replace_existing=True)

    assert called["profile_key"] == "gelbooru"
    assert called["user_agent"] == "test-agent"
    assert result["imported"] >= 12
    assert any(row.get("role") == "tags" and row.get("imported") == 12 for row in result["files"])

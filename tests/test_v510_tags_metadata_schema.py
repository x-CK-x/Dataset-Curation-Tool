from __future__ import annotations

import json
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.metadata_service import MetadataService
from data_curation_tool.services.tag_service import TagService


def _paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_v510_tag_dictionary_import_keeps_zero_count_rows(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, _paths(tmp_path))
    csv_path = tmp_path / "tags.csv"
    csv_path.write_text(
        "id,name,category,post_count\n"
        "1,active_tag,0,12\n"
        "2,zero_count_old_tag,4,0\n"
        "3,another_zero,1,0\n",
        encoding="utf-8",
    )
    assert tags.import_dictionary_csv(csv_path, "e621", replace_existing=True) == 3
    meta = tags.metadata(["active_tag", "zero_count_old_tag", "another_zero"], "e621")
    assert meta["zero_count_old_tag"]["known"] is True
    assert meta["zero_count_old_tag"]["category"] == "character"
    assert meta["another_zero"]["category"] == "artist"


def test_v510_default_export_candidates_include_dated_fallbacks(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, _paths(tmp_path))
    urls = tags.default_export_urls("e621")
    recent = tags._recent_dated_export_candidates("e621", days=2)
    assert "https://e621.net/db_exports/tags.csv.gz" in urls
    assert any("/db_exports/tags-" in u for u in recent)


def test_v510_metadata_json_field_catalog_and_compose(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    paths = _paths(tmp_path)
    tag_service = TagService(db, paths)
    metadata = MetadataService(db, paths, MediaService(db, paths), tag_service)
    meta_path = tmp_path / "generation.json"
    meta_path.write_text(json.dumps({"prompt": "(blue hair:1.2), {artist_name}, 1girl", "nested": {"caption": "hero pose"}}), encoding="utf-8")
    inspected = metadata.inspect_fields_for_media(path=str(meta_path), include_raw=True)
    paths_seen = {item["path"] for item in inspected["fields"]}
    assert "$.normalized_metadata.normalized.prompt" in paths_seen
    result = metadata.compose_from_fields(
        path=str(meta_path),
        fields=["$.normalized_metadata.normalized.prompt", "$.normalized_metadata.normalized.nested.caption"],
        original_delimiter="auto",
        output_delimiter=" | ",
        keep_parentheses=False,
        keep_braces=False,
        strip_weight_syntax=True,
        normalize_tags=True,
    )
    assert result["tokens"][:3] == ["blue_hair", "artist_name", "1girl"]
    assert result["composed"].startswith("blue_hair | artist_name | 1girl")

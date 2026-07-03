from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.services.tag_service import TagService


def test_tag_parse_prune(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    tags = TagService(db)
    ds = db.insert_dataset("demo", str(tmp_path), {})
    media_id = db.upsert_media({"dataset_id": ds, "path": str(tmp_path / "a.png"), "relative_path": "a.png", "media_type": "image", "ext": "png"})
    tags.set_tag_string(media_id, "1girl, girl, highres, nan")
    result = tags.prune(type("Req", (), {"media_ids": [media_id], "dataset_id": None, "implications": {}, "dry_run": False})())
    assert result[0].removed == ["girl"]
    assert "1girl" in tags.get_tags(media_id)
    assert "girl" not in tags.get_tags(media_id)


def test_profile_suggestions_custom_unknown_and_reorder(tmp_path: Path):
    db = Database(tmp_path / "test_profiles.db")
    tags = TagService(db)
    tags.upsert_dictionary_entry("e621", "alpha_style", "artist", 10)
    tags.upsert_dictionary_entry("e621", "alpha_character", "character", 100)
    suggestions = tags.suggest("alpha", profile_key="e621", limit=10)
    assert [s["tag"] for s in suggestions][:2] == ["alpha_character", "alpha_style"]
    custom = tags.add_custom_tag("e621", "popular_tv_character", "character")
    assert custom["category"] == "character"
    metadata = tags.metadata(["popular_tv_character", "missing_tag"], "e621")
    assert metadata["popular_tv_character"]["known"] is True
    assert metadata["missing_tag"]["known"] is False
    ordered = tags.order_tags(["blue_background", "alpha_style", "alpha_character"], profile_key="e621", strategy="booru")
    assert ordered == ["alpha_character", "alpha_style", "blue_background"]

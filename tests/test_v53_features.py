from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_dictionary_status_default_urls_and_profile_precedence(tmp_path: Path):
    client = _client(tmp_path)
    urls = client.get("/api/tags/dictionary/default-urls?profile_key=e621").json()
    assert urls["profile_key"] == "e621"
    assert any("tags.csv.gz" in url for url in urls["urls"])

    profile = client.post(
        "/api/tags/profiles",
        json={
            "key": "my_lora_profile",
            "label": "My LoRA Profile",
            "categories": [
                {"key": "style", "label": "Style", "css_class": "cat-style"},
                {"key": "character", "label": "Character", "css_class": "cat-character"},
                {"key": "concept", "label": "Concept", "css_class": "cat-concept"},
            ],
            "precedence": ["style", "character", "concept"],
        },
    )
    assert profile.status_code == 200
    assert profile.json()["key"] == "my_lora_profile"

    updated = client.put(
        "/api/tags/profiles/my_lora_profile/precedence",
        json={"precedence": ["character", "style"]},
    )
    assert updated.status_code == 200
    assert updated.json()["precedence"][:2] == ["character", "style"]


def test_fast_suggest_uses_search_table_and_custom_tags(tmp_path: Path):
    db = Database(tmp_path / "suggest.db")
    tags = TagService(db)
    tags.upsert_dictionary_entry("danbooru", "blue_hair", "general", 1000)
    tags.upsert_dictionary_entry("danbooru", "blue_archive", "copyright", 5000)
    tags.add_custom_tag("danbooru", "popular_tv_character", "character")
    result = tags.suggest("blue", profile_key="danbooru", limit=5)
    assert [item["tag"] for item in result][:2] == ["blue_archive", "blue_hair"]
    assert tags.suggest("popular_tv", profile_key="danbooru", limit=5)[0]["category"] == "character"
    status = tags.dictionary_status("danbooru")
    assert status["total"] >= 3


def test_static_hud_contains_real_tag_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Tag Dictionaries" in app_js
    assert "Batch Tags" in app_js
    assert "pointerdown" in app_js
    assert "dropIndexFromPointer" in app_js
    assert "Load Default DB Export" in app_js
    assert "Select Page by Category" in app_js
    assert "Add Selected Left → Right" in app_js
    assert "tag-x" in app_js

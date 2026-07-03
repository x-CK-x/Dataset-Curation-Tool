from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.browser_service import BrowserService
from data_curation_tool.models.adapters import HFImageMultiLabelTaggerAdapter, HFImageRatingAdapter


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_redrocket_models_are_front_facing_and_downloadable(tmp_path: Path):
    client = _client(tmp_path)
    models = {m["name"]: m for m in client.get("/api/models").json()}
    assert "redrocket-jtp-3" in models
    assert models["redrocket-jtp-3"]["repo_id"] == "RedRocket/JTP-3"
    assert models["redrocket-jtp-3"]["download_supported"] is True
    assert {"tag", "auto_tag", "editor", "batch", "compare", "orchestration"}.issubset(set(models["redrocket-jtp-3"]["capabilities"]))
    assert "redrocket-e6-visual-ratings" in models
    assert models["redrocket-e6-visual-ratings"]["repo_id"] == "RedRocket/e6-visual-ratings"
    assert models["redrocket-e6-visual-ratings"]["download_supported"] is True
    assert {"rating", "classify", "tag", "compare", "orchestration"}.issubset(set(models["redrocket-e6-visual-ratings"]["capabilities"]))


def test_redrocket_label_normalization_helpers():
    tagger = HFImageMultiLabelTaggerAdapter("rr", "RR", "RedRocket/JTP-3")
    assert tagger._tag_from_label("Blue Hair") == "blue_hair"
    assert tagger._tag_from_label("tag_001:=artist:name") == "artist:name"
    rater = HFImageRatingAdapter("rating", "Rating", "RedRocket/e6-visual-ratings")
    assert rater._rating_tag("safe") == "safe"
    assert rater._rating_tag("q") == "questionable"
    assert rater._rating_tag("explicit") == "explicit"


def test_booru_source_validation_covers_all_sources(tmp_path: Path):
    client = _client(tmp_path)
    result = client.get("/api/downloads/source-validation").json()
    assert result["ok"] is True
    keys = {row["key"] for row in result["sources"]}
    for key in ["e621", "e926", "danbooru", "gelbooru", "safebooru", "rule34", "konachan", "yandere", "generic-json"]:
        assert key in keys


def test_browser_self_test_endpoint_without_live_launch(tmp_path: Path):
    client = _client(tmp_path)
    result = client.post("/api/browser/self-test", json={"install": False, "launch": False, "headless": True}).json()
    assert "status" in result
    assert "geckodriver_path" in result["status"]
    assert any(check["name"] == "firefox_found" for check in result["checks"])


def test_geckodriver_fallback_asset_is_platform_specific(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    service = BrowserService(paths)
    key = service.platform_key()
    asset = service._fallback_geckodriver_asset(key)
    assert asset["name"].startswith("geckodriver-v")
    assert key in asset["name"]
    assert asset["browser_download_url"].endswith(asset["name"])

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DatasetCreate


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_import_reads_json_sidecar_categories_and_refresh_endpoint_updates_them(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    img = root / "sample.png"
    Image.new("RGB", (32, 24), "white").save(img)
    img.with_suffix(".txt").write_text("artist_tag, character_tag, blue_hair", encoding="utf-8")
    img.with_suffix(".json").write_text(
        '{"categories":{"artist_tag":"artist","character_tag":"4","blue_hair":"general"},"caption":"json caption"}',
        encoding="utf-8",
    )

    client = _client(tmp_path)
    ctx = client.app.state.context
    result = ctx.datasets.import_folder(DatasetCreate(root_path=str(root)), progress=lambda p, m: None)
    page = client.get(f"/api/media?dataset_id={result['dataset_id']}").json()
    item = page["items"][0]
    assert item["categories"]["artist_tag"] == "artist"
    assert item["categories"]["character_tag"] == "character"
    assert item["categories"]["blue_hair"] == "general"
    assert item["caption"] == "json caption"

    img.with_suffix(".json").write_text(
        '{"categories":{"artist_tag":"artist","character_tag":"character","blue_hair":"meta"},"caption":"changed"}',
        encoding="utf-8",
    )
    refreshed = client.post("/api/media/refresh-sidecars", json={"media_ids": [item["id"]], "tag_profile": "e621"})
    assert refreshed.status_code == 200
    assert refreshed.json()["refreshed"] == 1

    updated = client.get(f"/api/media/{item['id']}").json()
    assert updated["categories"]["blue_hair"] == "meta"
    assert updated["caption"] == "changed"


def test_static_hud_contains_gallery_refresh_and_category_normalization():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Search / Refresh" in app_js
    assert "Reload Page" in app_js
    assert "Refresh JSON/Sidecars + Reload" in app_js
    assert "CATEGORY_ALIASES" in app_js
    assert "'4': 'character'" in app_js

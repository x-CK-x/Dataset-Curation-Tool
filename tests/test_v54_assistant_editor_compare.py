from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DatasetCreate


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_model_tag_selection_uses_saved_json_sidecar_categories(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    img = root / "sample.png"
    Image.new("RGB", (32, 24), "white").save(img)
    img.with_suffix(".txt").write_text("char_from_json, general_tag", encoding="utf-8")
    img.with_suffix(".json").write_text(
        '{"tag_categories":{"char_from_json":"4","general_tag":"0"}}',
        encoding="utf-8",
    )

    client = _client(tmp_path)
    ctx = client.app.state.context
    result = ctx.datasets.import_folder(DatasetCreate(root_path=str(root)), progress=lambda p, m: None)
    item = client.get(f"/api/media?dataset_id={result['dataset_id']}").json()["items"][0]

    response = client.post(
        "/api/models/select-tags",
        json={"media_ids": [item["id"]], "criteria": "character", "profile_key": "e621", "operation": "preview"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "char_from_json" in payload["selected_tags"]
    assert payload["selected_tags_by_media"][str(item["id"])] == ["char_from_json"]


def test_static_hud_contains_editor_and_compare_assistant_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "LLM/VLM/Assistant Tag Selection for This Image" in app_js
    assert "LLM/VLM/Assistant Tag Selection for Current Compare Pair" in app_js
    assert "Compare Queue" in app_js
    assert "Left ▶" in app_js
    assert "Right ▶" in app_js
    assert "markEditorAssistantSelection" in app_js
    assert "markCompareAssistantSelection" in app_js
    assert "categoryFromItem" in app_js

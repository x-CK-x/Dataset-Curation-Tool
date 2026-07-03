from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_api_health_and_models(tmp_path: Path):
    client = _client(tmp_path)
    assert client.get("/api/health").json()["ok"] is True
    models = client.get("/api/models").json()
    assert any(model["name"] == "rule-based-filename" for model in models)
    assert any(model["name"] == "dataset-assistant" for model in models)


def test_new_sources_categories_and_chat(tmp_path: Path):
    client = _client(tmp_path)
    sources = client.get("/api/downloads/sources").json()
    assert any(item["key"] == "gelbooru" for item in sources)
    categories = client.get("/api/tags/categories").json()
    assert any(item["key"] == "character" for item in categories)
    response = client.post(
        "/api/models/chat",
        json={"model_name": "dataset-assistant", "prompt": "Suggest portrait character tags"},
    )
    assert response.status_code == 200
    assert "suggested_tags" in response.json()

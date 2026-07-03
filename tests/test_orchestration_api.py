from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_tag_profile_metadata_and_orchestration_templates(tmp_path: Path):
    client = _client(tmp_path)
    profiles = client.get("/api/tags/profiles").json()
    assert any(p["key"] == "e621" for p in profiles)
    added = client.post("/api/tags/custom", json={"profile_key": "e621", "tag": "popular_tv_character", "category": "character"}).json()
    assert added["category"] == "character"
    meta = client.post("/api/tags/metadata", json={"profile_key": "e621", "tags": ["popular_tv_character", "missing_tag"]}).json()
    assert meta["popular_tv_character"]["known"] is True
    assert meta["missing_tag"]["known"] is False
    ordered = client.post("/api/tags/reorder", json={"profile_key": "e621", "strategy": "booru", "tags": ["missing_tag", "popular_tv_character"]}).json()
    assert ordered["tags"] == ["popular_tv_character", "missing_tag"]
    templates = client.get("/api/orchestration/templates").json()
    assert any(t["key"] == "classifier-threshold-check" for t in templates)


def test_settings_accept_tokens_and_orchestration_run(tmp_path: Path):
    client = _client(tmp_path)
    r = client.put("/api/settings", json={"values": {"openrouter_token": "test", "tag_suggestion_count": 25, "preferred_devices": ["cuda:0", "cuda:1"]}})
    assert r.status_code == 200
    settings = r.json()
    assert settings["openrouter_token"] == "********"
    assert settings["tag_suggestion_count"] == 25
    response = client.post("/api/orchestration/run", json={"name": "empty", "dry_run": True, "steps": [{"kind": "tag_select", "prompt": "select unknown tags"}]})
    assert response.status_code == 200
    assert "job_id" in response.json()

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.models.adapters import HFImageCaptionAdapter, HFImageClassifierAdapter
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_redrocket_models_are_front_facing_downloadable_rows(tmp_path: Path):
    c = _client(tmp_path)
    models = {m["name"]: m for m in c.get("/api/models").json()}
    assert "redrocket-jtp-3" in models
    assert "redrocket-e6-visual-ratings" in models
    assert models["redrocket-jtp-3"]["repo_id"] == "RedRocket/JTP-3"
    assert models["redrocket-e6-visual-ratings"]["repo_id"] == "RedRocket/e6-visual-ratings"
    assert models["redrocket-jtp-3"]["download_supported"] is True
    assert "tag" in models["redrocket-jtp-3"]["capabilities"]
    assert "rating" in models["redrocket-e6-visual-ratings"]["capabilities"]


def test_hf_image_adapters_prefer_downloaded_or_custom_model_id(monkeypatch):
    calls = []

    def fake_pipeline(task, model, **kwargs):
        calls.append((task, model, kwargs))
        return lambda *a, **k: []

    import sys, types
    mod = types.SimpleNamespace(pipeline=fake_pipeline)
    monkeypatch.setitem(sys.modules, "transformers", mod)
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace())

    clf = HFImageClassifierAdapter("x", "X", "repo/original")
    clf.load(model_id="/tmp/downloaded-model", device="cpu")
    cap = HFImageCaptionAdapter("c", "C", "repo/caption")
    cap.load(model_id="/tmp/caption-model", device="cpu")
    assert calls[0][1] == "/tmp/downloaded-model"
    assert calls[1][1] == "/tmp/caption-model"


def test_browser_status_and_source_validation_endpoints(tmp_path: Path):
    c = _client(tmp_path)
    status = c.get("/api/browser/status").json()
    assert "geckodriver_path" in status
    assert "firefox_binary" in status
    validation = c.get("/api/downloads/source-validation").json()
    keys = {item["source"] for item in validation["sources"]}
    for expected in ["e621", "e926", "danbooru", "gelbooru", "safebooru", "rule34", "konachan", "yandere"]:
        assert expected in keys
    assert validation["ok"] is True

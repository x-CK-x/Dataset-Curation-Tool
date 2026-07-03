from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.install_migration_service import InstallMigrationService


def _client(tmp_path: Path) -> tuple[TestClient, AppPaths]:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths)), paths


def test_custom_model_requires_category_and_is_pinned_to_top(tmp_path: Path):
    client, paths = _client(tmp_path)
    bad = client.post("/api/models/custom", json={"label": "My EfficientNet", "repo_id": "timm/tf_efficientnetv2_s.in21k"})
    assert bad.status_code == 400
    assert "category" in bad.text.lower()

    ok = client.post(
        "/api/models/custom",
        json={"label": "My EfficientNet", "category": "classifier", "repo_id": "timm/tf_efficientnetv2_s.in21k", "provider": "huggingface"},
    )
    assert ok.status_code == 200
    model = ok.json()["model"]
    assert model["user_custom"] is True
    assert model["custom_category"] == "classifier"

    rows = client.get("/api/models").json()
    assert rows[0]["user_custom"] is True
    assert rows[0]["label"] == "My EfficientNet"
    saved = json.loads(paths.settings.read_text(encoding="utf-8"))
    assert saved["custom_models"][0]["category"] == "classifier"
    assert (paths.runtime / "custom_models.json").exists()


def test_modern_cv_registry_rows_include_efficientnet_detection_segmentation():
    registry = ModelRegistry(Path("/tmp/dct-model-test"))
    rows = {row["name"]: row for row in registry.list()}
    for name in [
        "timm-efficientnetv2-s-21k",
        "timm-efficientnetv2-rw-m-in1k",
        "timm-gc-efficientnetv2-rw-t-in1k",
        "yolo26n-detect",
        "rtdetrv2-l-detection",
        "d-fine-detector-contract",
        "florence-2-large-multitask",
        "sam3-contract",
    ]:
        assert name in rows
    assert rows["timm-efficientnetv2-s-21k"]["kind"] == "classifier"
    assert rows["yolo26n-detect"]["kind"] == "detection"
    assert rows["sam3-contract"]["kind"] == "segmentation"


def test_migration_skips_corrupt_models_and_imports_custom_registry(tmp_path: Path, monkeypatch):
    current = tmp_path / "current"
    previous = tmp_path / "previous"
    current.mkdir()
    previous.mkdir()
    monkeypatch.chdir(current)
    paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")
    settings = AppSettings.load(paths.settings)
    service = InstallMigrationService(paths, app_settings=settings)

    good = previous / "models" / "hf" / "good-repo"
    good.mkdir(parents=True)
    (good / "model.safetensors").write_bytes(b"valid weights")
    (good / "config.json").write_text("{}", encoding="utf-8")

    corrupt = previous / "models" / "hf" / "corrupt-repo"
    corrupt.mkdir(parents=True)
    (corrupt / "config.json").write_text("{}", encoding="utf-8")
    (corrupt / "model.safetensors.part").write_bytes(b"partial")

    zero = previous / "models" / "hf" / "zero-repo"
    zero.mkdir(parents=True)
    (zero / "model.safetensors").write_bytes(b"")

    old_settings = previous / "runtime" / "settings.json"
    old_settings.parent.mkdir(parents=True)
    old_settings.write_text(
        json.dumps({"custom_models": [{"label": "Prior Custom VLM", "category": "vlm", "repo_id": "example/prior-vlm"}]}),
        encoding="utf-8",
    )

    result = service.migrate([str(previous)], include={"models": True, "custom_models": True, "tag_exports": False, "tag_database": False, "custom_tags": False}, mode="copy")
    assert result["errors"] == []
    assert (current / "models" / "hf" / "good-repo" / "model.safetensors").exists()
    assert not (current / "models" / "hf" / "corrupt-repo" / "config.json").exists()
    assert not (current / "models" / "hf" / "zero-repo" / "model.safetensors").exists()
    assert result["custom_models"][0]["imported"] == 1
    saved = json.loads(paths.settings.read_text(encoding="utf-8"))
    assert saved["custom_models"][0]["category"] == "vlm"


def test_frontend_custom_model_affordances_are_present():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "Add Custom Model to Catalog" in app_js
    assert "Choose the custom model category first" in app_js
    assert "function sortedModels" in app_js
    assert "CUSTOM" in app_js
    assert "user-custom-model" in css
    assert "custom-model-chip" in css

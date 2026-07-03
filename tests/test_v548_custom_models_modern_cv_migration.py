from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.install_migration_service import InstallMigrationService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_custom_model_requires_category_and_is_pinned_to_top(tmp_path: Path):
    client = _client(tmp_path)

    missing = client.post("/api/models/custom", json={"label": "No Category", "repo_id": "org/repo"})
    assert missing.status_code in {400, 422}

    saved = client.post(
        "/api/models/custom",
        json={"label": "My Test VLM", "category": "vlm", "repo_id": "example/my-vlm", "vram_gb": 6},
    )
    assert saved.status_code == 200
    model = saved.json()["model"]
    assert model["user_custom"] is True
    assert model["custom_model_category"] == "vlm"
    assert model["source_type"] == "huggingface"

    rows = client.get("/api/models").json()
    assert rows[0]["name"] == model["name"]
    assert rows[0]["user_custom"] is True
    assert rows[0]["custom_model_category"] == "vlm"

    catalog = tmp_path / "runtime" / "custom_models.json"
    assert catalog.exists()
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    assert payload["models"][0]["category"] == "vlm"


def test_modern_cv_catalog_rows_are_front_facing(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    rows = {row["name"]: row for row in registry.list()}

    for name in [
        "efficientnetv2-s-in21k-ft-in1k",
        "efficientnetv2-l-in21k-ft-in1k",
        "timm-efficientnetv2-xl-21k",
        "convnextv2-large-22k",
        "grounding-dino-base-hf",
        "rtdetrv2-l-detection",
        "mask2former-swin-large-ade-panoptic",
        "sam2.1-hiera-large",
    ]:
        assert name in rows

    assert rows["efficientnetv2-l-in21k-ft-in1k"]["kind"] == "classifier"
    assert "classify" in rows["efficientnetv2-l-in21k-ft-in1k"]["capabilities"]
    assert rows["grounding-dino-base-hf"]["kind"] in {"detector", "detection"}
    assert "detect" in rows["grounding-dino-base-hf"]["capabilities"]
    assert rows["sam2.1-hiera-large"]["kind"] == "segmentation"
    assert rows["sam2.1-hiera-large"]["download_supported"] is True


def test_model_migration_copies_valid_groups_and_skips_corrupt_downloads(tmp_path: Path):
    current = tmp_path / "current"
    previous = tmp_path / "previous"
    current.mkdir()
    previous.mkdir()
    paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")

    valid = previous / "models" / "hf" / "valid-repo" / "model.safetensors"
    valid.parent.mkdir(parents=True, exist_ok=True)
    valid.write_text("valid weights", encoding="utf-8")
    (valid.parent / "config.json").write_text("{}", encoding="utf-8")

    corrupt = previous / "models" / "hf" / "broken-repo" / "model.safetensors.part"
    corrupt.parent.mkdir(parents=True, exist_ok=True)
    corrupt.write_text("partial", encoding="utf-8")
    zero = previous / "models" / "hf" / "zero-repo" / "model.safetensors"
    zero.parent.mkdir(parents=True, exist_ok=True)
    zero.write_bytes(b"")

    service = InstallMigrationService(paths)
    result = service.migrate(
        [str(previous)],
        include={"models": True, "custom_models": False, "tag_exports": False, "tag_database": False, "custom_tags": False},
        mode="copy",
        conflict="skip_existing",
    )

    assert result["errors"] == []
    assert (current / "models" / "hf" / "valid-repo" / "model.safetensors").exists()
    assert not (current / "models" / "hf" / "broken-repo" / "model.safetensors.part").exists()
    assert not (current / "models" / "hf" / "zero-repo" / "model.safetensors").exists()
    skipped = [op for op in result["files"] if op.get("action") == "skip_corrupt_model"]
    assert len(skipped) >= 2


def test_migration_imports_custom_model_catalog_and_rewrites_local_paths(tmp_path: Path):
    current = tmp_path / "current"
    previous = tmp_path / "previous"
    current.mkdir()
    previous.mkdir()
    paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")
    old_model = previous / "models" / "custom" / "local-vlm" / "model.safetensors"
    old_model.parent.mkdir(parents=True, exist_ok=True)
    old_model.write_text("weights", encoding="utf-8")
    catalog = previous / "runtime" / "custom_models.json"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps({"models": [{"name": "local-vlm", "label": "Local VLM", "category": "vlm", "local_source_path": str(old_model.parent)}]}),
        encoding="utf-8",
    )

    settings = AppSettings.load(paths.settings)
    service = InstallMigrationService(paths, app_settings=settings)
    result = service.migrate(
        [str(previous)],
        include={"models": True, "custom_models": True, "tag_exports": False, "tag_database": False, "custom_tags": False},
        mode="copy",
        conflict="skip_existing",
    )

    assert result["errors"] == []
    assert (current / "models" / "custom" / "local-vlm" / "model.safetensors").exists()
    new_catalog = current / "runtime" / "custom_models.json"
    assert new_catalog.exists()
    models = json.loads(new_catalog.read_text(encoding="utf-8"))["models"]
    assert models[0]["category"] == "vlm"
    assert str(current) in models[0]["local_source_path"]


def test_frontend_custom_model_controls_and_styles_present():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "Add Custom Model to Catalog" in app_js
    assert "REQUIRED: choose model category" in app_js
    assert "function sortedModels" in app_js
    assert "custom-model-chip" in app_js
    assert ".model-card.user-custom-model" in css
    assert ".user-custom-model-row" in css

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.install_migration_service import InstallMigrationService


def _make_hf_group(root: Path, folder_name: str, *, with_stale_lock: bool = False, missing_index_shard: bool = False) -> Path:
    group = root / "models" / "hf" / folder_name
    group.mkdir(parents=True)
    (group / "config.json").write_text("{}", encoding="utf-8")
    (group / "preprocessor_config.json").write_text("{}", encoding="utf-8")
    (group / "model-00001-of-00002.safetensors").write_bytes(b"a" * 32)
    if not missing_index_shard:
        (group / "model-00002-of-00002.safetensors").write_bytes(b"b" * 32)
    (group / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"a": "model-00001-of-00002.safetensors", "b": "model-00002-of-00002.safetensors"}}),
        encoding="utf-8",
    )
    if with_stale_lock:
        (group / "download.lock").write_bytes(b"stale lock should be ignored")
        (group / "model-00002-of-00002.safetensors.part").write_bytes(b"old temp file should be ignored")
    return group


def test_migration_moves_named_hf_model_folders_even_with_stale_locks(tmp_path: Path, monkeypatch):
    current = tmp_path / "current"
    previous = tmp_path / "previous"
    current.mkdir(); previous.mkdir()
    monkeypatch.chdir(current)
    paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")
    service = InstallMigrationService(paths)

    names = [
        "fancyfeast--llama-joycaption-beta-one-hf-llava",
        "Qwen--Qwen2.5-VL-7B-Instruct",
        "Qwen--Qwen3-VL-2B-Instruct",
    ]
    for name in names:
        _make_hf_group(previous, name, with_stale_lock=True)

    scan = service.scan([str(previous)], include={"models": True, "tag_exports": False, "tag_database": False})
    groups = scan["sources"][0]["assets"]["models"]["model_groups"]
    assert groups["valid"] == 3
    assert groups["skipped"] == 0

    result = service.migrate([str(previous)], include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False}, mode="move")
    assert result["errors"] == []
    for name in names:
        target = current / "models" / "hf" / name
        assert (target / "model-00001-of-00002.safetensors").exists()
        assert (target / "model-00002-of-00002.safetensors").exists()
        assert (target / "model.safetensors.index.json").exists()
        assert not (target / "download.lock").exists()
        assert not (target / "model-00002-of-00002.safetensors.part").exists()


def test_migration_keeps_repairable_sharded_hf_model_with_index_warning(tmp_path: Path, monkeypatch):
    current = tmp_path / "current"
    previous = tmp_path / "previous"
    current.mkdir(); previous.mkdir()
    monkeypatch.chdir(current)
    paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")
    service = InstallMigrationService(paths)

    _make_hf_group(previous, "Qwen--Qwen2.5-VL-7B-Instruct", missing_index_shard=True)
    scan = service.scan([str(previous)], include={"models": True, "tag_exports": False, "tag_database": False})
    reason = scan["sources"][0]["assets"]["models"]["model_groups"]["valid_groups"][0]["reason"]
    assert "index integrity warning" in reason
    result = service.migrate([str(previous)], include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False}, mode="copy")
    assert result["errors"] == []
    skipped = [row for row in result["files"] if row.get("action") == "skip_corrupt_model"]
    assert skipped == []
    assert (current / "models" / "hf" / "Qwen--Qwen2.5-VL-7B-Instruct" / "config.json").exists()


def test_model_list_marks_downloaded_and_exposes_instance_status(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    _make_hf_group(tmp_path, "Qwen--Qwen2.5-VL-7B-Instruct")
    client = TestClient(create_app(paths))
    rows = client.get("/api/models").json()
    row = next(item for item in rows if item["name"] == "qwen2.5-vl-7b")
    assert row["downloaded"] is True
    assert row["download_state"] == "downloaded"
    assert row["loaded_instance_count"] == 0
    assert "downloaded" in row["status_badges"]
    assert row["local_path"].endswith("Qwen--Qwen2.5-VL-7B-Instruct")


def test_frontend_model_status_indicators_present():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "function modelStatusBits" in app_js
    assert "loaded_instance_count" in app_js
    assert "DOWNLOADED" in app_js
    assert "LOADED x" in app_js
    assert "downloaded-model-chip" in app_js
    assert "loaded-instance-chip" in css
    assert "model-option-downloaded" in css

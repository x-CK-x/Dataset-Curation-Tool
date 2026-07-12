from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from data_curation_tool import __version__
from data_curation_tool.config import AppSettings
from data_curation_tool.services.install_migration_service import InstallMigrationService

ROOT = Path(__file__).resolve().parents[1]


def make_paths(root: Path):
    models = root / "models"
    runtime = root / "runtime"
    outputs = root / "outputs"
    for p in (models, runtime, outputs):
        p.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(root=root, models=models, runtime=runtime, outputs=outputs)


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"


def test_model_group_move_uses_single_directory_fast_path(tmp_path: Path):
    old = tmp_path / "old"
    model_dir = old / "models" / "hf" / "Fast--Group"
    model_dir.mkdir(parents=True)
    for idx in range(4):
        (model_dir / f"model-{idx}.safetensors").write_bytes(b"x" * 1024)
    (model_dir / "config.json").write_text('{"model_type":"demo"}', encoding="utf-8")

    current = tmp_path / "current"
    service = InstallMigrationService(make_paths(current), app_settings=AppSettings())
    plan = service._build_file_plan(
        [old],
        {"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False, "presets": False, "downloads": False, "outputs": False},
        "skip_existing",
        mode="move",
        fast_same_volume_moves=True,
    )
    assert len([op for op in plan if op.get("action") == "move_dir_fast"]) == 1
    assert not any(str(op.get("source", "")).endswith("model-0.safetensors") for op in plan)

    result = service.migrate(
        [old],
        include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False, "presets": False, "downloads": False, "outputs": False},
        mode="move",
        conflict="skip_existing",
        parallel_file_transfers=True,
        file_transfer_workers=4,
        fast_same_volume_moves=True,
    )
    assert (current / "models" / "hf" / "Fast--Group" / "model-3.safetensors").exists()
    assert not model_dir.exists()
    assert any(op.get("action") == "move_dir_fast" for op in result["files"])


def test_existing_complete_model_group_shortcuts_without_recopy(tmp_path: Path):
    old = tmp_path / "old"
    current = tmp_path / "current"
    src_group = old / "models" / "hf" / "Already--Moved"
    dst_group = current / "models" / "hf" / "Already--Moved"
    src_group.mkdir(parents=True)
    dst_group.mkdir(parents=True)
    for idx in range(3):
        data = (f"payload-{idx}".encode()) * 128
        (src_group / f"shard-{idx}.safetensors").write_bytes(data)
        (dst_group / f"shard-{idx}.safetensors").write_bytes(data)
    (src_group / "config.json").write_text("{}", encoding="utf-8")
    (dst_group / "config.json").write_text("{}", encoding="utf-8")

    service = InstallMigrationService(make_paths(current), app_settings=AppSettings())
    result = service.migrate(
        [old],
        include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False, "presets": False, "downloads": False, "outputs": False},
        mode="move",
        conflict="skip_existing",
        delete_source_duplicates=True,
        parallel_file_transfers=True,
        file_transfer_workers=4,
        fast_same_volume_moves=True,
    )
    assert any(op.get("action") == "delete_duplicate_group_source" for op in result["files"])
    assert not src_group.exists()
    assert dst_group.exists()
    assert result["deleted_source_duplicates"] >= 4


def test_migration_router_no_longer_compresses_file_stage_to_75_percent():
    router = (ROOT / "data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    assert "0.02 + 0.88 * local" in router
    assert "0.02 + 0.73 * local" not in router
    assert "Reloading migrated custom model catalog" in router
    assert "progress(0.91" in router

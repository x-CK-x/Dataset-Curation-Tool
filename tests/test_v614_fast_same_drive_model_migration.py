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


def test_migration_fast_same_volume_moves_default_enabled():
    settings = AppSettings()
    assert settings.migration_fast_same_volume_moves is True


def test_move_mode_uses_fast_rename_not_byte_copy_for_same_volume_models(tmp_path: Path):
    old = tmp_path / "old"
    model_dir = old / "models" / "hf" / "Huge--Model"
    model_dir.mkdir(parents=True)
    src = model_dir / "model-00001-of-00002.safetensors"
    src.write_bytes(b"large-model-shard" * 4096)
    (model_dir / "config.json").write_text('{"model_type":"test"}', encoding="utf-8")

    current = tmp_path / "current"
    service = InstallMigrationService(make_paths(current), app_settings=AppSettings())

    def fail_copy(*args, **kwargs):  # pragma: no cover - should never be called in fast path
        raise AssertionError("Move mode should not copy bytes when fast same-volume moves are enabled")

    service._copy_file_with_progress = fail_copy  # type: ignore[method-assign]
    progress_rows: list[tuple[float, str]] = []
    result = service.migrate(
        [old],
        include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False, "presets": False, "downloads": False, "outputs": False},
        mode="move",
        conflict="skip_existing",
        parallel_file_transfers=False,
        fast_same_volume_moves=True,
        progress=lambda value, message="": progress_rows.append((float(value), str(message))),
    )

    target = current / "models" / "hf" / "Huge--Model" / "model-00001-of-00002.safetensors"
    assert target.exists()
    assert not src.exists()
    assert result["moved"] >= 2
    assert result["fast_same_volume_moves"] is True
    assert any((row.get("action") in {"move_fast", "move_dir_fast"}) for row in result["files"])


def test_migration_schema_router_and_ui_expose_fast_same_drive_moves():
    schemas = (ROOT / "data_curation_tool/schemas.py").read_text(encoding="utf-8")
    router = (ROOT / "data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    app = (ROOT / "data_curation_tool/app.py").read_text(encoding="utf-8")
    app_js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "fast_same_volume_moves: bool = True" in schemas
    assert "migration_fast_same_volume_moves" in router
    assert "fast_same_volume_moves=payload.fast_same_volume_moves" in router
    assert "fast_same_volume_moves=bool(getattr(c.settings" in app
    assert "Fast same-drive moves" in app_js
    assert "fast_same_volume_moves" in app_js

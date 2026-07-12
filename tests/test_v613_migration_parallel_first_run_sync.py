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


def test_migration_parallel_defaults_are_enabled():
    settings = AppSettings()
    assert settings.migration_parallel_file_transfers is True
    assert settings.migration_file_transfer_workers == 4
    assert settings.tag_db_sync_if_empty_only is False


def test_parallel_migration_copies_with_multiple_workers(tmp_path: Path):
    old = tmp_path / "old"
    model_dir = old / "models" / "hf" / "Parallel--Model"
    model_dir.mkdir(parents=True)
    for idx in range(6):
        (model_dir / f"shard-{idx}.safetensors").write_bytes((f"payload-{idx}".encode()) * 2048)
    current = tmp_path / "current"
    service = InstallMigrationService(make_paths(current), app_settings=AppSettings())
    progress_rows: list[tuple[float, str]] = []
    result = service.migrate(
        [old],
        include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False, "presets": False, "downloads": False, "outputs": False},
        mode="copy",
        conflict="replace",
        parallel_file_transfers=True,
        file_transfer_workers=4,
        progress=lambda v, m="": progress_rows.append((float(v), str(m))),
    )
    assert result["parallel_file_transfers"] is True
    assert result["file_transfer_workers"] == 4
    assert result["copied"] >= 6
    assert (current / "models" / "hf" / "Parallel--Model" / "shard-5.safetensors").exists()
    assert any("parallel" in message.lower() for _, message in progress_rows)


def test_schema_and_router_expose_parallel_migration_fields():
    schemas = (ROOT / "data_curation_tool/schemas.py").read_text(encoding="utf-8")
    router = (ROOT / "data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    app = (ROOT / "data_curation_tool/app.py").read_text(encoding="utf-8")
    assert "parallel_file_transfers: bool = True" in schemas
    assert "file_transfer_workers: int = Field(default=4" in schemas
    assert "migration_parallel_file_transfers" in router
    assert "parallel_file_transfers=payload.parallel_file_transfers" in router
    assert "parallel_file_transfers=bool(getattr(c.settings" in app


def test_first_run_startup_sync_bypasses_weekly_gate_when_dictionary_empty():
    app = (ROOT / "data_curation_tool/app.py").read_text(encoding="utf-8")
    assert "first_run_missing" in app
    assert "total_rows <= 0" in app
    assert "force_download=bool(first_run_missing)" in app
    assert "use Sync Now to force an update" in app


def test_ui_exposes_parallel_migration_and_manual_sync_button():
    app_js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Parallelize file transfers" in app_js
    assert "transfer workers" in app_js
    assert "parallel_file_transfers" in app_js
    assert "Update Tag Dictionary Now" in app_js
    assert "Update Now / Force Refresh" in app_js
    assert "force_download: true" in app_js

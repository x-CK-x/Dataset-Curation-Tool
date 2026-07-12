from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from data_curation_tool import __version__
from data_curation_tool.services.install_migration_service import InstallMigrationService

ROOT = Path(__file__).resolve().parents[1]


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"


def test_dashboard_has_manual_refresh_and_uncached_startup_status():
    app_js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    system_py = (ROOT / "data_curation_tool/routers/system.py").read_text(encoding="utf-8")
    assert "Refresh Dashboard Now" in app_js
    assert "refreshDashboardOnly" in app_js
    assert "refreshStartupStatus({ force: true" in app_js
    assert "Cache-Control" in app_js and "no-store" in app_js
    assert "response.headers[\"Cache-Control\"] = \"no-store" in system_py


def test_manual_migration_sets_optimistic_startup_progress_and_polls_asset_jobs():
    app_js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    migration_py = (ROOT / "data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    assert "phase: 'startup_migration'" in app_js
    assert "Asset migration'} job #" in app_js
    assert "['asset_migration','startup_initialization','tag_dictionary_sync','db_export_sync']" in app_js
    assert "Migration-triggered maintenance started: waiting for migration worker" in migration_py


def test_migration_service_emits_live_progress_during_copy_and_tag_import(tmp_path: Path):
    old_root = tmp_path / "old"
    old_models = old_root / "models" / "hf" / "Example--Model"
    old_models.mkdir(parents=True)
    src = old_models / "model.safetensors"
    src.write_bytes(b"x" * (1024 * 1024 + 7))

    current_root = tmp_path / "current"
    models = current_root / "models"
    runtime = current_root / "runtime"
    outputs = current_root / "outputs"
    for path in (models, runtime, outputs):
        path.mkdir(parents=True, exist_ok=True)
    service = InstallMigrationService(SimpleNamespace(root=current_root, models=models, runtime=runtime, outputs=outputs))
    progress_rows: list[tuple[float, str]] = []
    result = service.migrate(
        [old_root],
        include={"models": True, "tag_exports": False, "tag_database": False, "custom_tags": False, "custom_models": False, "presets": False, "downloads": False, "outputs": False},
        mode="copy",
        conflict="replace",
        progress=lambda value, message="": progress_rows.append((float(value), str(message))),
    )
    assert result["copied"] >= 1
    assert (models / "hf" / "Example--Model" / "model.safetensors").exists()
    assert any("Scanning previous installs" in message or "Migration plan prepared" in message for _, message in progress_rows)
    assert any("Copy Models" in message or "Copy models" in message or "Copy Model" in message for _, message in progress_rows)
    assert progress_rows[-1][0] == 1.0


def test_import_tag_database_accepts_progress_callback():
    text = (ROOT / "data_curation_tool/services/install_migration_service.py").read_text(encoding="utf-8")
    assert "def import_tag_database(self, old_db_path" in text
    assert "progress: ProgressCallback | None = None" in text
    assert "Importing migrated tag table" in text
    assert "copied {min(source_count, chunk_index * chunk_size):,}/{source_count:,} row(s)" in text
    assert "_copy_file_with_progress" in text

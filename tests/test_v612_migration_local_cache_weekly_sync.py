from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from data_curation_tool import __version__
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService

ROOT = Path(__file__).resolve().parents[1]


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths(
        root=tmp_path,
        runtime=tmp_path / "runtime",
        models=tmp_path / "models",
        outputs=tmp_path / "outputs",
        database=tmp_path / "runtime" / "app.db",
        settings=tmp_path / "runtime" / "settings.json",
        thumbnails=tmp_path / "runtime" / "thumbnails",
        presets=tmp_path / "runtime" / "presets",
        downloads=tmp_path / "runtime" / "downloads",
        exports=tmp_path / "runtime" / "exports",
    )


def test_version_bumped_to_5_8_25() -> None:
    assert __version__ == "5.8.48"


def test_defaults_use_weekly_startup_sync_and_local_only_migration() -> None:
    s = AppSettings()
    assert s.tag_db_export_cache_hours == 168
    assert s.tag_db_startup_sync_interval_hours == 168
    assert s.migration_skip_post_online_tag_sync is True
    assert s.migration_local_only_existing_assets is True


def test_startup_sync_recently_checked_gate(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    paths.ensure()
    db = Database(paths.database)
    tags = TagService(db, paths)
    assert tags.startup_sync_recently_checked("danbooru", 168) is False
    tags.mark_startup_sync_checked("danbooru", status="checked")
    assert tags.startup_sync_recently_checked("danbooru", 168) is True
    assert tags.startup_sync_recently_checked("danbooru", 0) is True


def test_cached_exports_can_import_without_network(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    paths.ensure()
    db = Database(paths.database)
    tags = TagService(db, paths)
    cache_dir = paths.runtime / "tag_exports" / "danbooru"
    cache_dir.mkdir(parents=True)
    (cache_dir / "tags.csv").write_text(
        "id,name,category,post_count\n1,blue_eyes,0,12\n2,red_hair,0,5\n",
        encoding="utf-8",
    )
    result = tags.import_cached_exports("danbooru", replace_existing=True)
    assert result["source"] == "local-cache"
    assert result["imported"] >= 2
    assert db.query_one("SELECT 1 FROM tag_dictionary_entries WHERE source=? AND tag=?", ("danbooru", "blue_eyes"))
    assert "local-cache" in (result["files"][0].get("source") or result["files"][0].get("url", ""))


def test_migration_router_skips_post_migration_internet_refresh_by_default() -> None:
    migration_py = (ROOT / "data_curation_tool" / "routers" / "migration.py").read_text(encoding="utf-8")
    schemas_py = (ROOT / "data_curation_tool" / "schemas.py").read_text(encoding="utf-8")
    app_py = (ROOT / "data_curation_tool" / "app.py").read_text(encoding="utf-8")
    assert "skip_internet_refresh: bool = True" in schemas_py
    assert "local-only migration mode reused migrated tag exports/database rows and did not use the network" in migration_py
    assert "import_cached_exports" in migration_py
    assert "startup network sync already checked within" in app_py
    assert "tag_db_startup_sync_interval_hours" in app_py


def test_ui_exposes_local_only_migration_and_weekly_sync_controls() -> None:
    app_js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Local-only migration: do NOT download internet refreshes after migration" in app_js
    assert "skip_internet_refresh" in app_js
    assert "Startup network check interval hours, default 168" in app_js
    assert "The app should not download tag dictionaries on every launch" in app_js

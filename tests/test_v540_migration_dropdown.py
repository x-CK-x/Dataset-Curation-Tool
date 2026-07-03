from __future__ import annotations

import os
from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.install_migration_service import InstallMigrationService
from data_curation_tool.services.tag_service import TagService


def _touch(path: Path, text: str, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_migration_moves_newest_first_then_older_unique(tmp_path, monkeypatch):
    current = tmp_path / "current"
    previous_old = tmp_path / "old_install"
    previous_new = tmp_path / "newer_install"
    current.mkdir()
    previous_old.mkdir()
    previous_new.mkdir()
    monkeypatch.chdir(current)
    paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")
    service = InstallMigrationService(paths)

    _touch(previous_old / "models" / "hf" / "repo" / "weights.safetensors", "older duplicate", 100)
    _touch(previous_old / "models" / "hf" / "repo" / "old-only.safetensors", "old unique", 100)
    _touch(previous_new / "models" / "hf" / "repo" / "weights.safetensors", "new duplicate", 200)
    _touch(previous_new / "runtime" / "tag_exports" / "e621" / "tags-2026-01-02.csv.gz", "tags-new", 200)
    _touch(previous_old / "runtime" / "tag_exports" / "e621" / "tag_aliases-2025-12-01.csv.gz", "aliases-old", 100)

    result = service.migrate(
        [str(previous_old), str(previous_new)],
        include={"models": True, "tag_exports": True, "tag_database": False, "custom_tags": False},
        mode="move",
        conflict="skip_existing",
        newest_first=True,
    )

    assert result["errors"] == []
    assert (current / "models" / "hf" / "repo" / "weights.safetensors").read_text(encoding="utf-8") == "new duplicate"
    assert (current / "models" / "hf" / "repo" / "old-only.safetensors").read_text(encoding="utf-8") == "old unique"
    assert (current / "runtime" / "tag_exports" / "e621" / "tags-2026-01-02.csv.gz").exists()
    assert (current / "runtime" / "tag_exports" / "e621" / "tag_aliases-2025-12-01.csv.gz").exists()
    assert not (previous_new / "models" / "hf" / "repo" / "weights.safetensors").exists()
    assert not (previous_old / "models" / "hf" / "repo" / "old-only.safetensors").exists()
    # Older conflicting file is intentionally left in place because the newer install won the target path.
    assert (previous_old / "models" / "hf" / "repo" / "weights.safetensors").exists()


def test_migration_imports_prior_tag_database_rows(tmp_path, monkeypatch):
    current = tmp_path / "current"
    previous = tmp_path / "previous"
    current.mkdir()
    previous.mkdir()

    monkeypatch.chdir(current)
    current_paths = AppPaths.create(runtime=current / "runtime", models=current / "models", outputs=current / "outputs")
    current_db = Database(current_paths.database)
    current_tags = TagService(current_db, current_paths)

    old_paths = AppPaths(root=previous, runtime=previous / "runtime", models=previous / "models", outputs=previous / "outputs", database=previous / "runtime" / "app.db", settings=previous / "runtime" / "settings.json", thumbnails=previous / "runtime" / "thumbnails", presets=previous / "runtime" / "presets", downloads=previous / "runtime" / "downloads", exports=previous / "runtime" / "exports")
    old_paths.ensure()
    old_db = Database(old_paths.database)
    TagService(old_db, old_paths)
    old_db.execute(
        """INSERT OR REPLACE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
           VALUES (?, ?, ?, ?, '[]', '[]', 0, ?)""",
        ("e621", "prior_unique_tag", "general", 123, "2026-01-01T00:00:00+00:00"),
    )
    old_db.execute(
        """INSERT OR REPLACE INTO tag_dictionary_search(source, tag, tag_lower, category, post_count, is_custom, updated_at)
           VALUES (?, ?, ?, ?, ?, 0, ?)""",
        ("e621", "prior_unique_tag", "prior_unique_tag", "general", 123, "2026-01-01T00:00:00+00:00"),
    )

    service = InstallMigrationService(current_paths, current_db, current_tags)
    result = service.migrate([str(previous)], include={"tag_database": True, "models": False, "tag_exports": False, "custom_tags": False}, mode="copy")

    assert result["errors"] == []
    assert result["tag_database"][0]["tables"]["tag_dictionary_entries"]["inserted"] == 1
    row = current_db.query_one("SELECT category, post_count FROM tag_dictionary_entries WHERE source=? AND tag=?", ("e621", "prior_unique_tag"))
    assert row == {"category": "general", "post_count": 123}


def test_frontend_defers_poll_rerenders_for_select_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function isSelectEditingElement" in app_js
    assert "shouldDeferControlRender()" in app_js
    assert "renderOrDeferForEditing" in app_js
    assert "SELECT" in app_js
    assert "Install Migration" in app_js

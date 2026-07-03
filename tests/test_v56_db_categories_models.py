from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.dataset_service import DatasetService
from data_curation_tool.services.tag_service import TagService
from data_curation_tool.schemas import DatasetCreate
from data_curation_tool.models.registry import ModelRegistry


def _paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_two_week_stale_export_status_and_custom_category_priority(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, _paths(tmp_path))
    tag_csv = tmp_path / "tags.csv"
    tag_csv.write_text("id,name,category,post_count\n1,alice,4,20\n2,blue_hair,0,100\n", encoding="utf-8")
    assert tags.import_dictionary_csv(tag_csv, "e621") == 2
    old = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
    db.execute(
        "INSERT OR REPLACE INTO tag_export_files(profile_key, role, url, local_path, sha256, downloaded_at, imported_at, row_count, status, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("e621", "tags", "https://e621.net/db_exports/tags.csv.gz", str(tag_csv), "abc", old, old, 2, "imported", ""),
    )
    assert tags.should_auto_sync_default_export("e621", empty_only=False, cache_hours=336) is True
    tags.add_custom_tag("e621", "alice", "style", color="#ff00aa")
    assert tags.metadata(["alice"], "e621")["alice"]["category"] == "style"
    assert tags.categorize("alice", "e621") == "style"


def test_txt_only_import_uses_active_profile_and_reapply_categories(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    img = root / "sample.png"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(img)
    img.with_suffix(".txt").write_text("alice, blue_hair", encoding="utf-8")
    db = Database(tmp_path / "app.sqlite3")
    paths = _paths(tmp_path)
    tags = TagService(db, paths)
    tag_csv = tmp_path / "tags.csv"
    tag_csv.write_text("id,name,category,post_count\n1,alice,4,20\n2,blue_hair,0,100\n", encoding="utf-8")
    tags.import_dictionary_csv(tag_csv, "e621")
    service = DatasetService(db, MediaService(db, paths), tags, import_workers=1)
    result = service.import_folder(DatasetCreate(root_path=str(root), auto_sync_tag_dictionary=False, tag_profile="e621"))
    media_id = db.query_one("SELECT id FROM media")["id"]
    cats = tags.get_categories(media_id)
    assert cats["alice"] == "character"
    assert cats["blue_hair"] == "general"
    tags.add_custom_tag("e621", "alice", "style")
    reapplied = tags.reapply_categories([media_id], profile_key="e621")
    assert reapplied["changed"] == 1
    assert tags.get_categories(media_id)["alice"] == "style"


def test_v56_model_catalog_contains_recent_and_repo_feature_rows(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    names = {m["name"] for m in registry.list()}
    assert "pixai-tagger-v09" in names
    assert "granite-vision-3.3-2b" in names
    assert "paddleocr-vl-1.6" in names
    assert "joycaption-adapter" in names
    assert "clean-tags-llm-pruner" in names
    assert "model-builder-classifier-contract" in names


def test_v56_hud_contains_custom_category_editor_and_tag_editor_queue_controls():
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Global Custom Category / Color Overrides" in js
    assert "Apply Overrides to Gallery/Selection" in js
    assert "selectedEditorItems" in js
    assert "Next ▶" in js
    assert "Reapply Profile/Custom Categories" in js

from __future__ import annotations

from pathlib import Path

from PIL import Image
from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.dataset_service import DatasetService
from data_curation_tool.schemas import DatasetCreate


def test_db_export_import_parses_tags_aliases_and_implications(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    tags = TagService(db, AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs"))
    tag_csv = tmp_path / "tags.csv"
    tag_csv.write_text("id,name,category,post_count\n1,blue_hair,0,100\n2,alice,4,20\n", encoding="utf-8")
    alias_csv = tmp_path / "tag_aliases.csv"
    alias_csv.write_text("antecedent_name,consequent_name\nblu_hair,blue_hair\n", encoding="utf-8")
    implication_csv = tmp_path / "tag_implications.csv"
    implication_csv.write_text("antecedent_name,consequent_name\nalice,1girl\n", encoding="utf-8")

    assert tags.import_dictionary_csv(tag_csv, "e621") == 2
    assert tags.import_aliases_csv(alias_csv, "e621") == 1
    assert tags.import_implications_csv(implication_csv, "e621") == 1
    meta = tags.metadata(["blue_hair", "alice", "blu_hair"], "e621")
    assert meta["blue_hair"]["category"] == "general"
    assert meta["alice"]["category"] == "character"
    assert meta["blu_hair"]["category"] == "invalid"
    assert tags.should_auto_sync_default_export("e621", empty_only=True) is False


def test_parallel_import_reports_workers_and_reads_txt_sidecars(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    for idx in range(4):
        img = root / f"image_{idx}.png"
        Image.new("RGB", (8, 8), (idx * 20, 0, 0)).save(img)
        img.with_suffix(".txt").write_text(f"tag_{idx}, shared_tag", encoding="utf-8")
    db = Database(tmp_path / "app.sqlite3")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    tag_service = TagService(db, paths)
    service = DatasetService(db, MediaService(db, paths), tag_service, import_workers=2)
    result = service.import_folder(DatasetCreate(root_path=str(root), auto_sync_tag_dictionary=False, import_workers=2))
    assert result["imported"] == 4
    assert result["workers"] == 2
    rows = db.query("SELECT COUNT(*) AS n FROM tags WHERE tag='shared_tag'")
    assert rows[0]["n"] == 4


def test_models_endpoint_exposes_download_metadata_and_hud_controls(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "1")
    app = create_app(AppPaths.create(tmp_path))
    client = TestClient(app)
    models = client.get("/api/models").json()
    assert any(m["name"] == "vit-image-classifier" and m["download_supported"] and m["size_gb"] for m in models)
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Download / Install Models" in js
    assert "Parallel import workers" in js
    assert "Auto-sync selected booru tag DB" in js

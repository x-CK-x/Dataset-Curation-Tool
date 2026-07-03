import csv
import gzip
from pathlib import Path

from PIL import Image

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DatasetCreate
from data_curation_tool.services.dataset_service import DatasetService
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.tag_service import TagService


def test_v58_fast_dictionary_import_and_pair_exports(tmp_path: Path):
    db = Database(tmp_path / "tags.db")
    tags = TagService(db, None)
    export = tmp_path / "tags.csv.gz"
    with gzip.open(export, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "category", "post_count"])
        writer.writerow([1, "alpha", 4, 100])
        writer.writerow([2, "beta", 1, 50])
        writer.writerow([3, "zero_count", 0, 0])
    imported = tags.import_dictionary_csv(export, "e621", replace_existing=True)
    assert imported == 3
    meta = tags.metadata(["alpha", "zero_count"], "e621")
    assert meta["alpha"]["category"] == "character"
    assert meta["zero_count"]["known"] is True
    assert db.query_one("SELECT COUNT(*) AS n FROM tag_dictionary_search WHERE source='e621'")["n"] == 3

    aliases = tmp_path / "tag_aliases.csv.gz"
    with gzip.open(aliases, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["antecedent_name", "consequent_name", "status"])
        writer.writerow(["old_alpha", "alpha", "active"])
    assert tags.import_aliases_csv(aliases, "e621") == 1
    assert db.query_one("SELECT COUNT(*) AS n FROM tag_aliases WHERE source='e621'")["n"] == 1

    implications = tmp_path / "tag_implications.csv.gz"
    with gzip.open(implications, "wt", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["antecedent_name", "consequent_name", "status"])
        writer.writerow(["alpha", "person", "active"])
    assert tags.import_implications_csv(implications, "e621") == 1
    assert db.query_one("SELECT COUNT(*) AS n FROM tag_implications WHERE source='e621'")["n"] == 1


def test_v58_dataset_import_uses_bulk_paths_and_fast_options(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    for idx in range(5):
        Image.new("RGB", (8, 8), (idx, 0, 0)).save(root / f"{idx}.png")
        (root / f"{idx}.txt").write_text("alpha, beta", encoding="utf-8")
    db = Database(tmp_path / "media.db")
    tag_service = TagService(db, None)
    media_service = MediaService(db, AppPaths.create(tmp_path / "app"))
    dataset_service = DatasetService(db, media_service, tag_service, metadata_extract_on_import=False)
    req = DatasetCreate(
        root_path=str(root),
        auto_sync_tag_dictionary=False,
        read_sidecars=True,
        skip_duplicates=False,
        compute_sha256=False,
        compute_phash=False,
        probe_dimensions=False,
        find_near_duplicates=False,
        read_embedded_metadata=False,
        import_workers=2,
        import_commit_batch_size=3,
    )
    result = dataset_service.import_folder(req)
    assert result["imported"] == 5
    assert result["compute_sha256"] is False
    assert result["probe_dimensions"] is False
    assert result["find_near_duplicates"] is False
    assert db.query_one("SELECT COUNT(*) AS n FROM media")["n"] == 5
    assert db.query_one("SELECT COUNT(*) AS n FROM tags")["n"] == 10

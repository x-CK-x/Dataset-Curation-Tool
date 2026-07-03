from pathlib import Path

from PIL import Image

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.dataset_service import DatasetService
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.tag_service import TagService
from data_curation_tool.schemas import DatasetCreate


def test_dataset_import_reads_sidecars(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    img = root / "sample_image.png"
    Image.new("RGB", (32, 24), "white").save(img)
    img.with_suffix(".txt").write_text("alpha, beta", encoding="utf-8")
    img.with_suffix(".caption").write_text("a white test image", encoding="utf-8")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db)
    media = MediaService(db, paths)
    datasets = DatasetService(db, media, tags)
    result = datasets.import_folder(DatasetCreate(root_path=str(root)), progress=lambda p, m: None)
    assert result["imported"] == 1
    page = media.page(dataset_id=result["dataset_id"])
    assert page.total == 1
    assert page.items[0].tags == ["alpha", "beta"]
    assert page.items[0].caption == "a white test image"

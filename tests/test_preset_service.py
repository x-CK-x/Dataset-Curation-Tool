from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.services.preset_service import PresetService


def test_import_text_preset_sections(tmp_path: Path):
    svc = PresetService(Database(tmp_path / "test.db"), tmp_path / "presets")
    names = svc.import_text("name: first\npositive: red blue\nnegative: blurry\n;;;\nname: second\ngreen")
    assert names == ["first", "second"]
    presets = {p["name"]: p for p in svc.list()}
    assert presets["first"]["positive_tags"] == ["red", "blue"]
    assert presets["first"]["negative_tags"] == ["blurry"]

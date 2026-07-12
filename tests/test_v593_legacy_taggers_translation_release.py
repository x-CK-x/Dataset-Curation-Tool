from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from data_curation_tool import __version__
from data_curation_tool.database import Database, now_iso
from data_curation_tool.models.adapters import LegacyVisionTaggerAdapter
from data_curation_tool.models.legacy_tagger_configs import LEGACY_TAGGER_CONFIGS
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def _paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def _tag_service(tmp_path: Path) -> TagService:
    paths = _paths(tmp_path)
    db = Database(paths.database)
    return TagService(db, paths)


def test_release_version_is_5_8_2() -> None:
    assert __version__ == "5.8.48"


def test_registry_exposes_legacy_local_tagger_rows(tmp_path: Path) -> None:
    registry = ModelRegistry(_paths(tmp_path).models)
    rows = {row["name"]: row for row in registry.list()}
    expected = {
        "legacy-eva02-clip-vit-large-7704": "huggingface",
        "legacy-eva02-vit-large-448-8046": "huggingface",
        "legacy-efficientnetv2-m-8035": "huggingface",
    }
    for name, provider in expected.items():
        row = rows[name]
        assert row["kind"] == "tagger"
        assert row["provider"] == provider
        assert row["download_supported"] is True
        for cap in ["tag", "auto_tag", "legacy_model_config", "tag_editor", "compare", "tag_translation_ready"]:
            assert cap in row["capabilities"]
        assert "onnxruntime" in row["requirements"]


def test_legacy_tagger_adapter_loads_json_and_csv_tag_metadata(tmp_path: Path) -> None:
    json_tags = tmp_path / "tags.json"
    json_tags.write_text('{"zebra": 0, "blue eyes": 1}', encoding="utf-8")
    cfg = dict(LEGACY_TAGGER_CONFIGS["thouph-eva02-clip-vit-large-7704"])
    cfg.update({"output_layer_size": 5, "extend_output_dims": ["placeholder0"], "extend_output_dims_pos": [-1]})
    adapter = LegacyVisionTaggerAdapter("test", "Test", cfg)
    loaded = adapter._load_tags(json_tags)
    assert loaded[:2] == ["blue_eyes", "zebra"]
    assert len(loaded) == 5

    csv_tags = tmp_path / "tags.csv"
    csv_tags.write_text("id,name\n1,red hair\n2,solo\n", encoding="utf-8")
    cfg = dict(LEGACY_TAGGER_CONFIGS["thouph-eva02-clip-vit-large-7704"])
    cfg.update({"output_layer_size": 2, "use_extend_output_dims": False, "use_column_number": 1, "tags_csv_format": True})
    adapter = LegacyVisionTaggerAdapter("csv", "CSV", cfg)
    assert adapter._load_tags(csv_tags) == ["red_hair", "solo"]


def test_tag_format_translation_and_model_tag_postprocessing(tmp_path: Path) -> None:
    svc = _tag_service(tmp_path)
    now = now_iso()
    svc.db.execute(
        """INSERT OR REPLACE INTO tag_dictionary_entries(source, tag, category, post_count, aliases_json, implications_json, is_custom, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("danbooru", "blue_eyes", "general", 10, "[]", "[]", 0, now),
    )
    svc.db.execute(
        """INSERT OR REPLACE INTO tag_aliases(source, alias, target, status, updated_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("e621", "azure_eyes", "blue_eyes", "active", now),
    )
    svc.db.execute(
        """INSERT OR REPLACE INTO tag_implications(source, antecedent, consequent, updated_at)
           VALUES (?, ?, ?, ?)""",
        ("e621", "blue_eyes", "eyes", now),
    )

    request = SimpleNamespace(
        tags=[],
        tag_string="azure eyes, custom concept",
        source_profile_key="e621",
        target_profile_key="danbooru",
        output_format="comma_caption",
        preserve_unknown=True,
        dry_run=True,
        include_prompt=True,
    )
    translated = svc.translate_format(request)
    assert translated["source_tags"] == ["azure_eyes", "custom_concept"]
    assert "blue_eyes" in translated["translated_tags"]
    assert "custom_concept" in translated["unknown_tags"]
    assert "model_prompt" in translated

    postprocessed = svc.postprocess_model_tags(["azure eyes"], profile_key="e621", apply_aliases=True, apply_implications=True)
    assert postprocessed == ["blue_eyes", "eyes"]


def test_frontend_exposes_tag_caption_translation_controls() -> None:
    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "/api/tags/translate-format" in text
    assert "Tag / Caption Format Translator" in text
    assert "legacy EVA/EfficientNet" in text

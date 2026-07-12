from __future__ import annotations

from pathlib import Path

from PIL import Image

from data_curation_tool.models.adapters import LegacyVisionTaggerAdapter, LingBotVideoAdapter
from data_curation_tool.models.legacy_tagger_configs import legacy_tagger_config
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.database import Database
from data_curation_tool.services.multimodal_dataset_service import MultimodalDatasetService
from data_curation_tool.paths import AppPaths


APP_JS = Path("data_curation_tool/static/app.js")


def test_thouph_preprocess_contracts_are_model_specific() -> None:
    clip = legacy_tagger_config("thouph-eva02-clip-vit-large-7704")
    eva = legacy_tagger_config("thouph-eva02-vit-large-448-8046")
    eff = legacy_tagger_config("thouph-experimental-efficientnetv2-m-8035")

    assert clip["resize_mode"] == "thouph_clip_aspect_bicubic"
    assert clip["interpolation"] == "bicubic"
    assert eva["resize_mode"] == "resize_exact"
    assert eva["interpolation"] == "bilinear"
    assert eff["resize_mode"] == "thouph_effnet_area_512"
    assert eff["torch_allows_dynamic_spatial"] is True
    assert eff["onnx_resize_mode"] == "resize_exact"


def test_efficientnet_pytorch_preprocess_keeps_thouph_dynamic_thumbnail(tmp_path: Path) -> None:
    image = tmp_path / "wide.png"
    Image.new("RGB", (2048, 512), (128, 64, 32)).save(image)
    cfg = legacy_tagger_config("thouph-experimental-efficientnetv2-m-8035")
    arr = LegacyVisionTaggerAdapter("eff", "eff", cfg)._preprocess_pil(image)

    # Thouph's PyTorch EfficientNet helper uses a 512-area thumbnail box, so a
    # 4:1 image becomes 1024x256 before CHW batching rather than forced 448x448.
    assert arr.shape == (1, 3, 256, 1024)


def test_eva02_clip_extreme_aspect_preprocess_uses_short_edge_crop(tmp_path: Path) -> None:
    image = tmp_path / "tall.png"
    Image.new("RGB", (100, 500), (16, 32, 48)).save(image)
    cfg = legacy_tagger_config("thouph-eva02-clip-vit-large-7704")
    arr = LegacyVisionTaggerAdapter("clip", "clip", cfg)._preprocess_pil(image)
    assert arr.shape == (1, 3, 224, 224)


def test_graph_editor_dropdown_scroll_and_prediction_sort_markers_exist() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function graphEditorLocalPresets" in text
    assert "function graphEditorSaveLocalPreset" in text
    assert "hardForce = force === 'hard'" in text
    assert "shouldDeferControlRender()" in text
    assert "models-download-catalog-scroll" in text
    assert "sortDraftTagsByPredictionMetric" in text
    assert "average_prediction_desc" in text
    assert "specific_model_prediction_desc" in text
    assert "detected_model_count_desc" in text
    assert "stddev_asc" in text
    assert "median_prediction_desc" in text
    assert "mode_prediction_desc" in text


def test_lingbot_world_model_rows_are_in_registry(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path / "models")
    names = {row["name"] for row in registry.list()}
    assert "lingbot-video-dense-1-3b" in names
    assert "lingbot-video-moe-30b-a3b" in names
    assert "lingbot-video-rewriter-base-qwen36-27b" in names
    assert "lingbot-video-rewriter-lora" in names
    moe = registry.get_record("lingbot-video-moe-30b-a3b")
    assert moe.supports_sharding is True
    assert moe.min_gpus >= 2
    assert isinstance(moe.adapter, LingBotVideoAdapter)


def test_multimodal_voice_profiles_and_av_sync_schema(tmp_path: Path) -> None:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    service = MultimodalDatasetService(db, paths)
    catalog = service.catalog()
    assert catalog["voice_dataset_scope"]["tracked_fields"]
    assert "audio_stt_dataset" in {p["key"] for p in catalog["task_profiles"]}
    assert "voice_consent_manifest" in {p["key"] for p in catalog["export_profiles"]}

    profile = service.save_voice_profile({"display_name": "consented narrator", "consent_status": "documented", "allowed_use": "local research"})
    assert profile["consent_status"] == "documented"
    assert service.voice_profile(profile["id"])["allowed_use"] == "local research"

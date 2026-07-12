from __future__ import annotations

from pathlib import Path

from PIL import Image

from data_curation_tool import __version__
from data_curation_tool.models.adapters import LegacyVisionTaggerAdapter
from data_curation_tool.models.legacy_tagger_configs import legacy_tagger_config

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_5_8_15() -> None:
    assert __version__ == "5.8.48"


def test_legacy_efficientnet_pytorch_preprocess_matches_thouph_dynamic_thumbnail(tmp_path: Path) -> None:
    cfg = legacy_tagger_config("thouph-experimental-efficientnetv2-m-8035")
    adapter = LegacyVisionTaggerAdapter("legacy-efficientnetv2-m-8035", cfg["label"], cfg)
    image = tmp_path / "wide.png"
    Image.new("RGB", (552, 473), (128, 90, 40)).save(image)
    tensor = adapter._preprocess_pil(image)
    assert tensor.shape == (1, 3, 473, 552)


def test_legacy_eva_pickle_compat_adds_missing_nullable_tokens() -> None:
    class Eva:
        __module__ = "timm.models.eva"
        def modules(self):
            return [self]
    cfg = legacy_tagger_config("thouph-eva02-vit-large-448-8046")
    adapter = LegacyVisionTaggerAdapter("legacy-eva02-vit-large-448-8046", cfg["label"], cfg)
    model = Eva()
    assert not hasattr(model, "reg_token")
    assert not hasattr(model, "mask_token")
    adapter._patch_torch_model_compat(model)
    assert hasattr(model, "reg_token")
    assert model.reg_token is None
    assert hasattr(model, "mask_token")
    assert model.mask_token is None


def test_scroll_restore_is_tokenized_and_short_lived_not_erratic() -> None:
    js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "state.scrollRestoreToken" in js
    assert "const quietWindow = aggressive ? 650 : 140" in js
    assert "setTimeout(apply, 1200)" not in js
    assert "setTimeout(() => { apply(); state.scrollRestoringUntil = 0; }, 2200)" not in js
    assert "cancelScrollRestoreFromUserInput" in js

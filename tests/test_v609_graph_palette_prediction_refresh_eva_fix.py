from __future__ import annotations

import json
from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.models.adapters import LegacyVisionTaggerAdapter
from data_curation_tool.services.graph_editor_service import GRAPH_NODE_PALETTE


ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")


class _FakeEva:
    __module__ = "timm.models.eva"

    def modules(self):
        return [self]


def test_release_version_is_5_8_16():
    assert __version__ == "5.8.48"
    assert 'version = "5.8.48"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_legacy_eva_nullable_attributes_are_patched():
    adapter = LegacyVisionTaggerAdapter("legacy-eva02-vit-large-448-8046", "Legacy EVA", {"source_name": "eva02-vit-large-448-8046"})
    model = _FakeEva()
    adapter._patch_torch_model_compat(model)
    assert model.reg_token is None
    assert model.mask_token is None
    assert model.no_embed_class is False
    assert model.dynamic_img_size is False
    assert model.dynamic_img_pad is False
    assert model.strict_img_size is True
    assert model.patch_drop is None


def test_graph_palette_exposes_standalone_node_customization_contracts():
    by_kind = {row["kind"]: row for row in GRAPH_NODE_PALETTE}
    assert by_kind["model_call"]["standalone_type"] == "MODEL"
    assert by_kind["bundle_context"]["standalone_type"] == "BUNDLE"
    assert by_kind["supervisor_controller"]["standalone_type"] == "SUPERVISOR"
    model_fields = {field["key"] for field in by_kind["model_call"]["customization_fields"]}
    assert {"model_ref_id", "user_prompt", "input_modalities", "output_modalities"} <= model_fields
    bundle_fields = {field["key"] for field in by_kind["bundle_context"]["customization_fields"]}
    assert {"max_items", "max_chars", "policy", "text_only"} <= bundle_fields
    supervisor_fields = {field["key"] for field in by_kind["supervisor_controller"]["customization_fields"]}
    assert {"controller_model_ref_id", "max_spawns", "channels"} <= supervisor_fields


def test_frontend_has_palette_driven_editor_and_prediction_refresh_watcher():
    assert "Graph Node Palette / Standalone Node Contracts" in APP_JS
    assert "graphEditorPaletteCustomizationInspector" in APP_JS
    assert "graphEditorPaletteFieldControl" in APP_JS
    assert "customization_schema" in APP_JS
    assert "watchModelInferenceJob" in APP_JS
    assert "modelInferenceJobWatchers" in APP_JS
    assert "refreshMediaAfterCompletedModelJobs" in APP_JS
    assert "Always refresh the media rows after model inference" in APP_JS


def test_frontend_uses_scroll_holds_and_unique_model_hues():
    assert "scrollActiveUntil" in APP_JS
    assert "Never replace the app shell while the user is actively scrolling" in APP_JS
    assert "modelScorePanelStyle" in APP_JS
    assert "MODEL_SCORE_HUE_PALETTE" in APP_JS
    assert "peerModels" in APP_JS

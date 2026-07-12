from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.models.adapters import LegacyVisionTaggerAdapter
from data_curation_tool.models.legacy_tagger_configs import legacy_tagger_config
from data_curation_tool.services.graph_editor_service import GRAPH_NODE_CUSTOMIZATION_SCHEMA, GraphEditorService

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_is_5_8_16() -> None:
    assert __version__ == "5.8.48"


def test_eva_compat_defaults_include_no_embed_class_and_retry_helper() -> None:
    cfg = legacy_tagger_config("thouph-eva02-vit-large-448-8046")
    adapter = LegacyVisionTaggerAdapter("legacy-eva02-vit-large-448-8046", cfg["label"], cfg)
    defaults = adapter._eva_compat_defaults()
    assert defaults["reg_token"] is None
    assert defaults["mask_token"] is None
    assert defaults["no_embed_class"] is False
    assert "dynamic_img_size" in defaults

    class Eva:
        __module__ = "timm.models.eva"
        def modules(self):
            return [self]

    model = Eva()
    adapter._patch_torch_model_compat(model)
    assert model.no_embed_class is False
    assert model.reg_token is None


def test_graph_catalog_exposes_standalone_palette_customization() -> None:
    service = GraphEditorService(type("P", (), {"runtime": Path("/tmp/dct_graph_test_runtime")})())
    catalog = service.catalog()
    kinds = {row["kind"]: row for row in catalog["node_palette"]}
    for kind in ["text_input", "image_input", "audio_input", "video_input", "bundle_context", "model_call", "supervisor_controller", "external_tool_call", "output_artifact"]:
        assert kind in kinds
        assert kinds[kind].get("customization_schema")
    assert GRAPH_NODE_CUSTOMIZATION_SCHEMA["model_call"]["standalone_type"] == "MODEL"
    assert "node_customization_schema" in catalog
    assert "standalone_palette_customization" in catalog["runtime_capabilities"]


def test_frontend_uses_palette_driven_node_config_and_fast_prediction_refresh() -> None:
    js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "graphEditorPaletteCustomizationInspector" in js
    assert "graphEditorChangeNodeKind" in js
    assert "customization_schema" in js
    assert "graphEditorNodePaletteCard" in js
    assert "requestTagScores(id, tags)" in js
    assert "lastMediaPredictionRefreshAt" in js
    assert "mediaRefreshed && ['Tag Editor','Compare','Gallery','Batch Tags','Prediction Analytics'].includes(state.tab)" in js


def test_prediction_score_colors_are_panel_unique_not_small_hash_bucket() -> None:
    js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function modelScorePanelHue" in js
    assert "function modelScorePanelStyle" in js
    assert "peerModels" in js
    assert "MODEL_SCORE_HUE_PALETTE" in js
    assert "% 32" in js


def test_scroll_restore_does_not_refire_after_user_scroll_on_tab_switch() -> None:
    js = (ROOT / "data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Number(state.lastUserScrollAt || 0) > started" in js
    assert "if (!recentUserScroll(350)) restoreScrollState(tab, { aggressive: true })" in js

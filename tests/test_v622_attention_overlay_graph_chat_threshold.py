from __future__ import annotations

from pathlib import Path

from PIL import Image

from data_curation_tool.config import AppSettings
from data_curation_tool.models.legacy_tagger_configs import legacy_tagger_config
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.attention_visualization_service import AttentionVisualizationService


APP_JS = Path("data_curation_tool/static/app.js")


def test_default_classifier_threshold_is_point_seven() -> None:
    assert AppSettings().classifier_threshold == 0.70
    for key in [
        "thouph-eva02-vit-large-448-8046",
        "thouph-eva02-clip-vit-large-7704",
        "thouph-experimental-efficientnetv2-m-8035",
    ]:
        assert legacy_tagger_config(key)["confidence_threshold"] == 0.70


def test_attention_service_writes_heatmap_and_overlay_paths(tmp_path: Path) -> None:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    image = tmp_path / "sample.png"
    Image.new("RGB", (320, 240), (30, 60, 90)).save(image)

    service = AttentionVisualizationService(paths)
    result = service.run({"method": "classifier_gradcam", "tag": "blue eyes", "image_path": str(image)})

    assert result["ok"] is True
    assert result["overlay_url"]
    assert result["heatmap_url"]
    assert Path(result["overlay_path"]).exists()
    assert Path(result["heatmap_path"]).exists()
    assert Path(result["manifest_path"]).exists()


def test_tag_editor_and_compare_have_inline_heatmap_overlay_controls() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function attentionOverlayControls" in text
    assert "function attentionOverlayPreview" in text
    assert "heatmap_url" in text
    assert "attentionOverlayControls([item]" in text
    assert "Compare Pair Attention Heatmaps" in text
    assert "m.key !== 'tsne_embedding_map'" in text


def test_graph_editor_interaction_markers_exist() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function graphEditorOpenNodeInspector" in text
    assert "render(true, 'hard')" in text
    assert "Edit properties panel" in text
    assert "Maximize properties" in text
    assert "box.addEventListener('dblclick'" in text
    assert "canvas.addEventListener('dblclick'" in text
    assert "world-menu" in text
    assert "Graph saved" in text
    assert "Remove Graph" in text


def test_graph_chat_tab_and_safe_visible_reasoning_trace_exist() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "Agentic Graph Chat" in text
    assert "function agenticGraphChatView" in text
    assert "function graphChatContextSnapshot" in text
    assert "Graph-Linked Chat" in text
    assert "visible_plan_and_action_trace_only" in text
    assert "do not reveal private hidden chain-of-thought" in text
    assert "'Agentic Graph Chat': agenticGraphChatView" in text

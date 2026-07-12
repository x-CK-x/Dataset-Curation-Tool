from pathlib import Path
from types import SimpleNamespace

from PIL import Image

import data_curation_tool
from data_curation_tool.services.attention_visualization_service import AttentionVisualizationService

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_version_bumped_to_v5845():
    assert data_curation_tool.__version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")
    assert "v5.8.48 Update" in read("README.md")


def test_attention_service_has_hydra_signed_cam_and_fallback(tmp_path):
    img = tmp_path / "image.png"
    Image.new("RGB", (192, 128), (64, 72, 90)).save(img)
    svc = AttentionVisualizationService(SimpleNamespace(outputs=str(tmp_path / "outputs")))
    result = svc.run({"method": "hydra_cam_attention", "tag": "blue_eyes", "image_path": str(img), "cam_depth": 1})
    assert result["ok"] is True
    assert result["heatmap_path"] and Path(result["heatmap_path"]).exists()
    assert result["overlay_path"] and Path(result["overlay_path"]).exists()
    assert result["attention_source"] in {"fallback_signed_cam", "native_hydra_demo_cam"}
    svc_src = read("data_curation_tool/services/attention_visualization_service.py")
    assert "_try_hydra_cam_overlay" in svc_src
    assert "model.forward_features" in svc_src
    assert "hydra_model.select_labels(tag)" in svc_src
    assert "fallback_signed_cam" in svc_src
    assert "positive evidence" in svc_src


def test_attention_dropdowns_are_refresh_protected_and_partial_overlay_updates():
    app = read("data_curation_tool/static/app.js")
    assert "attentionOverlayInteractionActive" in app
    assert "preserveAttentionControlAttrs" in app
    assert "attention-heatmap-control-select" in app
    assert "data-preserve-selection" in app
    assert "updateAttentionOverlayDom" in app
    assert "refreshAfterAttentionArtifactChange" in app
    assert "CAM depth" in app
    assert "heat strength" in app
    assert "cam_depth: Number(state.attentionOverlayCamDepth || 1)" in app
    assert "alpha_scale: Number(state.attentionOverlayAlphaScale || 0.58)" in app


def test_quick_queue_recent_rows_clear_without_tab_switch():
    app = read("data_curation_tool/static/app.js")
    assert "recentMaxAgeMs" in app
    assert "scope === 'quick' ? 12000 : 120000" in app
    assert "updateInferenceQueueDom" in app
    assert "pollModelRuntimeLive" in app


def test_docs_added():
    assert "Attention Heatmap" in read("docs/V5_8_45_ATTENTION_HEATMAP_DROPDOWN_QUEUE_REFRESH.md")
    assert "75-Attention-Heatmap-Dropdown-Queue-Refresh.md" in read("docs/wiki/_Sidebar.md")

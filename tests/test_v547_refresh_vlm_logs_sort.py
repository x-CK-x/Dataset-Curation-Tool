from pathlib import Path

from PIL import Image

from data_curation_tool.models.adapters import HFVLMChatAdapter


class FakeImageTextPipeline:
    def __init__(self):
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if args and isinstance(args[0], list):
            content = args[0][0]["content"]
            assert any(part.get("type") == "image" and part.get("image") is not None for part in content)
            assert "images" not in kwargs, "chat messages and images must not be passed separately"
            return [{"generated_text": [{"role": "assistant", "content": [{"type": "text", "text": "tags: blue_eyes, smile"}]}]}]
        raise RuntimeError("fallback should not be needed")


def test_hf_vlm_pipeline_embeds_images_inside_chat_message(tmp_path: Path):
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (16, 16)).save(image_path)
    adapter = HFVLMChatAdapter("local-test-model")
    adapter.pipeline = FakeImageTextPipeline()
    adapter.model_id = "local-test-model"

    result = adapter.chat(
        "look at the image and validate existing tags",
        context={"media": [{"path": str(image_path)}]},
        model_id="local-test-model",
    )

    assert result["suggested_tags"] == ["blue_eyes", "smile"]
    assert adapter.pipeline.calls


def test_v547_frontend_contains_refresh_safe_logs_and_predicted_sort_controls():
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Sort Predicted by Category" in js
    assert "Sort Predicted by Accuracy" in js
    assert "Download Error" in js
    assert "Download Log File" in js
    assert "updateTileSelectionDom" in js
    assert "updateLiveStatusDom" in js
    assert "passiveSensitiveTabs" in js

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def test_select_tags_route_returns_full_error_detail(tmp_path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "1")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    c = app.state.context

    def boom(_payload):
        raise RuntimeError("synthetic VLM failure")

    c.models.select_tags = boom  # type: ignore[method-assign]
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/models/select-tags", json={"media_ids": [1], "model_name": "hf-vlm-chat", "operation": "preview"})
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "Tag-selection inference failed" in detail
    assert "synthetic VLM failure" in detail
    assert "Traceback" in detail


def test_v547_frontend_exposes_more_stable_refresh_and_sort_controls():
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Live job refresh" in js
    assert "Live status refresh" in js
    assert "lastApiError" in js
    assert "Sort All by Category" in js
    assert "state.lastModelListRefreshAt" in js
    assert "updateTileSelectionDom();" in js

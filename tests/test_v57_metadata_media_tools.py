from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_metadata_extract_now_reads_a1111_parameters_and_applies_tags(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    image_path = root / "sample.png"
    meta = PngImagePlugin.PngInfo()
    meta.add_text("parameters", "1girl, blue_hair, <lora:test_style:0.8>\nNegative prompt: blurry\nSteps: 20, Sampler: Euler, CFG scale: 7, Seed: 42, Model: test")
    Image.new("RGB", (32, 32), (20, 30, 40)).save(image_path, pnginfo=meta)

    client = _client(tmp_path)
    job = client.post("/api/datasets/import", json={"root_path": str(root), "read_sidecars": True, "auto_sync_tag_dictionary": False}).json()
    assert job["status"] == "queued"
    media = client.get("/api/media").json()["items"][0]
    result = client.post(
        "/api/media-tools/metadata/extract-now",
        json={"media_ids": [media["id"]], "apply_tags": True, "tag_source": "positive_prompt", "caption_source": "metadata_summary", "include_raw": False},
    )
    assert result.status_code == 200
    body = result.json()
    assert body["count"] == 1
    assert "blue_hair" in body["results"][0]["extracted_tags"]
    updated = client.get(f"/api/media/{media['id']}").json()
    assert "1girl" in updated["tags"]
    assert "blue_hair" in updated["tags"]


def test_media_tools_and_hud_controls_exist(tmp_path: Path):
    client = _client(tmp_path)
    assert client.get("/api/media-tools/ffmpeg/status").status_code == 200
    html = client.get("/static/app.js").text
    assert "Media Tools" in html
    assert "Metadata Extraction From Images / Videos" in html
    assert "Video Frame Extraction" in html
    assert "Krita Bridge" in html
    assert "/api/media-tools/video/extract-audio" in html

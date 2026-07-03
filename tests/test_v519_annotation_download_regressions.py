from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def _create_media(client: TestClient, tmp_path: Path) -> int:
    folder = tmp_path / "dataset"
    folder.mkdir()
    image_path = folder / "sample.png"
    Image.new("RGB", (160, 120), "white").save(image_path)
    dataset = client.post("/api/datasets/import", json={"root_path": str(folder), "name": "ann", "auto_sync_tag_dictionary": False}).json()
    dataset_id = client.get("/api/datasets").json()[0]["id"]
    media = client.get(f"/api/media?dataset_id={dataset_id}").json()["items"]
    return int(media[0]["id"])


def test_reference_annotation_editor_endpoints_and_krita_package(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _create_media(client, tmp_path)
    state = client.get(f"/api/reference/annotations/editor-state/{media_id}").json()
    assert state["media"]["id"] == media_id
    assert state["annotations"] == []

    proposed = client.post(
        "/api/reference/annotations/propose",
        json={"media_id": media_id, "label": "character", "target_name": "target", "save": True, "create_mask": True},
    ).json()
    assert proposed["ok"] is False
    assert proposed["count"] == 0
    assert proposed["saved"] == []

    manual = client.post(
        "/api/reference/annotations",
        json={"media_id": media_id, "label": "character", "target_name": "target", "annotation_type": "bbox", "bbox": {"x1": 1, "y1": 2, "x2": 80, "y2": 90}},
    ).json()
    assert manual["annotation_id"] > 0

    state = client.get(f"/api/reference/annotations/editor-state/{media_id}").json()
    assert len(state["annotations"]) == 1

    pkg = client.post("/api/krita/annotation-package", json={"media_id": media_id}).json()
    assert Path(pkg["manifest_path"]).exists()
    assert pkg["annotations"] == 1


def test_downloader_reports_monotonic_aggregate_progress(tmp_path: Path, monkeypatch):
    client = _client(tmp_path)
    ctx = client.app.state.context
    svc: DownloaderService = ctx.downloads

    calls = []

    def fake_fetch(preset, cfg, api_url, limit, page, request=None):
        return [{"file": {"url": f"https://example.test/{preset['name']}_{page}_{i}.jpg"}, "tags": {"general": [preset['name']]}} for i in range(limit)]

    def fake_item(item, cfg, output_dir, preset):
        target = Path(output_dir) / Path(item["file"]["url"]).name
        target.write_bytes(b"fake")
        return str(target)

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    monkeypatch.setattr(svc, "_download_item", fake_item)

    req = DownloadRequest(
        confirmed_authorized=True,
        max_items=3,
        parallel_workers=2,
        parallel_presets=True,
        preset=DownloadPreset(name="p0", source="e621", positive_tags=["tag0"]),
        output_dir=str(tmp_path / "downloads"),
    )
    # Simulate category expansion into 2 presets without needing a dictionary.
    monkeypatch.setattr(svc, "_expand_presets_for_categories", lambda presets, request: [
        {"name": "p1", "source": "e621", "positive_tags": ["tag1"], "negative_tags": [], "options": {"_max_items": 3}},
        {"name": "p2", "source": "e621", "positive_tags": ["tag2"], "negative_tags": [], "options": {"_max_items": 3}},
    ])
    result = svc.run(req, lambda value, message="": calls.append((value, message)))
    assert result["downloaded"] == 6
    values = [v for v, _ in calls]
    assert values == sorted(values)
    assert values[-1] == 1.0
    assert "6/6" in calls[-1][1]

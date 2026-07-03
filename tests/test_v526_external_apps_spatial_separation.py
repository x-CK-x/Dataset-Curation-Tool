from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


class _FakeProcess:
    pid = 42426

    @staticmethod
    def poll():
        return None


def _app(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    return app, paths, TestClient(app)


def _import_image(client: TestClient, tmp_path: Path) -> int:
    root = tmp_path / "dataset"
    root.mkdir(exist_ok=True)
    Image.new("RGB", (96, 64), (100, 120, 140)).save(root / "sample.png")
    response = client.post("/api/datasets/import", json={
        "root_path": str(root), "recursive": True, "read_sidecars": False,
        "compute_sha256": False, "probe_dimensions": True,
    })
    assert response.status_code == 200, response.text
    media = client.get("/api/media", params={"page_size": 10}).json()["items"]
    return int(media[0]["id"])


def test_external_app_launch_now_creates_safe_handoff_and_returns_pid(tmp_path: Path):
    app, paths, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    fake_exe = tmp_path / "home" / "Topaz Photo AI.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"fake executable")
    service = app.state.context.external_apps
    service._popen = lambda path, args, cwd=None: _FakeProcess()  # type: ignore[method-assign]

    response = client.post("/api/augment/external-tool/launch-now", json={
        "media_ids": [media_id],
        "tool_name": "topaz_photo_ai",
        "mode": "open",
        "executable_path": str(fake_exe),
        "copy_inputs": True,
        "auto_discover": True,
        "save_discovered_path": True,
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["pid"] == 42426
    assert body["launched"] == 1
    handoff = Path(body["handoff_dir"])
    assert handoff.exists()
    manifest = json.loads((handoff / "handoff_manifest.json").read_text(encoding="utf-8"))
    assert manifest["copy_inputs"] is True
    assert Path(manifest["items"][0]["staged"]).exists()
    assert Path(manifest["items"][0]["staged"]).resolve() != Path(manifest["items"][0]["source"]).resolve()
    assert app.state.context.settings.external_image_tools["topaz_photo_ai"]["executable_path"] == str(fake_exe.resolve())
    client.close()


def test_external_app_discovery_searches_home_style_root(tmp_path: Path):
    app, _, client = _app(tmp_path)
    fake_home = tmp_path / "home"
    fake_exe = fake_home / "Portable Apps" / "Topaz Labs" / "Topaz Gigapixel AI.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"fake")
    service = app.state.context.external_apps
    service._candidate_roots = lambda: [fake_home]  # type: ignore[method-assign]
    result = service.discover("topaz_gigapixel", refresh=True, save=False)
    assert result["available"] is True
    assert Path(result["path"]) == fake_exe.resolve()
    client.close()


def test_detection_and_segmentation_catalogs_are_separate(tmp_path: Path):
    _, _, client = _app(tmp_path)
    detection = {row["name"] for row in client.get("/api/spatial/detection/models").json()}
    segmentation = {row["name"] for row in client.get("/api/spatial/segmentation/models").json()}
    assert "yolo11n-detect" in detection
    assert "yolo11n-seg" not in detection
    assert "sam-vit-b" not in detection
    assert "sam-vit-b" in segmentation
    assert "yolo11n-seg" in segmentation
    assert "yolo11n-detect" not in segmentation
    assert "yoloe-training-runtime" not in segmentation
    client.close()


def test_wrong_task_model_is_rejected_without_fake_output(tmp_path: Path):
    _, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    wrong_detection = client.post("/api/spatial/detection/propose", json={
        "media_id": media_id, "model_key": "sam-vit-b", "save": False,
    }).json()
    assert wrong_detection["ok"] is False
    assert wrong_detection["proposals"] == []
    assert wrong_detection["saved"] == []
    wrong_segmentation = client.post("/api/spatial/segmentation/propose", json={
        "media_id": media_id, "model_key": "yolo11n-detect", "save": False,
    }).json()
    assert wrong_segmentation["ok"] is False
    assert wrong_segmentation["proposals"] == []
    client.close()


def test_multiple_manual_masks_get_unique_files_and_preview(tmp_path: Path):
    _, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    polygon_a = [[5, 5], [40, 5], [40, 40], [5, 40]]
    polygon_b = [[45, 10], [85, 10], [85, 55], [45, 55]]
    first = client.post("/api/reference/annotations", json={
        "media_id": media_id, "label": "first", "annotation_type": "mask", "polygon": polygon_a,
        "bbox": {"x1": 0, "y1": 0, "x2": 95, "y2": 63},
    }).json()
    second = client.post("/api/reference/annotations", json={
        "media_id": media_id, "label": "second", "annotation_type": "mask", "polygon": polygon_b,
    }).json()
    assert first["mask_path"] and second["mask_path"]
    assert first["mask_path"] != second["mask_path"]
    assert Path(first["mask_path"]).exists()
    assert Path(second["mask_path"]).exists()
    # Polygon geometry must take priority over an optional model bbox prompt.
    with Image.open(first["mask_path"]) as mask:
        assert mask.getpixel((90, 60)) == 0
        assert mask.getpixel((10, 10)) > 0
    preview = client.get("/api/spatial/mask-preview", params={"path": first["mask_path"]})
    assert preview.status_code == 200
    state = client.get(f"/api/spatial/segmentation/state/{media_id}").json()
    assert len(state["annotations"]) == 2
    client.close()


def test_frontend_exposes_separate_spatial_tabs_and_immediate_launch():
    source = (Path(__file__).resolve().parents[1] / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Detection & Boxes" in source
    assert "Segmentation & Masks" in source
    assert "Pose & 3D" in source
    assert "/api/spatial/detection/propose" in source
    assert "/api/spatial/segmentation/propose" in source
    assert "/api/augment/external-tool/launch-now" in source
    assert "Launch / Send Selected Now" in source
    assert "Edit/Upscale/Topaz Selected" not in source

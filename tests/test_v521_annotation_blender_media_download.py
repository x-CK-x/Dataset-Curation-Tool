from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def _import_one_image(client: TestClient, tmp_path: Path) -> int:
    root = tmp_path / "dataset"
    root.mkdir()
    img = root / "sample.png"
    Image.new("RGB", (96, 64), (120, 40, 20)).save(img)
    resp = client.post("/api/datasets/import", json={"root_path": str(root), "recursive": True, "read_sidecars": False, "compute_sha256": False, "probe_dimensions": True})
    assert resp.status_code == 200, resp.text
    page = client.get("/api/media", params={"page_size": 5}).json()
    return int(page["items"][0]["id"])


def test_annotation_download_dry_run_and_blender_plugin(tmp_path: Path):
    client = _client(tmp_path)
    resp = client.post("/api/reference/annotations/download-model", json={"model_key": "sam-vit-b", "dry_run": True})
    assert resp.status_code == 200, resp.text
    job = client.get(f"/api/jobs/{resp.json()['job_id']}").json()
    assert job["status"] == "completed"
    assert job["result"]["dry_run_supported"] is True
    yolo = client.post("/api/reference/annotations/download-model", json={"model_key": "yolo11n-seg", "dry_run": True})
    assert yolo.status_code == 200, yolo.text
    plugin = client.get("/api/blender/plugin")
    assert plugin.status_code == 200
    assert plugin.content[:2] == b"PK"


def test_pose3d_import_and_annotation_delete(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    pose_payload = {
        "media_id": media_id,
        "label": "rig_pose",
        "target_name": "character_rig",
        "rig_name": "TestArmature",
        "keypoints_3d": [{"name": "hip", "x": 0, "y": 0, "z": 0}, {"name": "head", "x": 0, "y": 1, "z": 0}],
        "edges": [[0, 1]],
    }
    saved = client.post("/api/blender/import-pose", json=pose_payload)
    assert saved.status_code == 200, saved.text
    ann_id = saved.json()["annotation_id"]
    state = client.get(f"/api/reference/annotations/editor-state/{media_id}").json()
    assert any(a["id"] == ann_id and a["metadata"].get("keypoints_3d") for a in state["annotations"])
    deleted = client.delete(f"/api/reference/annotations/{ann_id}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["deleted"] == 1

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
    assert page["items"]
    return int(page["items"][0]["id"])


def test_annotation_catalog_exposes_sam_yolo_pose_rows(tmp_path: Path):
    client = _client(tmp_path)
    names = {m["name"] for m in client.get("/api/models").json()}
    assert {"sam-vit-b", "sam-hq-vit-b", "sam2.1-hiera-tiny", "yolo11n-detect", "yolo11n-seg", "yolo11n-pose", "custom-yolo-local", "pose-3d-dataset-contract"} <= names
    catalog = client.get("/api/reference/annotations/model-catalog").json()
    c_names = {m["name"] for m in catalog}
    assert "sam-vit-b" in c_names
    assert "yolo11n-seg" in c_names
    assert "yolo11n-pose" in c_names


def test_annotation_pose_metadata_save_and_no_fake_fallback_proposal(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    proposal = client.post("/api/reference/annotations/propose", json={"media_id": media_id, "model_key": "demo_center_bbox", "annotation_type": "bbox", "label": "object", "save": False}).json()
    assert proposal["ok"] is False
    assert proposal["count"] == 0
    assert proposal["proposals"] == []
    assert "No annotation model selected" in proposal["error"]
    pose = {
        "media_id": media_id,
        "label": "body_pose",
        "annotation_type": "pose2d",
        "metadata": {"keypoints_2d": [{"name": "head", "x": 12, "y": 8}, {"name": "hip", "x": 20, "y": 44}], "edges": [[0, 1]]},
    }
    saved = client.post("/api/reference/annotations", json=pose)
    assert saved.status_code == 200, saved.text
    state = client.get(f"/api/reference/annotations/editor-state/{media_id}").json()
    anns = state["annotations"]
    assert any(a["annotation_type"] == "pose2d" and a["metadata"].get("keypoints_2d") for a in anns)


def test_annotation_model_status_custom_local_path(tmp_path: Path):
    client = _client(tmp_path)
    fake = tmp_path / "custom.pt"
    fake.write_bytes(b"not a real model but path exists")
    status = client.get("/api/reference/annotations/model-status", params={"model_key": "custom-yolo-local", "local_model_path": str(fake), "custom_model_type": "yolo"}).json()
    assert status["available"] is True
    assert status["downloaded"] is True

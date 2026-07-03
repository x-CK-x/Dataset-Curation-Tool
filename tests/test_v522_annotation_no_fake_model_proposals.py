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


def test_no_model_preview_never_creates_fake_bbox_or_saved_annotation(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    resp = client.post("/api/reference/annotations/propose", json={"media_id": media_id, "model_key": "", "annotation_type": "bbox", "save": True})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is False
    assert body["proposals"] == []
    assert body["saved"] == []
    state = client.get(f"/api/reference/annotations/editor-state/{media_id}").json()
    assert state["annotations"] == []


def test_missing_runtime_returns_structured_error_not_internal_server_error(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    resp = client.post("/api/reference/annotations/propose", json={"media_id": media_id, "model_key": "sam-vit-b", "annotation_type": "mask", "save": False})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is False
    assert body["proposals"] == []
    assert body["count"] == 0
    assert body.get("error")


def test_pose_contract_does_not_generate_synthetic_pose_without_user_keypoints(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    resp = client.post("/api/reference/annotations/propose", json={"media_id": media_id, "model_key": "pose-3d-dataset-contract", "annotation_type": "pose3d", "save": False})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is False
    assert body["proposals"] == []
    assert "not a runnable model" in body["error"]


def test_mocked_yolo_model_proposal_is_saved_without_fallback(tmp_path: Path, monkeypatch):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)

    def fake_yolo(*args, **kwargs):
        return [{
            "label": "character",
            "annotation_type": "bbox",
            "bbox": {"x1": 2, "y1": 3, "x2": 80, "y2": 50},
            "polygon": [],
            "confidence": 0.91,
            "source": "model",
            "model_key": kwargs.get("model_key", "yolo11n-detect"),
            "metadata": {"class_name": "character"},
        }]

    monkeypatch.setattr("data_curation_tool.services.reference_service.propose_with_yolo", fake_yolo)
    resp = client.post("/api/reference/annotations/propose", json={"media_id": media_id, "model_key": "yolo11n-detect", "annotation_type": "bbox", "label": "character", "save": True})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["count"] == 1
    assert body["saved"][0]["annotation_id"] > 0
    state = client.get(f"/api/reference/annotations/editor-state/{media_id}").json()
    assert state["annotations"][0]["source"] == "model"
    assert state["annotations"][0]["bbox"]["x1"] == 2

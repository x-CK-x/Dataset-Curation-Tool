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
    Image.new("RGB", (96, 64), (120, 40, 20)).save(root / "sample.png")
    resp = client.post("/api/datasets/import", json={"root_path": str(root), "recursive": True, "read_sidecars": False, "compute_sha256": False, "probe_dimensions": True})
    assert resp.status_code == 200, resp.text
    return int(client.get("/api/media", params={"page_size": 5}).json()["items"][0]["id"])


def test_annotation_catalog_excludes_generic_dataset_assistant(tmp_path: Path):
    client = _client(tmp_path)
    catalog = client.get("/api/reference/annotations/model-catalog").json()
    names = {row["name"] for row in catalog}
    assert "dataset-assistant" not in names
    assert {"sam-vit-b", "sam-hq-vit-b", "sam2.1-hiera-tiny", "yolo11n-seg"} <= names


def test_custom_sam_type_without_checkpoint_does_not_use_dataset_assistant_as_checkpoint(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    resp = client.post("/api/reference/annotations/propose", json={
        "media_id": media_id,
        "model_key": "dataset-assistant",
        "annotation_type": "mask",
        "options": {"custom_model_type": "sam"},
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is False
    assert body["proposals"] == []
    assert "dataset-assistant" not in body.get("error", "") or "No annotation adapter" in body.get("error", "")
    assert "SAM checkpoint was not found: dataset-assistant" not in body.get("error", "")


def test_hq_status_checks_segment_anything_hq_dependency(tmp_path: Path):
    client = _client(tmp_path)
    status = client.get("/api/reference/annotations/model-status", params={"model_key": "sam-hq-vit-b"}).json()
    assert "segment-anything-hq" in status.get("requirements", {})


def test_missing_sam_checkpoint_names_selected_model_not_checkpoint_literal(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _import_one_image(client, tmp_path)
    body = client.post("/api/reference/annotations/propose", json={
        "media_id": media_id,
        "model_key": "sam-vit-b",
        "annotation_type": "mask",
    }).json()
    assert body["ok"] is False
    assert "Download weights" in body.get("error", "") or "checkpoint" in body.get("error", "")
    assert "SAM checkpoint was not found: sam-vit-b" not in body.get("error", "")

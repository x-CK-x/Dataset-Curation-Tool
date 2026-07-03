from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.pose_models import (
    BLAZEPOSE33_EDGES,
    COCO17_EDGES,
    H36M17_EDGES,
    infer_skeleton_key,
    list_skeleton_templates,
    normalize_edges,
    normalize_keypoints,
)


def _client(tmp_path: Path) -> tuple[TestClient, AppPaths]:
    paths = AppPaths.create(
        runtime=tmp_path / "runtime",
        models=tmp_path / "models",
        outputs=tmp_path / "outputs",
    )
    return TestClient(create_app(paths)), paths


def _import_image(client: TestClient, tmp_path: Path) -> int:
    root = tmp_path / "dataset"
    root.mkdir(exist_ok=True)
    Image.new("RGB", (160, 120), (40, 80, 120)).save(root / "pose_source.png")
    response = client.post(
        "/api/datasets/import",
        json={
            "root_path": str(root),
            "recursive": True,
            "read_sidecars": False,
            "compute_sha256": False,
            "probe_dimensions": True,
        },
    )
    assert response.status_code == 200, response.text
    items = client.get("/api/media", params={"page_size": 10}).json()["items"]
    assert items
    return int(items[0]["id"])


def test_pose_templates_have_named_topology_and_normalizers():
    templates = {row["key"]: row for row in list_skeleton_templates()}
    assert templates["coco17"]["edges"] == [list(edge) for edge in COCO17_EDGES]
    assert templates["blazepose33"]["edges"] == [list(edge) for edge in BLAZEPOSE33_EDGES]
    assert templates["h36m17"]["edges"] == [list(edge) for edge in H36M17_EDGES]
    assert len(templates["blazepose33"]["names"]) == 33
    assert infer_skeleton_key(33, "mediapipe-pose-full", "3d") == "blazepose33"
    assert infer_skeleton_key(17, "mmpose-motionbert-human3d", "3d") == "h36m17"
    assert normalize_edges([[0, 1], [1, 0], ["hip", "head"], [2, 2], [None, 3]]) == [[0, 1], ["hip", "head"]]
    points = normalize_keypoints([[12, 15, 0.9], [300, -5, 0.4]], names=["a", "b"], image_size=(160, 120))
    assert points == [
        {"name": "a", "x": 12.0, "y": 15.0, "score": 0.9},
        {"name": "b", "x": 160.0, "y": 0.0, "score": 0.4},
    ]


def test_model_catalog_lists_multiple_2d_and_real_3d_pose_backends(tmp_path: Path):
    client, _ = _client(tmp_path)
    models = {row["name"]: row for row in client.get("/api/models").json()}
    expected = {
        "yolo11n-pose",
        "mediapipe-pose-lite",
        "mediapipe-pose-full",
        "mediapipe-pose-heavy",
        "mmpose-rtmpose-human",
        "mmpose-vitpose-base",
        "mmpose-rtmpose-wholebody",
        "mmpose-rtmpose-animal",
        "mmpose-motionbert-human3d",
        "mmpose-internet-hand3d",
        "custom-mmpose-local",
    }
    assert expected <= set(models)
    assert "pose3d" in models["mediapipe-pose-full"]["capabilities"]
    assert "keypoints3d" in models["mmpose-motionbert-human3d"]["capabilities"]
    assert "keypoints3d" in models["mmpose-internet-hand3d"]["capabilities"]
    templates = client.get("/api/reference/annotations/pose-templates")
    assert templates.status_code == 200
    assert any(row["key"] == "h36m17" and row["edges"] for row in templates.json())
    client.close()


def test_3d_provider_catalog_dry_runs_and_asset_library(tmp_path: Path):
    client, paths = _client(tmp_path)
    media_id = _import_image(client, tmp_path)
    catalog = client.get("/api/three-d/providers")
    assert catalog.status_code == 200, catalog.text
    body = catalog.json()
    generation = {row["key"] for row in body["generation"]}
    rigging = {row["key"] for row in body["rigging"]}
    assert {
        "triposr_local",
        "stable_fast_3d_local",
        "trellis_image_local",
        "trellis_text_local",
        "hunyuan3d_local_api",
        "meshy_image_api",
        "generic_image_to_3d_api",
    } <= generation
    assert {"unirig_local", "blender_pose_rig"} <= rigging

    dry = client.post(
        "/api/three-d/generate",
        json={
            "provider": "hunyuan3d_local_api",
            "media_id": media_id,
            "endpoint": "http://127.0.0.1:8081/generate",
            "output_format": "glb",
            "dry_run": True,
        },
    )
    assert dry.status_code == 200, dry.text
    job = client.get(f"/api/jobs/{dry.json()['job_id']}").json()
    assert job["status"] == "completed", job
    assert job["result"]["dry_run"] is True
    assert job["result"]["plan"]["request"]["method"] == "POST"
    assert "remove_background" not in job["result"]["plan"]["request"]["body_fields"]
    assert "background removal internally" in job["result"]["plan"]["request"]["note"]
    assert Path(job["result"]["job_dir"], "dry_run_plan.json").exists()

    external_asset = tmp_path / "source.glb"
    external_asset.write_bytes(b"glTF-test-asset")
    imported = client.post(
        "/api/three-d/assets/import",
        json={"source_path": str(external_asset), "copy": True, "label": "test asset"},
    )
    assert imported.status_code == 200, imported.text
    record = imported.json()
    assert Path(record["path"]).is_file()
    assert Path(record["path"]).is_relative_to(paths.outputs / "3d_assets")
    assert record["metadata"]["label"] == "test asset"

    assets = client.get("/api/three-d/assets").json()
    assert any(row["path"] == record["path"] for row in assets)
    download = client.get("/api/three-d/assets/file", params={"path": record["relative_path"]})
    assert download.status_code == 200
    assert download.content == b"glTF-test-asset"
    traversal = client.get("/api/three-d/assets/file", params={"path": "../../outside.glb"})
    assert traversal.status_code == 404

    rig = client.post(
        "/api/three-d/rig",
        json={
            "provider": "blender_pose_rig",
            "asset_path": record["path"],
            "media_id": media_id,
            "dry_run": True,
        },
    )
    assert rig.status_code == 200, rig.text
    rig_job = client.get(f"/api/jobs/{rig.json()['job_id']}").json()
    assert rig_job["status"] == "completed", rig_job
    command = rig_job["result"]["plan"]["command"]
    assert "dct_auto_rig.py" in " ".join(command)
    client.close()


def test_pose_annotations_round_trip_edges_and_blender_fetch(tmp_path: Path):
    client, _ = _client(tmp_path)
    media_id = _import_image(client, tmp_path)
    payload = {
        "media_id": media_id,
        "label": "editable_3d_pose",
        "target_name": "character",
        "annotation_type": "pose3d",
        "source": "user",
        "metadata": {
            "keypoints_2d": [
                {"name": "pelvis", "x": 80, "y": 80},
                {"name": "head", "x": 80, "y": 20},
            ],
            "keypoints_3d": [
                {"name": "pelvis", "x": 0, "y": 0, "z": 0, "image_x": 80, "image_y": 80},
                {"name": "head", "x": 0, "y": 1, "z": 0, "image_x": 80, "image_y": 20},
            ],
            "edges": [[0, 1]],
            "skeleton_template": "h36m17",
        },
    }
    saved = client.post("/api/reference/annotations", json=payload)
    assert saved.status_code == 200, saved.text
    annotation_id = int(saved.json()["id"])
    fetched = client.get(f"/api/blender/pose/{media_id}", params={"annotation_id": annotation_id})
    assert fetched.status_code == 200, fetched.text
    result = fetched.json()
    assert result["annotation_id"] == annotation_id
    assert result["edges"] == [[0, 1]]
    assert result["keypoints_3d"][1]["name"] == "head"
    client.close()


def test_frontend_and_blender_bridge_expose_interactive_pose_and_3d_actions():
    root = Path(__file__).resolve().parents[1]
    source = (root / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "data_curation_tool" / "static" / "styles.css").read_text(encoding="utf-8")
    for text in (
        "Pose Editor — Visible Bones and Drag-editable Joints",
        "Connect Bones",
        "Interactive 3D Skeleton Viewer",
        "Bones are redrawn continuously as joints move.",
        "MotionBERT",
        "3D Generation Studio",
        "Automatic 3D Rigging",
        "Validate / Dry-run",
        "Open in Blender",
        "Help & Workflows",
        "pose3DWithImageProjection",
        "canvas.addEventListener('pointermove'",
    ):
        assert text in source
    for text in (".pose-editor-canvas.tool-move", ".pose-toolbar", ".pose3d-interactive"):
        assert text in css

    plugin = root / "integrations" / "blender_dataset_bridge.zip"
    assert plugin.exists()
    with zipfile.ZipFile(plugin) as archive:
        archive.testzip()
        init_name = next(name for name in archive.namelist() if name.endswith("__init__.py"))
        addon = archive.read(init_name).decode("utf-8")
    for text in (
        "Create Armature from DCT Pose",
        "Import Latest DCT Asset",
        "Queue 3D Generation",
        "Queue Automatic Rigging",
        "rig_repo_path",
        "shell_executable",
        "/api/three-d/generate",
        "/api/three-d/rig",
    ):
        assert text in addon

    auto_rig = (root / "integrations" / "blender_scripts" / "dct_auto_rig.py").read_text(encoding="utf-8")
    assert 'point.get("image_x")' in auto_rig
    assert 'point.get("image_y")' in auto_rig

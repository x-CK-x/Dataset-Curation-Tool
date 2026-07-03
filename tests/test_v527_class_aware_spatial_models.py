from __future__ import annotations

import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.annotation_classes import inspect_model_classes, resolve_class_query
from data_curation_tool.services.annotation_models import AnnotationModelError, propose_with_yolo
import data_curation_tool.services.reference_service as reference_module


def _app(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    return app, paths, TestClient(app)


def _import_image(client: TestClient, tmp_path: Path) -> int:
    root = tmp_path / "dataset"
    root.mkdir(exist_ok=True)
    Image.new("RGB", (128, 96), (80, 100, 120)).save(root / "sample.png")
    response = client.post("/api/datasets/import", json={
        "root_path": str(root), "recursive": True, "read_sidecars": False,
        "compute_sha256": False, "probe_dimensions": True,
    })
    assert response.status_code == 200, response.text
    return int(client.get("/api/media", params={"page_size": 10}).json()["items"][0]["id"])


def test_custom_class_metadata_parses_yaml_and_json(tmp_path: Path):
    yaml_dir = tmp_path / "yaml_model"
    yaml_dir.mkdir()
    (yaml_dir / "data.yaml").write_text("names:\n  0: dragon\n  1: knight\n  2: magic_sword\n", encoding="utf-8")
    info = inspect_model_classes(yaml_dir, model_key="custom-yolo-local", provider="local", custom_model_type="yolo", allow_runtime_load=False)
    assert info["mode"] == "closed_set"
    assert [row["name"] for row in info["classes"]] == ["dragon", "knight", "magic_sword"]
    assert resolve_class_query(info["classes"], "knights")["class_ids"] == [1]

    json_dir = tmp_path / "json_model"
    json_dir.mkdir()
    (json_dir / "config.json").write_text('{"id2label":{"0":"background","1":"spaceship"}}', encoding="utf-8")
    info = inspect_model_classes(json_dir, model_key="custom-detector", custom_model_type="custom", allow_runtime_load=False)
    assert info["class_count"] == 2
    assert info["classes"][1] == {"id": 1, "name": "spaceship"}


def test_yolo_class_query_is_passed_to_inference_and_post_filtered(tmp_path: Path, monkeypatch):
    image_path = tmp_path / "image.png"
    Image.new("RGB", (100, 100), "white").save(image_path)
    calls: list[dict] = []

    class FakeBoxes:
        xyxy = [[1, 1, 20, 20], [10, 10, 40, 40], [50, 50, 90, 90]]
        conf = [0.99, 0.72, 0.61]
        cls = [0, 1, 1]

    class FakeResult:
        boxes = FakeBoxes()
        masks = None
        keypoints = None

    class FakeYOLO:
        names = {0: "cat", 1: "dog"}

        def __init__(self, model_path):
            self.model_path = model_path

        def predict(self, **kwargs):
            calls.append(kwargs)
            # Deliberately return a cat too, simulating a backend that ignored
            # its classes argument. The adapter must still remove it.
            return [FakeResult()]

    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=FakeYOLO))
    proposals = propose_with_yolo(
        image_path,
        "custom.pt",
        model_key="custom-yolo-local",
        annotation_type="bbox",
        threshold=0.05,
        options={"class_query": "dog", "max_proposals": 7, "iou": 0.8, "agnostic_nms": False},
    )
    assert calls and calls[0]["classes"] == [1]
    assert calls[0]["max_det"] == 7
    assert calls[0]["iou"] == 0.8
    assert len(proposals) == 2
    assert {proposal["label"] for proposal in proposals} == {"dog"}
    assert [proposal["confidence"] for proposal in proposals] == [0.72, 0.61]

    try:
        propose_with_yolo(image_path, "custom.pt", model_key="custom-yolo-local", options={"class_query": "dragon"})
    except AnnotationModelError as exc:
        assert "not supported" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Unsupported classes must not silently reuse identical detections.")


def test_spatial_class_endpoints_explain_closed_set_and_class_agnostic_models(tmp_path: Path):
    _, _, client = _app(tmp_path)
    detection = client.get("/api/spatial/detection/model-classes", params={"model_key": "yolo11n-detect"})
    assert detection.status_code == 200, detection.text
    det = detection.json()
    assert det["mode"] == "closed_set"
    assert det["class_count"] == 80
    assert {row["name"] for row in det["classes"]} >= {"person", "cat", "dog"}
    assert det["prompt_affects_geometry"] is True

    segmentation = client.get("/api/spatial/segmentation/model-classes", params={"model_key": "sam-vit-b"})
    assert segmentation.status_code == 200, segmentation.text
    seg = segmentation.json()
    assert seg["mode"] == "class_agnostic"
    assert seg["class_count"] == 0
    assert seg["prompt_affects_geometry"] is False
    assert "bbox prompt" in seg["message"]
    client.close()


def test_clear_preview_and_saved_generated_annotations_preserve_manual_work(tmp_path: Path):
    app, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    service = app.state.context.reference
    preview_dir = service.annotations_dir / "model_masks"
    preview_dir.mkdir(parents=True, exist_ok=True)
    loose_preview = preview_dir / "loose.png"
    saved_preview = preview_dir / "saved.png"
    Image.new("L", (128, 96), 255).save(loose_preview)
    Image.new("L", (128, 96), 255).save(saved_preview)

    service.add_annotation(media_id, "model-mask", "mask", mask_path=str(saved_preview), source="model", model_key="sam-vit-b")
    service.add_annotation(media_id, "manual-box", "bbox", bbox={"x1": 2, "y1": 2, "x2": 20, "y2": 20}, source="user")

    cleared = client.post("/api/spatial/segmentation/clear-preview", json={"mask_paths": [str(loose_preview), str(saved_preview)]}).json()
    assert cleared["deleted"] == 1
    assert not loose_preview.exists()
    assert saved_preview.exists()

    deleted = client.delete(f"/api/spatial/segmentation/generated/{media_id}").json()
    assert deleted["deleted_annotations"] == 1
    assert not saved_preview.exists()
    rows = service.list_annotations(media_id=media_id)
    assert len(rows) == 1
    assert rows[0]["label"] == "manual-box"
    client.close()



def test_sam_rejects_semantic_class_query_without_prompt_or_guide(tmp_path: Path, monkeypatch):
    _, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    checkpoint = tmp_path / "sam_vit_b.pth"
    checkpoint.write_bytes(b"checkpoint")
    called = {"sam": False}

    def should_not_run(*args, **kwargs):
        called["sam"] = True
        raise AssertionError("SAM must not run when a semantic class query has no spatial prompt or detector guide.")

    monkeypatch.setattr(reference_module, "propose_with_sam", should_not_run)
    response = client.post("/api/spatial/segmentation/propose", json={
        "media_id": media_id,
        "model_key": "sam-vit-b",
        "label": "dragon",
        "threshold": 0.05,
        "save": False,
        "options": {"local_model_path": str(checkpoint), "class_query": "dragon"},
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is False
    assert body["proposals"] == []
    assert "class-agnostic" in body["error"]
    assert "detector-guided" in body["error"]
    assert called["sam"] is False
    client.close()

def test_detector_guided_sam_sends_all_class_filtered_boxes_to_segmentation(tmp_path: Path, monkeypatch):
    app, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    checkpoint = tmp_path / "sam_vit_b.pth"
    checkpoint.write_bytes(b"checkpoint")
    captured: dict = {}

    def fake_yolo(image_path, model_path, *, model_key, label, threshold, annotation_type, device, output_dir, options):
        assert options["class_query"] == "person"
        return [
            {"label": "person", "annotation_type": "bbox", "bbox": {"x1": 5, "y1": 6, "x2": 45, "y2": 70}, "polygon": [], "confidence": 0.81, "source": "model", "model_key": model_key, "mask_path": "", "metadata": {}},
            {"label": "person", "annotation_type": "bbox", "bbox": {"x1": 55, "y1": 8, "x2": 110, "y2": 90}, "polygon": [], "confidence": 0.76, "source": "model", "model_key": model_key, "mask_path": "", "metadata": {}},
        ]

    def fake_sam(image_path, checkpoint_path, *, model_key, model_type, label, threshold, annotation_type, bbox_prompt, device, output_dir, options):
        captured["bbox_prompts"] = list(options.get("bbox_prompts") or [])
        return [
            {"label": label, "annotation_type": "mask", "bbox": box, "polygon": [[box["x1"], box["y1"]], [box["x2"], box["y1"]], [box["x2"], box["y2"]]], "confidence": 0.9 - index * 0.1, "source": "model", "model_key": model_key, "mask_path": "", "metadata": {"prompt_index": index}}
            for index, box in enumerate(captured["bbox_prompts"])
        ]

    monkeypatch.setattr(reference_module, "propose_with_yolo", fake_yolo)
    monkeypatch.setattr(reference_module, "propose_with_sam", fake_sam)

    response = client.post("/api/spatial/segmentation/propose", json={
        "media_id": media_id,
        "model_key": "sam-vit-b",
        "label": "person",
        "threshold": 0.05,
        "save": False,
        "options": {
            "local_model_path": str(checkpoint),
            "class_query": "person",
            "guide_detection_model_key": "yolo11n-detect",
            "guide_max_proposals": 8,
            "max_proposals": 8,
        },
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True, body
    assert body["count"] == 2
    assert len(captured["bbox_prompts"]) == 2
    assert body["conditioning"]["mode"] == "detector_guided_bbox_prompts"
    assert body["conditioning"]["guide_box_count"] == 2
    client.close()


def test_frontend_exposes_generated_clear_class_inspection_and_semantic_pipeline():
    source = (Path(__file__).resolve().parents[1] / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "Clear Generated Preview",
        "Inspect / Search Classes",
        "Semantic Class → Detector → SAM Pipeline",
        "guide_detection_model_key",
        "class_query",
        "max_det",
    ):
        assert text in source

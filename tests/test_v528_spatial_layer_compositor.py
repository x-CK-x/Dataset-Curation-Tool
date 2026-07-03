from __future__ import annotations

import base64
import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _app(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    return app, paths, TestClient(app)


def _import_image(client: TestClient, tmp_path: Path, *, split_color: bool = False) -> int:
    root = tmp_path / "dataset"
    root.mkdir(exist_ok=True)
    if split_color:
        image = Image.new("RGB", (100, 80), "red")
        ImageDraw.Draw(image).rectangle((50, 0, 99, 79), fill="blue")
    else:
        image = Image.new("RGB", (100, 80), (90, 110, 130))
    image.save(root / "sample.png")
    response = client.post("/api/datasets/import", json={
        "root_path": str(root), "recursive": True, "read_sidecars": False,
        "compute_sha256": False, "probe_dimensions": True,
    })
    assert response.status_code == 200, response.text
    return int(client.get("/api/media", params={"page_size": 10}).json()["items"][0]["id"])


def _add_box(client: TestClient, media_id: int, label: str, bbox: dict, *, source: str = "user", model_key: str = "", confidence: float | None = None):
    response = client.post("/api/reference/annotations", json={
        "media_id": media_id, "label": label, "annotation_type": "bbox", "bbox": bbox,
        "source": source, "model_key": model_key, "confidence": confidence,
        "metadata": {"spatial_task": "detection"}, "layer_name": label,
    })
    assert response.status_code == 200, response.text
    return response.json()


def _add_mask(client: TestClient, media_id: int, label: str, polygon: list[list[float]], *, source: str = "user"):
    response = client.post("/api/reference/annotations", json={
        "media_id": media_id, "label": label, "annotation_type": "mask", "polygon": polygon,
        "source": source, "metadata": {"spatial_task": "segmentation"}, "layer_name": label,
    })
    assert response.status_code == 200, response.text
    return response.json()


def _mask_data_url(width: int, height: int, box: tuple[int, int, int, int]) -> str:
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    ImageDraw.Draw(image).rectangle(box, fill=(255, 255, 255, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def test_bbox_layers_merge_edit_revision_lock_duplicate_and_reorder(tmp_path: Path):
    app, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    first = _add_box(client, media_id, "first", {"x1": 0, "y1": 0, "x2": 40, "y2": 40}, source="model", model_key="detector-a", confidence=0.9)
    second = _add_box(client, media_id, "second", {"x1": 20, "y1": 10, "x2": 60, "y2": 50}, source="user", confidence=0.2)
    first_id, second_id = int(first["id"]), int(second["id"])

    union = client.post("/api/spatial/detection/layers/merge", json={
        "media_id": media_id, "annotation_ids": [first_id, second_id], "operation": "union", "label": "union",
    })
    assert union.status_code == 200, union.text
    union_row = union.json()["annotation"]
    assert union_row["bbox"] == {"x1": 0.0, "y1": 0.0, "x2": 60.0, "y2": 50.0}
    assert union_row["source"] == "composite"
    assert union_row["parent_ids"] == [first_id, second_id]

    intersection = client.post("/api/spatial/detection/layers/merge", json={
        "media_id": media_id, "annotation_ids": [first_id, second_id], "operation": "intersection", "label": "intersection",
    }).json()["annotation"]
    assert intersection["bbox"] == {"x1": 20.0, "y1": 10.0, "x2": 40.0, "y2": 40.0}

    average = client.post("/api/spatial/detection/layers/merge", json={
        "media_id": media_id, "annotation_ids": [first_id, second_id], "operation": "average", "label": "average",
    }).json()["annotation"]
    assert average["bbox"] == {"x1": 10.0, "y1": 5.0, "x2": 50.0, "y2": 45.0}

    weighted = client.post("/api/spatial/detection/layers/merge", json={
        "media_id": media_id, "annotation_ids": [first_id, second_id], "operation": "confidence_weighted", "label": "weighted",
    }).json()["annotation"]
    assert round(weighted["bbox"]["x1"], 6) == round((0 * 0.9 + 20 * 0.2) / 1.1, 6)

    # Editing a raw model layer promotes it to user-edited while preserving provenance.
    edited = client.patch(f"/api/spatial/layers/{first_id}", json={
        "bbox": {"x1": 3, "y1": 4, "x2": 35, "y2": 36},
        "metadata": {"edited_in_test": True},
    })
    assert edited.status_code == 200, edited.text
    edited_row = edited.json()
    assert edited_row["source"] == "user-edited"
    assert edited_row["metadata"]["original_source"] == "model"
    assert edited_row["metadata"]["original_model_key"] == "detector-a"
    assert edited_row["metadata"]["manual_edit"] is True

    # Clearing raw model results must not delete a layer the user refined.
    cleared = client.delete(f"/api/spatial/detection/generated/{media_id}").json()
    assert cleared["deleted_annotations"] == 0
    assert client.get(f"/api/spatial/layers/{first_id}").status_code == 200

    revisions = client.get(f"/api/spatial/layers/{first_id}/revisions").json()
    assert revisions and revisions[0]["snapshot"]["bbox"] == {"x1": 0, "y1": 0, "x2": 40, "y2": 40}
    restored = client.post(f"/api/spatial/layers/{first_id}/revisions/{revisions[0]['id']}/restore")
    assert restored.status_code == 200, restored.text
    assert restored.json()["bbox"] == {"x1": 0, "y1": 0, "x2": 40, "y2": 40}

    locked = client.patch(f"/api/spatial/layers/{first_id}", json={"locked": True})
    assert locked.status_code == 200
    refused = client.patch(f"/api/spatial/layers/{first_id}", json={"bbox": {"x1": 1, "y1": 1, "x2": 10, "y2": 10}})
    assert refused.status_code == 400
    visibility = client.patch(f"/api/spatial/layers/{first_id}", json={"visible": False})
    assert visibility.status_code == 200 and visibility.json()["visible"] is False
    client.patch(f"/api/spatial/layers/{first_id}", json={"locked": False})

    duplicate = client.post(f"/api/spatial/layers/{second_id}/duplicate", json={"layer_name": "second copy"})
    assert duplicate.status_code == 200, duplicate.text
    duplicate_id = int(duplicate.json()["id"])
    reordered = client.post("/api/spatial/layers/reorder", json={
        "media_id": media_id, "annotation_ids": [duplicate_id, second_id, first_id], "task": "detection",
    })
    assert reordered.status_code == 200, reordered.text
    state = client.get(f"/api/spatial/detection/state/{media_id}").json()["annotations"]
    selected = [row for row in state if row["id"] in {duplicate_id, second_id, first_id}]
    assert [row["id"] for row in selected] == [duplicate_id, second_id, first_id]
    assert [row["layer_order"] for row in selected] == [1, 2, 3]
    client.close()


def test_mask_layers_union_intersection_subtract_xor_and_pixel_edit(tmp_path: Path):
    _, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    first = _add_mask(client, media_id, "left", [[5, 5], [45, 5], [45, 45], [5, 45]], source="model")
    second = _add_mask(client, media_id, "right", [[25, 5], [65, 5], [65, 45], [25, 45]])
    first_id, second_id = int(first["id"]), int(second["id"])

    def merged(operation: str, *, base: int | None = None):
        response = client.post("/api/spatial/segmentation/layers/merge", json={
            "media_id": media_id, "annotation_ids": [first_id, second_id], "operation": operation,
            "label": operation, "threshold": 1, "base_annotation_id": base,
        })
        assert response.status_code == 200, response.text
        row = response.json()["annotation"]
        assert Path(row["mask_path"]).exists()
        return row

    union = merged("union")
    intersection = merged("intersection")
    subtract = merged("subtract", base=first_id)
    xor = merged("xor")

    with Image.open(union["mask_path"]) as image:
        assert image.getpixel((10, 10)) > 0 and image.getpixel((55, 10)) > 0
    with Image.open(intersection["mask_path"]) as image:
        assert image.getpixel((10, 10)) == 0 and image.getpixel((30, 10)) > 0
    with Image.open(subtract["mask_path"]) as image:
        assert image.getpixel((10, 10)) > 0 and image.getpixel((30, 10)) == 0
    with Image.open(xor["mask_path"]) as image:
        assert image.getpixel((10, 10)) > 0 and image.getpixel((30, 10)) == 0 and image.getpixel((55, 10)) > 0

    # Raster editor can create and update a persistent layer with revisions.
    create = client.post("/api/spatial/segmentation/save-mask-layer", json={
        "media_id": media_id, "mask_data_url": _mask_data_url(100, 80, (10, 50, 25, 70)),
        "label": "painted", "layer_name": "painted layer", "source": "user", "color": "#ff00ff", "opacity": 0.4,
    })
    assert create.status_code == 200, create.text
    painted = create.json()
    painted_id = int(painted["id"])
    assert Path(painted["mask_path"]).exists()
    update = client.post("/api/spatial/segmentation/save-mask-layer", json={
        "media_id": media_id, "annotation_id": painted_id,
        "mask_data_url": _mask_data_url(100, 80, (30, 50, 50, 70)),
        "label": "painted-edited", "layer_name": "painted layer", "source": "user", "color": "#00ffff", "opacity": 0.7,
    })
    assert update.status_code == 200, update.text
    assert update.json()["updated"] is True
    assert update.json()["bbox"] == {"x1": 30.0, "y1": 50.0, "x2": 51.0, "y2": 71.0}
    assert client.get(f"/api/spatial/layers/{painted_id}/revisions").json()

    # Editing a model mask also protects it from bulk raw-model cleanup.
    edited_model = client.post("/api/spatial/segmentation/save-mask-layer", json={
        "media_id": media_id, "annotation_id": first_id,
        "mask_data_url": _mask_data_url(100, 80, (2, 2, 20, 20)),
        "label": "refined model mask", "source": "model", "model_key": "sam-vit-b",
    })
    assert edited_model.status_code == 200, edited_model.text
    assert edited_model.json()["source"] == "user-edited"
    cleared = client.delete(f"/api/spatial/segmentation/generated/{media_id}").json()
    assert first_id not in [row.get("id") for row in cleared.get("rows", [])]
    assert client.get(f"/api/spatial/layers/{first_id}").status_code == 200
    client.close()


def test_magic_select_color_methods_and_preview_cleanup(tmp_path: Path):
    _, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path, split_color=True)
    flood = client.post("/api/spatial/segmentation/magic-select", json={
        "media_id": media_id, "x": 10, "y": 10, "method": "flood_fill", "tolerance": 5,
    })
    assert flood.status_code == 200, flood.text
    flood_row = flood.json()
    assert 3500 <= flood_row["pixel_count"] <= 4500
    assert Path(flood_row["mask_path"]).exists()
    with Image.open(flood_row["mask_path"]) as mask:
        assert mask.getpixel((10, 10)) > 0
        assert mask.getpixel((80, 10)) == 0

    similar = client.post("/api/spatial/segmentation/magic-select", json={
        "media_id": media_id, "x": 80, "y": 10, "method": "color_range", "tolerance": 5,
        "feather": 0, "grow": 0, "invert": False,
    })
    assert similar.status_code == 200, similar.text
    similar_row = similar.json()
    with Image.open(similar_row["mask_path"]) as mask:
        assert mask.getpixel((10, 10)) == 0
        assert mask.getpixel((80, 10)) > 0

    cleared = client.post("/api/spatial/segmentation/clear-preview", json={
        "mask_paths": [flood_row["mask_path"], similar_row["mask_path"]],
    })
    assert cleared.status_code == 200
    assert cleared.json()["deleted"] == 2
    client.close()


def test_selected_model_preview_layers_can_be_persisted_and_composed_later(tmp_path: Path):
    app, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    preview_dir = app.state.context.reference.annotations_dir / "model_masks"
    preview_dir.mkdir(parents=True, exist_ok=True)
    mask_path = preview_dir / "proposal.png"
    Image.new("L", (100, 80), 0).save(mask_path)
    with Image.open(mask_path) as image:
        array = image.copy()
    draw = ImageDraw.Draw(array)
    draw.rectangle((10, 10, 30, 30), fill=255)
    array.save(mask_path)

    proposal = {
        "label": "model object", "annotation_type": "mask", "mask_path": str(mask_path),
        "bbox": {"x1": 10, "y1": 10, "x2": 31, "y2": 31}, "polygon": [],
        "source": "model", "model_key": "sam-vit-b", "confidence": 0.88,
        "metadata": {"run_id": "preview-1"},
    }
    persisted = client.post("/api/spatial/segmentation/persist-preview", json={
        "media_id": media_id, "proposals": [proposal], "label": "kept model part",
    })
    assert persisted.status_code == 200, persisted.text
    body = persisted.json()
    assert body["count"] == 1
    saved = body["saved"][0]
    assert saved["source"] == "model"
    assert saved["model_key"] == "sam-vit-b"
    assert saved["metadata"]["persisted_from_preview"] is True

    # Preview cleanup sees the DB reference and preserves the persistent file.
    cleanup = client.post("/api/spatial/segmentation/clear-preview", json={"mask_paths": [str(mask_path)]}).json()
    assert cleanup["deleted"] == 0
    assert mask_path.exists()
    client.close()


def test_frontend_exposes_layer_stack_merge_editing_and_mask_tools():
    source = (Path(__file__).resolve().parents[1] / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "Box Layer Stack & Compositor",
        "Mask Layer Stack & Compositor",
        "Combine Selected ${isDetection ? 'Boxes' : 'Masks'}",
        "Persist Selected Preview Layers",
        "Load Selected Preview Box into Editor",
        "Load Selected Preview Masks into Editor",
        "Add Blank Persistent Layer",
        "Save as New Mask Layer",
        "Update Selected Mask Layer",
        "Brush",
        "Eraser",
        "Freehand Lasso",
        "Ellipse Select",
        "Magic Select",
        "Non-contiguous Similar Color",
        "Undo Saved Edit",
        "Move Up",
        "Move Down",
    ):
        assert text in source


def test_soft_mask_compositing_preserves_alpha_strengths():
    from data_curation_tool.services.reference_service import combine_masks
    import numpy as np

    first = np.array([[0, 64, 128, 255]], dtype=np.uint8)
    second = np.array([[32, 96, 64, 128]], dtype=np.uint8)
    assert combine_masks([first, second], "union", threshold=1).tolist() == [[32, 96, 128, 255]]
    assert combine_masks([first, second], "intersection", threshold=1).tolist() == [[0, 64, 64, 128]]
    assert combine_masks([first, second], "subtract", threshold=1).tolist() == [[0, 0, 64, 127]]
    assert combine_masks([first, second], "xor", threshold=1).tolist() == [[32, 32, 64, 127]]


def test_layer_patch_accepts_pixel_mask_data_and_updates_same_layer(tmp_path: Path):
    _, _, client = _app(tmp_path)
    media_id = _import_image(client, tmp_path)
    created = client.post("/api/spatial/segmentation/save-mask-layer", json={
        "media_id": media_id,
        "mask_data_url": _mask_data_url(100, 80, (2, 2, 12, 12)),
        "label": "patchable",
    })
    assert created.status_code == 200, created.text
    annotation_id = int(created.json()["id"])
    patched = client.patch(f"/api/spatial/layers/{annotation_id}", json={
        "mask_data_url": _mask_data_url(100, 80, (40, 20, 60, 50)),
        "label": "patched pixels",
        "color": "#123456",
        "opacity": 0.35,
    })
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert int(body["id"]) == annotation_id
    assert body["bbox"] == {"x1": 40.0, "y1": 20.0, "x2": 61.0, "y2": 51.0}
    assert body["label"] == "patched pixels"
    assert body["color"] == "#123456"
    assert body["opacity"] == 0.35
    client.close()


def test_feature_audit_reports_persistent_spatial_layer_capability(tmp_path: Path):
    _, _, client = _app(tmp_path)
    response = client.get('/api/system/feature-audit')
    assert response.status_code == 200, response.text
    groups = response.json()['feature_groups']
    assert any('persistent editable spatial layers' in value for value in groups)
    client.close()

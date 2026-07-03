from __future__ import annotations

import base64
import io
import os
import tempfile
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DCT_SKIP_STARTUP_TAG_SYNC", "1")

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _mask_data_url(width: int, height: int, rect: tuple[int, int, int, int]) -> str:
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    ImageDraw.Draw(image).rectangle(rect, fill=(255, 255, 255, 255))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode("ascii")


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    frontend = (project / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    required_ui = (
        "Box Layer Stack & Compositor", "Mask Layer Stack & Compositor",
        "Persist Selected Preview Layers", "Add Blank Persistent Layer",
        "Freehand Lasso", "Ellipse Select", "Magic Select", "Brush", "Eraser",
        "Update Selected Box Layer", "Update Selected Mask Layer", "Undo Saved Edit",
    )
    missing = [value for value in required_ui if value not in frontend]
    assert not missing, missing

    with tempfile.TemporaryDirectory(prefix="dct-v528-") as temp:
        root = Path(temp)
        image_root = root / "dataset"
        image_root.mkdir()
        Image.new("RGB", (96, 64), (80, 100, 120)).save(image_root / "sample.png")
        app = create_app(AppPaths.create(runtime=root / "runtime", models=root / "models", outputs=root / "outputs"))
        with TestClient(app) as client:
            imported = client.post("/api/datasets/import", json={
                "root_path": str(image_root), "recursive": True, "read_sidecars": False,
                "compute_sha256": False, "probe_dimensions": True,
            })
            assert imported.status_code == 200, imported.text
            job_id = int(imported.json().get("job_id") or 0)
            deadline = time.time() + 20
            while job_id and time.time() < deadline:
                jobs = client.get("/api/jobs").json()
                job = next((row for row in jobs if int(row.get("id") or 0) == job_id), {})
                if job.get("status") in {"completed", "failed", "cancelled"}:
                    assert job.get("status") == "completed", job
                    break
                time.sleep(0.05)
            media_rows = client.get("/api/media", params={"page_size": 10}).json()["items"]
            assert media_rows, "Dataset import did not create a media row."
            media_id = int(media_rows[0]["id"])

            boxes = []
            for label, bbox, source in (
                ("model", {"x1": 2, "y1": 3, "x2": 35, "y2": 40}, "model"),
                ("manual", {"x1": 20, "y1": 10, "x2": 70, "y2": 55}, "user"),
            ):
                response = client.post("/api/reference/annotations", json={
                    "media_id": media_id, "label": label, "annotation_type": "bbox",
                    "bbox": bbox, "source": source, "metadata": {"spatial_task": "detection"},
                })
                assert response.status_code == 200, response.text
                boxes.append(response.json())
            combined_box = client.post("/api/spatial/detection/layers/merge", json={
                "media_id": media_id, "annotation_ids": [row["id"] for row in boxes],
                "operation": "union", "label": "combined",
            })
            assert combined_box.status_code == 200, combined_box.text
            assert combined_box.json()["annotation"]["bbox"]["x2"] == 70.0

            masks = []
            for index, rect in enumerate(((4, 4, 42, 45), (30, 8, 82, 55)), start=1):
                response = client.post("/api/spatial/segmentation/save-mask-layer", json={
                    "media_id": media_id, "mask_data_url": _mask_data_url(96, 64, rect),
                    "label": f"mask-{index}", "source": "user",
                })
                assert response.status_code == 200, response.text
                masks.append(response.json())
            combined_mask = client.post("/api/spatial/segmentation/layers/merge", json={
                "media_id": media_id, "annotation_ids": [row["id"] for row in masks],
                "operation": "union", "label": "combined-mask",
            })
            assert combined_mask.status_code == 200, combined_mask.text
            combined_path = Path(combined_mask.json()["annotation"]["mask_path"])
            assert combined_path.exists()

            edited = client.patch(f"/api/spatial/layers/{boxes[0]['id']}", json={
                "bbox": {"x1": 5, "y1": 5, "x2": 30, "y2": 30},
            })
            assert edited.status_code == 200, edited.text
            assert edited.json()["source"] == "user-edited"

            state = client.get(f"/api/spatial/segmentation/state/{media_id}").json()
            assert len(state["annotations"]) >= 3

    print("v5.28 persistent spatial-layer verification passed")
    print({"box_layers": 3, "mask_layers": 3, "frontend_tools": len(required_ui)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
import tempfile
import types
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_curation_tool.services.annotation_classes import inspect_model_classes, resolve_class_query
from data_curation_tool.services.annotation_models import AnnotationModelError, propose_with_yolo


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="dct_v527_spatial_verify_"))
    model_dir = root / "custom_model"
    model_dir.mkdir()
    (model_dir / "data.yaml").write_text("names:\n  0: cat\n  1: dog\n", encoding="utf-8")
    info = inspect_model_classes(model_dir, model_key="custom-yolo-local", custom_model_type="yolo", allow_runtime_load=False)
    assert info["class_count"] == 2, info
    assert resolve_class_query(info["classes"], "dog")["class_ids"] == [1]

    image_path = root / "image.png"
    Image.new("RGB", (100, 100), "white").save(image_path)
    calls = []

    class Boxes:
        xyxy = [[1, 1, 20, 20], [30, 30, 80, 80]]
        conf = [0.95, 0.65]
        cls = [0, 1]

    class Result:
        boxes = Boxes()
        masks = None
        keypoints = None

    class FakeYOLO:
        names = {0: "cat", 1: "dog"}

        def __init__(self, path):
            self.path = path

        def predict(self, **kwargs):
            calls.append(kwargs)
            return [Result()]

    previous = sys.modules.get("ultralytics")
    sys.modules["ultralytics"] = types.SimpleNamespace(YOLO=FakeYOLO)
    try:
        proposals = propose_with_yolo(
            image_path,
            "custom.pt",
            model_key="custom-yolo-local",
            options={"class_query": "dog", "max_det": 20, "iou": 0.8},
        )
        assert calls[0]["classes"] == [1], calls
        assert calls[0]["max_det"] == 20, calls
        assert len(proposals) == 1 and proposals[0]["label"] == "dog", proposals
        try:
            propose_with_yolo(image_path, "custom.pt", model_key="custom-yolo-local", options={"class_query": "dragon"})
        except AnnotationModelError:
            pass
        else:
            raise AssertionError("Unsupported class tokens must fail.")
    finally:
        if previous is None:
            sys.modules.pop("ultralytics", None)
        else:
            sys.modules["ultralytics"] = previous

    frontend = (Path(__file__).resolve().parents[1] / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for required in (
        "Inspect / Search Classes",
        "Clear Generated Preview",
        "Semantic Class → Detector → SAM Pipeline",
        "guide_detection_model_key",
        "max_det",
    ):
        assert required in frontend, required

    print("v5.27 class-aware spatial verification passed")
    print({"class_count": info["class_count"], "filtered_proposals": len(proposals), "class_filter": calls[0]["classes"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

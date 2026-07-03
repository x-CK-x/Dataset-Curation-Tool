from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("DCT_SKIP_STARTUP_TAG_SYNC", "1")

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    source = (project / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    required_ui = [
        "Detection & Boxes", "Segmentation & Masks", "Pose & 3D",
        "/api/spatial/detection/propose", "/api/spatial/segmentation/propose",
        "/api/augment/external-tool/launch-now", "Launch / Send Selected Now",
    ]
    missing = [item for item in required_ui if item not in source]
    if missing:
        raise SystemExit(f"Missing v5.26 UI contracts: {missing}")

    with TemporaryDirectory(prefix="dct-v526-") as temp:
        root = Path(temp)
        app = create_app(AppPaths.create(runtime=root / "runtime", models=root / "models", outputs=root / "outputs"))
        with TestClient(app) as client:
            detection = {row["name"] for row in client.get("/api/spatial/detection/models").json()}
            segmentation = {row["name"] for row in client.get("/api/spatial/segmentation/models").json()}
            assert "yolo11n-detect" in detection
            assert "sam-vit-b" not in detection
            assert "sam-vit-b" in segmentation
            assert "yolo11n-detect" not in segmentation
            tools = client.get("/api/augment/external-tools").json()["tools"]
            keys = {row["key"] for row in tools}
            assert {"topaz_photo_ai", "topaz_gigapixel", "krita", "comfyui"}.issubset(keys)
    print("v5.26 external-app and separated-spatial verification passed")


if __name__ == "__main__":
    main()

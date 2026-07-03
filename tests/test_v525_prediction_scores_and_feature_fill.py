from pathlib import Path
import sys

from PIL import Image
from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.database import Database, now_iso
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.media_service import MediaService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_tag_prediction_scores_are_persisted_and_analytics_available(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    media = MediaService(db, paths)
    db.execute("INSERT INTO datasets(name, root_path, settings_json, created_at) VALUES (?, ?, '{}', ?)", ("d", str(tmp_path), now_iso()))
    ds_id = db.query_one("SELECT id FROM datasets")["id"]
    img = tmp_path / "a.png"
    Image.new("RGB", (32, 32), "white").save(img)
    media_id = db.upsert_media({"dataset_id": ds_id, "path": str(img), "relative_path": img.name, "media_type": "image", "ext": "png", "width": 32, "height": 32, "size_bytes": img.stat().st_size})
    db.replace_tags(media_id, [("solo", "general"), ("rating_explicit", "rating")], source="test")
    media.add_prediction(media_id, 101, "model-a", "tag", {"tags": [["solo", 0.91], ["blue_eyes", 0.72]]})
    media.add_prediction(media_id, 102, "model-b", "rating", {"classes": [["rating_explicit", 0.88]]})
    client = TestClient(create_app(paths))
    scores = client.get(f"/api/models/tag-scores/{media_id}").json()["scores"]
    assert scores["solo"][0]["model_name"] == "model-a"
    assert scores["rating_explicit"][0]["model_name"] == "model-b"
    analytics = client.post("/api/models/tag-score-analytics", json={"dataset_id": ds_id, "limit": 20}).json()
    assert "solo" in analytics["tags"]
    assert "model-a" in analytics["models"]


def test_v525_model_catalog_has_missing_feature_families(tmp_path: Path):
    c = _client(tmp_path)
    models = {m["name"]: m for m in c.get("/api/models").json()}
    for key in [
        "wd-convnext-tagger-v3", "wd-eva02-large-tagger-v3", "blip2-opt-2.7b-captioner", "instructblip-vicuna-7b",
        "real-esrgan-x4plus", "real-esrgan-animevideov3", "swin2sr-realworld-x4", "detr-resnet50-detector", "u2net-saliency-mask",
        "topaz_gigapixel", "topaz_photo_ai", "redrocket-jtp-3", "redrocket-e6-visual-ratings",
    ]:
        assert key in models
    assert "upscale" in models["real-esrgan-x4plus"]["capabilities"]
    assert "tag" in models["wd-convnext-tagger-v3"]["capabilities"]
    assert "crop" in models["detr-resnet50-detector"]["capabilities"]


def test_external_image_tool_route_queues_job(tmp_path: Path):
    c = _client(tmp_path)
    # No media selected: still validates endpoint schema and queues a job.  The job
    # returns a no-op result instead of needing a real licensed external tool.
    r = c.post("/api/augment/external-tool", json={"media_ids": [], "tool_name": "topaz_photo_ai", "mode": "open", "executable_path": sys.executable})
    assert r.status_code == 200
    assert r.json()["status"] == "queued"

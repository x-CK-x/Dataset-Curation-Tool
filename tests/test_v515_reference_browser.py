import os
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DatasetCreate


def test_reference_finder_demo_query_annotation_and_browser_status(tmp_path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "1")
    paths = AppPaths.create(tmp_path / "runtime")
    app = create_app(paths)
    client = TestClient(app)
    ctx = app.state.context

    image_dir = tmp_path / "images"
    image_dir.mkdir()
    colors = [(255, 0, 0), (250, 5, 5), (0, 0, 255)]
    for idx, color in enumerate(colors):
        Image.new("RGB", (64, 64), color).save(image_dir / f"{idx}.png")
        (image_dir / f"{idx}.txt").write_text("red, solo" if idx < 2 else "blue, solo", encoding="utf-8")

    imported = ctx.datasets.import_folder(
        DatasetCreate(
            root_path=str(image_dir),
            recursive=True,
            read_sidecars=True,
            skip_duplicates=False,
            auto_sync_tag_dictionary=False,
        ),
        progress=lambda *_: None,
    )
    assert imported["imported"] == 3

    run = ctx.reference.run_search(
        {
            "target_name": "red thing",
            "reference_paths": [str(image_dir / "0.png")],
            "dataset_id": imported["dataset_id"],
            "pipeline": "demo_colorhash",
            "threshold": 0.55,
            "save_all_annotations": True,
        },
        None,
        lambda *_: None,
    )
    assert run["processed"] == 3
    assert run["matches"] >= 2

    results = client.get("/api/reference/results?limit=10").json()
    assert results
    assert results[0]["target_name"] == "red thing"

    verify = client.post("/api/reference/verify", json={"detection_id": results[0]["id"], "label": "correct"}).json()
    assert verify["label"] == "correct"

    query = client.post(
        "/api/reference/queries/evaluate",
        json={"target_name": "red thing", "query": "[tag:red]", "dataset_id": imported["dataset_id"]},
    ).json()
    assert query["metrics"]["known_positive_returned"] >= 1
    assert query["metrics"]["precision_known"] >= 0

    media = client.get("/api/media").json()["items"]
    ann = client.post(
        "/api/reference/annotations",
        json={"media_id": media[0]["id"], "label": "red thing", "annotation_type": "bbox", "bbox": {"x1": 1, "y1": 2, "x2": 20, "y2": 22}},
    ).json()
    assert ann["annotation_id"] > 0
    assert ann["bbox"]["x2"] == 20

    browser = client.get("/api/browser/status").json()
    assert browser["private_mode_default"] is True
    assert "geckodriver_path" in browser


def test_reference_query_parser_boolean_logic(tmp_path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "1")
    paths = AppPaths.create(tmp_path / "runtime")
    app = create_app(paths)
    ctx = app.state.context
    db = ctx.db
    dataset_id = db.insert_dataset("q", str(tmp_path), {})
    media_ids = []
    for idx in range(3):
        media_ids.append(db.upsert_media({"dataset_id": dataset_id, "path": str(tmp_path / f"{idx}.png"), "relative_path": f"{idx}.png", "media_type": "image", "ext": "png", "size_bytes": 1}))
    db.replace_tags(media_ids[0], [("red", "general"), ("solo", "general")])
    db.replace_tags(media_ids[1], [("red", "general"), ("group", "general")])
    db.replace_tags(media_ids[2], [("blue", "general"), ("solo", "general")])
    target_id = ctx.reference.upsert_target("red thing")
    # Seed known memory through a real verification-like table insert path.
    ctx.db.execute("INSERT INTO reference_verifications(detection_id, media_id, target_id, user_label, notes, created_at) VALUES (NULL, ?, ?, 'correct', '', datetime('now'))", (media_ids[0], target_id))
    ctx.db.execute("INSERT INTO reference_verifications(detection_id, media_id, target_id, user_label, notes, created_at) VALUES (NULL, ?, ?, 'incorrect', '', datetime('now'))", (media_ids[2], target_id))
    result = ctx.reference.evaluate_query("red thing", "[tag:red] AND NOT [tag:group]", dataset_id=dataset_id, store=False)
    assert result["result_ids"] == [media_ids[0]]
    assert result["metrics"]["known_positive_returned"] == 1

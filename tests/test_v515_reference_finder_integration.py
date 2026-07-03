from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_reference_finder_run_verify_and_query_optimizer(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    red = root / "red.png"
    blue = root / "blue.png"
    Image.new("RGB", (48, 48), (255, 0, 0)).save(red)
    Image.new("RGB", (48, 48), (0, 0, 255)).save(blue)
    red.with_suffix(".txt").write_text("red_character, solo", encoding="utf-8")
    blue.with_suffix(".txt").write_text("blue_character, solo", encoding="utf-8")

    client = _client(tmp_path)
    r = client.post("/api/datasets/import", json={"root_path": str(root), "read_sidecars": True, "compute_sha256": True})
    assert r.status_code == 200
    job = client.get(f"/api/jobs/{r.json()['job_id']}").json()
    assert job["status"] == "completed"
    dataset_id = job["result"]["dataset_id"]

    status = client.get("/api/reference/status").json()
    assert any(p["key"] == "demo_colorhash" for p in status["pipelines"])

    run = client.post(
        "/api/reference/run",
        json={
            "target_name": "red target",
            "reference_paths": [str(red)],
            "dataset_id": dataset_id,
            "pipeline": "demo_colorhash",
            "threshold": 0.98,
            "save_all_annotations": True,
        },
    )
    assert run.status_code == 200
    run_job = client.get(f"/api/jobs/{run.json()['job_id']}").json()
    assert run_job["status"] == "completed"
    assert run_job["result"]["processed"] == 2
    assert run_job["result"]["matches"] >= 1

    results = client.get("/api/reference/results", params={"target_name": "red target", "limit": 10}).json()
    assert results
    match = next(row for row in results if row["decision"] == "match")
    verify = client.post("/api/reference/verify", json={"detection_id": match["id"], "label": "correct"})
    assert verify.status_code == 200
    assert verify.json()["updated"] is True

    query = client.post(
        "/api/reference/queries/evaluate",
        json={"target_name": "red target", "query": "[tag:red_character]", "dataset_id": dataset_id},
    )
    assert query.status_code == 200
    assert query.json()["metrics"]["known_positive_returned"] >= 1


def test_reference_finder_ui_and_browser_status_are_wired(tmp_path: Path):
    client = _client(tmp_path)
    browser = client.get("/api/browser/status").json()
    assert browser["private_mode_default"] is True
    app_js = Path(__file__).resolve().parents[1] / "data_curation_tool" / "static" / "app.js"
    text = app_js.read_text(encoding="utf-8")
    assert "Reference Finder" in text
    assert "/api/reference/run" in text
    assert "Source Browser" in text

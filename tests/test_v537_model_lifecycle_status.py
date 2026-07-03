from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_model_lifecycle_status_endpoint_load_and_inference(tmp_path: Path):
    client = _client(tmp_path)

    initial = client.get("/api/models/status").json()
    assert set(["download", "load", "inference", "training"]).issubset(initial["aggregate"].keys())
    assert "dataset-assistant" in initial["models"]
    assert initial["models"]["dataset-assistant"]["load"]["state"] == "idle"

    load_job = client.post("/api/models/load", json={"model_name": "dataset-assistant", "device": "cpu"}).json()
    assert load_job["status"] == "queued"
    status = client.get("/api/models/status").json()
    load = status["models"]["dataset-assistant"]["load"]
    assert load["state"] == "completed"
    assert load["percent"] == 100
    assert load["job_id"] == load_job["job_id"]

    models = {row["name"]: row for row in client.get("/api/models").json()}
    assert models["dataset-assistant"]["loaded"] is True

    run_job = client.post("/api/models/run", json={"model_name": "dataset-assistant", "task": "tag", "media_ids": []}).json()
    assert run_job["status"] == "queued"
    status = client.get("/api/models/status").json()
    inference = status["models"]["dataset-assistant"]["inference"]
    assert inference["state"] == "completed"
    assert inference["percent"] == 100
    assert inference["job_id"] == run_job["job_id"]
    assert "No media selected" in inference["message"]


def test_training_scaffold_updates_training_status_circle(tmp_path: Path):
    client = _client(tmp_path)
    result = client.post(
        "/api/reference/training-jobs",
        json={"name": "unit_training_scaffold", "task": "detection", "model_key": "rule-based-filename", "config": {"epochs": 1}},
    ).json()
    assert result["training_job_id"]
    status = client.get("/api/models/status").json()
    training = status["models"]["rule-based-filename"]["training"]
    assert training["state"] == "completed"
    assert training["percent"] == 100
    assert "Training scaffold created" in training["message"]

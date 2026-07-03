from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "data_curation_tool" / "static" / "app.js"


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def _create_media(client: TestClient, tmp_path: Path, filename: str = "blue_cat_character.png") -> int:
    ctx = client.app.state.context
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir(exist_ok=True)
    image_path = dataset_dir / filename
    Image.new("RGB", (24, 24), "white").save(image_path)
    dataset_id = ctx.db.insert_dataset("model-refresh", str(dataset_dir), {})
    return ctx.db.upsert_media(
        {
            "dataset_id": dataset_id,
            "path": str(image_path),
            "relative_path": image_path.name,
            "media_type": "image",
            "ext": "png",
            "width": 24,
            "height": 24,
            "size_bytes": image_path.stat().st_size,
        }
    )


def test_loading_an_already_loaded_model_is_a_completed_noop(tmp_path: Path):
    client = _client(tmp_path)
    first = client.post("/api/models/load", json={"model_name": "dataset-assistant", "device": "cpu"}).json()
    assert first["status"] == "queued"

    second = client.post("/api/models/load", json={"model_name": "dataset-assistant", "device": "cpu"}).json()
    assert second["status"] == "completed"
    assert second["already_loaded"] is True
    assert second["job_id"] is None

    jobs = client.get("/api/jobs").json()
    load_jobs = [j for j in jobs if j["type"] == "model_load" and j["params"].get("model_name") == "dataset-assistant"]
    assert len(load_jobs) == 1


def test_loaded_model_inference_applies_tags_without_reassigning_load_job(tmp_path: Path):
    client = _client(tmp_path)
    media_id = _create_media(client, tmp_path)

    load = client.post("/api/models/load", json={"model_name": "rule-based-filename", "device": "cpu"}).json()
    run = client.post(
        "/api/models/run",
        json={
            "model_name": "rule-based-filename",
            "task": "tag",
            "media_ids": [media_id],
            "apply_tags": True,
            "threshold": 0.1,
            "device": "cpu",
        },
    ).json()

    status = client.get("/api/models/status/rule-based-filename").json()
    assert status["stages"]["load"]["job_id"] == load["job_id"]
    assert status["stages"]["load"]["state"] == "completed"
    assert status["stages"]["inference"]["job_id"] == run["job_id"]
    assert status["stages"]["inference"]["state"] == "completed"

    media = client.get(f"/api/media/{media_id}").json()
    assert {"blue", "cat", "character"}.issubset(set(media["tags"]))


def test_frontend_refreshes_model_tag_results_without_reload_and_preserves_typing_focus():
    js = APP_JS.read_text(encoding="utf-8")
    assert "function renderOrDeferForEditing" in js
    assert "function activeControlSnapshot" in js
    assert "function restoreActiveControl" in js
    assert "function refreshMediaRows" in js
    assert "function refreshCompletedModelJobById" in js
    assert "refreshMediaAfterCompletedModelJobs(completedModelJobs)" in js
    assert "state.lastCompletedModelJobIds" in js
    assert "raw.dataset.noPersist = '1'" in js
    assert "captionText.dataset.noPersist = '1'" in js
    assert "'data-form-key': `${title}-criteria`" in js
    assert "if (operation.value !== 'preview') await refreshMediaRows(mediaIds);" in js
    assert "await refreshCompletedModelJobById(r.job_id);" in js
    assert "no duplicate load job was queued" in js

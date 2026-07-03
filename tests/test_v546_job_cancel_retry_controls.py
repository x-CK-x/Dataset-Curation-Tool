from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.database import Database
from data_curation_tool.jobs import JobManager
from data_curation_tool.paths import AppPaths


def test_download_only_cancel_includes_startup_tag_dictionary_sync(tmp_path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tag_job = db.create_job("tag_dictionary_startup_sync", {"profile_key": "e621"})
    model_job = db.create_job("model_download", {"model_name": "gemma-4-e4b-it"})
    import_job = db.create_job("dataset_import", {})
    jobs = JobManager(db, max_workers=2)
    try:
        result = jobs.cancel_jobs(download_only=True, include_running=True)
        assert tag_job in result["cancelled"]
        assert model_job in result["cancelled"]
        assert import_job not in result["cancelled"]
        assert db.query_one("SELECT status FROM jobs WHERE id=?", (tag_job,))["status"] == "cancelled"
    finally:
        jobs.shutdown(wait=False)


def test_retry_failed_download_job_resubmits_with_force_download(tmp_path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "1")
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    c = app.state.context
    seen = {}

    def fake_run(payload, progress):
        seen["force_download"] = bool(payload.force_download)
        progress(1.0, "fake retry completed")
        return {"downloaded": 0, "force_download": bool(payload.force_download)}

    c.downloads.run = fake_run  # type: ignore[method-assign]
    failed_id = c.db.create_job("download", {"preset_names": [], "confirmed_authorized": True, "force_download": False})
    c.db.update_job(failed_id, status="failed", message="failed once", error="boom", finished=True)

    with TestClient(app) as client:
        result = client.post("/api/jobs/retry", json={"job_ids": [failed_id], "failed_only": True, "force_download": True}).json()
        assert result["count"] == 1
        assert result["retried"][0]["original_job_id"] == failed_id
        assert seen["force_download"] is True
        new_job = client.get(f"/api/jobs/{result['retried'][0]['job_id']}").json()
        assert new_job["status"] == "completed"
        assert new_job["result"]["force_download"] is True


def test_jobs_ui_persists_checked_selection_and_exposes_retry_control():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "jobSelections: new Set()" in app_js
    assert "data-no-persist': '1'" in app_js
    assert "Retry Checked Failed Downloads" in app_js
    assert "Retry from scratch" in app_js
    assert "/api/jobs/retry" in app_js

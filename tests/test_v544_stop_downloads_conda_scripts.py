from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.database import Database
from data_curation_tool.jobs import JobManager
from data_curation_tool.paths import AppPaths


def test_cancel_download_jobs_marks_queued_download_cancelled(tmp_path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    job_id = db.create_job("model_download", {"model_name": "gemma-4-e4b-it"})
    db.create_job("dataset_import", {})
    jobs = JobManager(db, max_workers=2)
    try:
        result = jobs.cancel_jobs(download_only=True, include_running=True)
        assert result["cancelled"] == [job_id]
        row = db.query_one("SELECT status, message FROM jobs WHERE id=?", (job_id,))
        assert row["status"] == "cancelled"
        assert "Cancelled" in row["message"]
    finally:
        jobs.shutdown(wait=False)


def test_cancel_jobs_api_and_frontend_buttons(tmp_path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    db = app.state.context.db
    job_id = db.create_job("model_download", {"model_name": "gemma-4-e4b-it"})
    with TestClient(app) as client:
        result = client.post("/api/jobs/cancel", json={"download_only": True, "include_running": True}).json()
        assert job_id in result["cancelled"]
        assert client.get(f"/api/jobs/{job_id}").json()["status"] == "cancelled"
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Stop Queued/Running Downloads" in app_js
    assert "/api/jobs/cancel" in app_js
    assert "Stop Checked Jobs" in app_js


def test_conda_helpers_and_entry_scripts_activate_application_env():
    for file_name in [
        "scripts/find_conda.bat",
        "scripts/activate_data_curation_env.bat",
        "scripts/activate_data_curation_env.sh",
        "run.bat",
        "install.bat",
        "update.bat",
        "run.sh",
        "install.sh",
        "update.sh",
    ]:
        assert Path(file_name).exists(), file_name
    run_bat = Path("run.bat").read_text(encoding="utf-8")
    install_bat = Path("install.bat").read_text(encoding="utf-8")
    find_bat = Path("scripts/find_conda.bat").read_text(encoding="utf-8")
    run_sh = Path("run.sh").read_text(encoding="utf-8")
    activate_sh = Path("scripts/activate_data_curation_env.sh").read_text(encoding="utf-8")
    assert "scripts\\activate_data_curation_env.bat" in run_bat
    assert "scripts\\find_conda.bat" in install_bat
    assert "%USERPROFILE%\\miniconda3\\condabin\\conda.bat" in find_bat
    assert "source scripts/activate_data_curation_env.sh" in run_sh
    assert "DCT_CONDA_BASE" in activate_sh

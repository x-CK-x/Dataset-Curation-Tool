from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService
from data_curation_tool.services.preset_service import PresetService


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_lifecycle_status_reconciles_completed_job_rows(tmp_path: Path):
    client = _client(tmp_path)
    ctx = client.app.state.context
    job_id = ctx.db.create_job("model_load", {"model_name": "dataset-assistant"})
    ctx.models.lifecycle.update("dataset-assistant", "load", state="queued", progress=0.0, message="Load queued", job_id=job_id)
    ctx.db.update_job(job_id, status="completed", progress=1.0, message="Completed after worker", result={"loaded": True}, finished=True)

    status = client.get("/api/models/status").json()["models"]["dataset-assistant"]["load"]
    assert status["state"] == "completed"
    assert status["percent"] == 100
    assert status["job_id"] == job_id


def test_gallery_score_requests_are_cached_and_render_is_scroll_safe():
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function tagScoreRequestSignature" in js
    assert "state.tagScoreRequestKeys[key] === signature" in js
    assert "scheduleRender()" in js
    assert "function snapshotScrollState" in js
    assert "function restoreScrollState" in js
    assert "requestAnimationFrame(apply)" in js


def test_download_defaults_are_slow_all_posts_defaults():
    settings = AppSettings()
    assert settings.downloader_download_all_posts_default is True
    assert settings.downloader_api_delay_seconds == 7.0
    assert settings.downloader_file_delay_seconds == 7.0
    assert settings.downloader_request_timeout_seconds == 60
    assert settings.downloader_max_retries == 3
    assert settings.downloader_retry_backoff_seconds == 2.0
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "downloader_download_all_posts_default !== false" in js
    assert "downloader_api_delay_seconds ?? 7" in js
    assert "downloader_file_delay_seconds ?? 7" in js


def test_parallel_category_dedupe_uses_post_identity_not_only_url(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    svc = DownloaderService(db, presets)
    presets.upsert(DownloadPreset(name="p1", source="e621", positive_tags=["alpha"]))
    presets.upsert(DownloadPreset(name="p2", source="e621", positive_tags=["beta"]))

    def fake_fetch(preset, cfg, api_url, limit, page, request=None):
        if page != 1:
            return []
        # Same source post id, different URL spelling. URL-only dedupe downloads two files.
        suffix = "a" if preset["name"] == "p1" else "b"
        return [{"id": 42, "file": {"url": f"https://cdn.example/{suffix}.jpg"}, "tags": {"general": [preset["name"]]}}]

    def fake_download(item, cfg, output_dir, preset):
        target = output_dir / Path(item["file"]["url"]).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"fake")
        return str(target)

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    monkeypatch.setattr(svc, "_download_item", fake_download)
    result = svc.run(
        DownloadRequest(
            preset_names=["p1", "p2"],
            confirmed_authorized=True,
            output_dir=str(tmp_path / "downloads"),
            max_items=2,
            parallel_workers=2,
            parallel_presets=True,
            dedupe_across_presets=True,
            store_membership_index=True,
        ),
        lambda pct, msg="": None,
    )
    assert result["downloaded"] == 1
    assert result["dedupe_keys"] >= 2


def test_model_dropdowns_keep_explicit_state_during_status_poll_renders():
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function rememberSelect" in js
    assert "select.dataset.noPersist = '1'" in js
    for key in [
        "modelRunSelection",
        "quickModelSelection",
        "curationModelSelection",
        "tagSelectionModelSelection",
        "predictionModelSelection",
        "assistantModelSelection",
        "orchestrationModelSelection",
    ]:
        assert key in js
    assert "await refreshAll();\n            toast(`Model job ${r.job_id} queued`)" in js
    assert "Model load queued as job ${r.job_id}. Status circles and Jobs are refreshed without reloading the page." in js

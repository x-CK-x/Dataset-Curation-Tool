from pathlib import Path

from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.services.downloader_service import BOORU_SOURCES, validate_source_configs
from data_curation_tool.services.browser_service import BrowserService
from data_curation_tool.paths import AppPaths


def test_redrocket_models_are_first_class_downloadable(tmp_path: Path):
    reg = ModelRegistry(tmp_path / "models")
    rows = {m["name"]: m for m in reg.list()}
    assert "redrocket-jtp-3" in rows
    assert rows["redrocket-jtp-3"]["repo_id"] == "RedRocket/JTP-3"
    assert rows["redrocket-jtp-3"]["download_supported"] is True
    assert "tag" in rows["redrocket-jtp-3"]["capabilities"]
    assert "redrocket-e6-visual-ratings" in rows
    assert rows["redrocket-e6-visual-ratings"]["repo_id"] == "RedRocket/e6-visual-ratings"
    assert rows["redrocket-e6-visual-ratings"]["download_supported"] is True
    assert "rating" in rows["redrocket-e6-visual-ratings"]["capabilities"]


def test_supported_booru_source_parsers_validate():
    payload = validate_source_configs()
    assert payload["ok"] is True
    by_source = {r["source"]: r for r in payload["sources"]}
    assert set(BOORU_SOURCES).issubset(by_source)
    bad = {k: v for k, v in by_source.items() if not v["ok"]}
    assert not bad
    assert by_source["danbooru"]["sample_tags"]
    assert by_source["gelbooru"]["page_param"] == "pid"
    assert by_source["e621"]["sample_url"].endswith("e621.png")


def test_browser_service_exposes_real_test_launch_path(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    svc = BrowserService(paths)
    status = svc.status()
    assert "geckodriver_path" in status
    assert status["private_mode_default"] is True
    assert hasattr(svc, "test_launch")


def test_model_run_request_accepts_rating_task():
    from data_curation_tool.schemas import ModelRunRequest
    req = ModelRunRequest(model_name="redrocket-e6-visual-ratings", task="rating", media_ids=[1])
    assert req.task == "rating"


def test_browser_router_has_visible_and_direct_endpoints(tmp_path: Path):
    from fastapi.testclient import TestClient
    from data_curation_tool.app import create_app
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    client = TestClient(create_app(paths))
    # Status should not need Firefox/geckodriver installed.
    assert client.get("/api/browser/status").status_code == 200
    # Ensure the schema endpoints are registered without actually launching.
    routes = {getattr(route, "path", "") for route in client.app.routes}
    assert "/api/browser/launch-direct" in routes
    assert "/api/browser/visible-self-test" in routes

from __future__ import annotations

from pathlib import Path

import pytest
import requests

from data_curation_tool.database import Database
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService, source_definitions
from data_curation_tool.services.preset_service import PresetService


def _service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    return DownloaderService(db, presets)


def test_danbooru_source_profile_uses_safe_api_page_size_and_no_redundant_newest_sort() -> None:
    by_key = {row["key"]: row for row in source_definitions()}
    assert by_key["danbooru"]["max_limit"] == 100


def test_danbooru_fetch_clamps_limit_and_omits_default_newest_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    svc = _service(tmp_path)
    captured: dict[str, object] = {}

    class FakeResponse:
        def json(self):
            return []

    def fake_request(method, url, *, timeout=60, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = dict(kwargs.get("params") or {})
        return FakeResponse()

    monkeypatch.setattr(svc, "_request_with_retries", fake_request)
    source, preset, cfg = svc._resolved_source_config(
        {"name": "direct-danbooru", "source": "danbooru", "positive_tags": ["human", "anthro"], "negative_tags": [], "options": {}},
        DownloadRequest(preset=DownloadPreset(name="direct-danbooru", source="danbooru"), confirmed_authorized=True, download_all_posts=True),
    )

    assert source == "danbooru"
    svc._fetch_page(preset, cfg, cfg["api_url"], 200, 1, request=DownloadRequest(preset=DownloadPreset(name="direct-danbooru", source="danbooru"), confirmed_authorized=True, download_all_posts=True))

    params = captured["params"]
    assert params["limit"] == 100
    assert params["page"] == 1
    assert params["tags"] == "human anthro"
    assert "order:id_desc" not in params["tags"]


def test_preflight_returns_source_error_row_instead_of_raising_on_source_http_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    svc = _service(tmp_path)

    def fake_fetch(*args, **kwargs):
        response = requests.Response()
        response.status_code = 422
        response._content = b'{"success":false,"message":"Search limited"}'
        raise requests.HTTPError("422 Client Error: Unprocessable Entity", response=response)

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    result = svc.preflight(
        DownloadRequest(
            preset=DownloadPreset(name="direct-danbooru", source="danbooru", positive_tags=["human", "anthro"]),
            confirmed_authorized=True,
            download_all_posts=True,
            max_pages=1,
        )
    )

    assert result["ok"] is False
    assert result["estimated_total"] == 0
    assert result["errors"]
    assert result["errors"][0]["source"] == "danbooru"
    assert "HTTP 422" in result["errors"][0]["error"]
    assert result["rows"][0]["source"] == "danbooru"

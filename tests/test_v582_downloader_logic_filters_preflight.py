from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService, source_definitions
from data_curation_tool.services.preset_service import PresetService

ROOT = Path(__file__).resolve().parents[1]


def _service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    return DownloaderService(db, presets)


def test_source_definitions_blacklists_disabled_and_preflight_advertised() -> None:
    rows = source_definitions()
    assert rows
    assert all(row["supports_preflight_count"] for row in rows)
    assert all(row["blacklists_applied_by_default"] is False for row in rows)
    assert any("animated" in row["content_filter_keys"] for row in rows)


def test_preflight_counts_unique_items_and_honors_media_rating_filters(tmp_path: Path, monkeypatch) -> None:
    svc = _service(tmp_path)

    def fake_fetch(preset, cfg, api_url, limit, page, request=None, progress=None):
        assert cfg.get("api_url")
        if page != 1:
            return []
        return [
            {"id": 1, "rating": "s", "file": {"url": "https://cdn.example/1.jpg", "ext": "jpg"}, "tags": {"general": ["solo"]}},
            {"id": 2, "rating": "e", "file": {"url": "https://cdn.example/2.webm", "ext": "webm"}, "tags": {"general": ["solo", "animated"]}},
            {"id": 3, "rating": "s", "file": {"url": "https://cdn.example/3.jpg", "ext": "jpg"}, "tags": {"general": ["solo", "blender"]}},
        ]

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    result = svc.preflight(
        DownloadRequest(
            preset=DownloadPreset(name="p", source="e621", positive_tags=["solo"]),
            confirmed_authorized=True,
            max_items=20,
            download_all_posts=True,
            max_pages=1,
            rating_filter=["s"],
            allow_video=False,
            allow_blender=False,
        )
    )
    assert result["estimated_total"] == 1
    assert result["rows"][0]["matching_items"] == 1
    assert result["blacklists_applied_by_default"] is False


def test_download_messages_include_estimated_total_and_eta(tmp_path: Path, monkeypatch) -> None:
    svc = _service(tmp_path)
    calls: list[str] = []

    def fake_fetch(preset, cfg, api_url, limit, page, request=None, progress=None):
        if page != 1:
            return []
        return [
            {"id": 10, "rating": "s", "file": {"url": "https://cdn.example/10.jpg", "ext": "jpg"}, "tags": {"general": ["solo"]}},
            {"id": 11, "rating": "s", "file": {"url": "https://cdn.example/11.jpg", "ext": "jpg"}, "tags": {"general": ["solo"]}},
        ]

    def fake_download(item, cfg, output_dir, preset, progress=None):
        target = output_dir / f"{item['id']}.jpg"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"x")
        return str(target)

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    monkeypatch.setattr(svc, "_download_item", fake_download)

    result = svc.run(
        DownloadRequest(
            preset=DownloadPreset(name="p", source="e621", positive_tags=["solo"]),
            output_dir=str(tmp_path / "downloads"),
            confirmed_authorized=True,
            download_all_posts=True,
            max_pages=1,
            estimate_total_before_download=True,
        ),
        lambda pct, msg: calls.append(msg),
    )
    assert result["downloaded"] == 2
    assert any("Preflight estimate: 2" in msg for msg in calls)
    assert any("downloaded 1/2" in msg and "ETA" in msg for msg in calls)


def test_frontend_exposes_logic_suggestions_filters_preflight_and_blacklist_policy() -> None:
    js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "tokenMode = 'tag'",
        "currentLogicToken",
        "Use either the logic expression OR the Positive/Negative fields",
        "allow animated",
        "allow video",
        "allow Blender",
        "safe",
        "questionable",
        "explicit",
        "apply source/account blacklists",
        "Preflight Count / Estimate Total",
        "/api/downloads/preflight",
    ):
        assert text in js

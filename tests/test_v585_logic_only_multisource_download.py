from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService, expand_booru_logic_query, source_definitions
from data_curation_tool.services.preset_service import PresetService
from data_curation_tool.utils import set_tag_text_mode

ROOT = Path(__file__).resolve().parents[1]


def _service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    return DownloaderService(db, presets)


def test_logic_query_accepts_lowercase_ops_and_preserves_space_tags(monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    clauses = expand_booru_logic_query("blue eyes and (red hair or black fur) and not low quality")
    assert clauses == [
        {"positive": ["blue eyes", "red hair"], "negative": ["low quality"]},
        {"positive": ["black fur", "blue eyes"], "negative": ["low quality"]},
    ]


def test_quoted_tags_can_contain_operator_words(monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    clauses = expand_booru_logic_query('"black and white" and solo')
    assert clauses == [{"positive": ["black and white", "solo"], "negative": []}]


def test_logic_query_overrides_positive_negative_boxes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    svc = _service(tmp_path)
    request = DownloadRequest(
        preset=DownloadPreset(name="direct-e621", source="e621", positive_tags=["stale positive"], negative_tags=["stale negative"]),
        confirmed_authorized=True,
        logic_query="blue eyes and not low quality",
    )
    prepared = svc._prepare_presets(request)
    assert len(prepared) == 1
    assert prepared[0]["positive_tags"] == ["blue eyes"]
    assert prepared[0]["negative_tags"] == ["low quality"]
    assert prepared[0]["options"]["_logic_overrode_manual_tags"] is True
    assert "stale positive" not in prepared[0]["positive_tags"]
    assert "stale negative" not in prepared[0]["negative_tags"]


def test_logic_only_preflight_counts_without_positive_negative_boxes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    svc = _service(tmp_path)
    seen_queries: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []

    def fake_fetch(preset, cfg, api_url, limit, page, request=None, progress=None):
        seen_queries.append((preset["source"], tuple(preset.get("positive_tags") or []), tuple(preset.get("negative_tags") or [])))
        if page != 1:
            return []
        if preset.get("positive_tags") == ["solo", "sonic"] and not preset.get("negative_tags"):
            return [{"id": 1, "rating": "s", "file": {"url": "https://cdn.example/1.jpg", "ext": "jpg"}, "tags": {"general": ["sonic", "solo"]}}]
        return []

    monkeypatch.setattr(svc, "_fetch_page", fake_fetch)
    result = svc.preflight(
        DownloadRequest(
            preset=DownloadPreset(name="direct-e621", source="e621"),
            confirmed_authorized=True,
            logic_query="sonic and solo",
            download_all_posts=True,
            max_pages=1,
        )
    )
    assert result["estimated_total"] == 1
    assert seen_queries == [("e621", ("solo", "sonic"), ())]


def test_direct_multi_source_presets_expand_for_one_job(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    svc = _service(tmp_path)
    request = DownloadRequest(
        presets=[
            DownloadPreset(name="direct-e621", source="e621"),
            DownloadPreset(name="direct-danbooru", source="danbooru"),
            DownloadPreset(name="direct-gelbooru", source="gelbooru"),
        ],
        confirmed_authorized=True,
        logic_query="sonic and solo",
        parallel_presets=True,
    )
    prepared = svc._prepare_presets(request)
    assert [p["source"] for p in prepared] == ["e621", "danbooru", "gelbooru"]
    assert all(p["positive_tags"] == ["solo", "sonic"] for p in prepared)
    assert all(p["options"].get("_logic_overrode_manual_tags") for p in prepared)


def test_frontend_exposes_logic_only_and_multi_source_direct_controls() -> None:
    js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "Optional additional sources for the same query",
        "One job: queue selected sources sequentially",
        "One job: run selected sources in parallel",
        "logic-only searches are valid",
        "positive_tags: logicText ? []",
        "body.presets = sourceKeys.map",
        "options.output_subdir = sourceKey",
    ):
        assert text in js
    assert "lower-case and/or/not" in source_definitions()[0]["logic_gate_syntax"]

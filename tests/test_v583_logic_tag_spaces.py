from __future__ import annotations

from pathlib import Path

from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService, expand_booru_logic_query, source_definitions
from data_curation_tool.utils import set_tag_text_mode

ROOT = Path(__file__).resolve().parents[1]


def test_logic_query_preserves_spaces_inside_tags(monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    clauses = expand_booru_logic_query("blue eyes AND (red hair OR black fur) AND NOT low quality")
    assert clauses == [
        {"positive": ["blue eyes", "red hair"], "negative": ["low quality"]},
        {"positive": ["black fur", "blue eyes"], "negative": ["low quality"]},
    ]
    flattened = {tag for clause in clauses for side in ("positive", "negative") for tag in clause[side]}
    assert "blue" not in flattened
    assert "eyes" not in flattened
    assert "red" not in flattened
    assert "hair" not in flattened


def test_logic_query_comma_and_symbol_ops_preserve_space_tags(monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    clauses = expand_booru_logic_query("blue eyes, red hair || black fur && !low quality")
    assert clauses == [
        {"positive": ["blue eyes", "red hair"], "negative": []},
        {"positive": ["black fur"], "negative": ["low quality"]},
    ]


def test_logic_spaces_convert_back_to_underscore_source_query(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DCT_TAG_TEXT_MODE_ACTIVE", "spaces")
    set_tag_text_mode("spaces")
    svc = DownloaderService.__new__(DownloaderService)
    captured = {}

    class FakeResponse:
        def json(self):
            return {"posts": []}

    def fake_request(method, api_url, params=None, **kwargs):
        captured["params"] = params or {}
        return FakeResponse()

    svc.user_agent = "test"
    svc._request_with_retries = fake_request  # type: ignore[method-assign]
    preset = {"name": "p", "source": "e621", "positive_tags": ["blue eyes"], "negative_tags": ["low quality"], "options": {}}
    cfg = {"api_url": "https://example.invalid/posts.json", "tags_param": "tags", "limit_param": "limit", "page_param": "page", "timeout_seconds": 1}
    svc._fetch_page(preset, cfg, cfg["api_url"], 25, 1, DownloadRequest(preset=DownloadPreset(name="p", source="e621"), confirmed_authorized=True))
    assert captured["params"]["tags"] == "blue_eyes -low_quality"


def test_frontend_and_source_docs_warn_whitespace_is_not_separator() -> None:
    js = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    assert "Spaces inside tag names are preserved" in js
    assert "Whitespace inside tag names is preserved" in source_definitions()[0]["logic_gate_syntax"]

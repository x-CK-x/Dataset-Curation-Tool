from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_release_version_is_5825():
    assert __version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_legacy_eva_attention_pool_and_head_defaults_are_present():
    src = read("data_curation_tool/models/adapters.py")
    assert '"attn_pool": None' in src
    assert '"head_drop": "__identity__"' in src
    assert '"pos_drop": "__identity__"' in src
    assert 'attempts <= 32' in src
    assert 'if attr in {"attn_pool"}' in src
    assert 'elif attr in {"head_drop", "pos_drop"' in src


def test_force_render_bypasses_scroll_defer_for_explicit_refreshes():
    js = read("data_curation_tool/static/app.js")
    assert 'function renderNowPreservingState()' in js
    assert 'if (!force && shouldSnapshot && recentUserScroll(1600)' in js
    assert 'async function refreshModelsPanel({ force = false, renderAfter = false, immediate = false } = {})' in js
    assert 'renderNowPreservingState();' in js
    assert 'Refresh This Log' in js and 'renderNowPreservingState()' in js

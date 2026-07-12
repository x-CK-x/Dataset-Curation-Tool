from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_eva_attn_pool_and_more_head_defaults_present():
    src = read("data_curation_tool/models/adapters.py")
    assert '"attn_pool": None' in src
    assert '"head_drop": "__identity__"' in src
    assert '"pos_drop": "__identity__"' in src
    assert 'attempts <= 32' in src


def test_ui_refresh_no_longer_blocks_tab_updates_after_plain_clicks():
    js = read("data_curation_tool/static/app.js")
    assert "normal button clicks are allowed" in js
    assert "recentUserScroll(900)" in js
    assert "passiveSensitiveTabs" not in js
    assert "renderAfter = false, immediate = false" in js
    assert "render(true, true)" in js
    assert "cache: 'no-store'" in js

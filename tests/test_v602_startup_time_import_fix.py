from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__


def test_release_version_is_5_8_11() -> None:
    assert __version__ == "5.8.48"


def test_app_imports_time_for_deferred_startup_progress() -> None:
    text = Path("data_curation_tool/app.py").read_text(encoding="utf-8")
    assert "import time" in text
    assert "time.monotonic()" in text


def test_startup_tag_sync_user_agent_uses_current_version_constant() -> None:
    text = Path("data_curation_tool/app.py").read_text(encoding="utf-8")
    assert "DataCurationTool/5.8.8" not in text
    assert "DataCurationTool/{__version__}" in text

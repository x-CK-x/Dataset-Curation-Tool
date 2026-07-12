from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_environment_uses_conda_soundfile_package_name() -> None:
    text = (ROOT / "environment.yml").read_text(encoding="utf-8")
    assert "  - soundfile\n" not in text
    assert "pysoundfile>=0.12" in text
    assert "libsndfile" in text
    assert "cffi" in text


def test_windows_installers_create_or_update_missing_env() -> None:
    for name in ("install.bat", "update.bat"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "env create -f" in text
        assert "env update -n" in text
        assert "pysoundfile" in text
        assert "call :ensure_conda_env" in text


def test_linux_installers_create_or_update_missing_env() -> None:
    for name in ("install.sh", "update.sh"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "conda env create -f" in text
        assert "conda env update -n" in text
        assert "pysoundfile" in text
        assert "ensure_conda_env" in text

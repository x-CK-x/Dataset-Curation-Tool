from __future__ import annotations

from pathlib import Path

import yaml

from data_curation_tool import __version__
from data_curation_tool.models import adapters


def test_release_version_is_5_8_5() -> None:
    assert __version__ == "5.8.48"


def test_hydra_environment_includes_binary_fallback_and_cffi_floor() -> None:
    env = yaml.safe_load(Path("environment.yml").read_text(encoding="utf-8"))
    deps = env["dependencies"]
    assert "libvips" in deps
    assert "pyvips" in deps
    assert "cffi>=1.17.1" in deps
    pip_deps = next(item["pip"] for item in deps if isinstance(item, dict) and "pip" in item)
    assert "pyvips[binary]>=3.0.0" in pip_deps
    req_models = Path("requirements-models.txt").read_text(encoding="utf-8")
    assert "pyvips[binary]>=3.0.0" in req_models


def test_hydra_installer_scripts_install_binary_fallback() -> None:
    for fname in ["install.bat", "update.bat", "install_hydra_runtime_deps.bat"]:
        text = Path(fname).read_text(encoding="utf-8")
        assert "pyvips[binary]>=3.0.0" in text
        assert "cffi>=1.17.1" in text or fname in {"install.bat", "update.bat"}
    for fname in ["install.sh", "update.sh", "install_hydra_runtime_deps.sh"]:
        text = Path(fname).read_text(encoding="utf-8")
        assert "pyvips[binary]>=3.0.0" in text


def test_hydra_dll_directory_handles_are_kept_alive_in_source() -> None:
    text = Path("data_curation_tool/models/adapters.py").read_text(encoding="utf-8")
    assert "handle = add_dll_dir(str(candidate))" in text
    assert "_HYDRA_DLL_DIRECTORY_HANDLES.append(handle)" in text
    assert "_HYDRA_DLL_DIRECTORY_PATHS.add(key)" in text


def test_hydra_missing_pyvips_message_mentions_binary_fallback(tmp_path: Path, monkeypatch) -> None:
    fake_bin = tmp_path / "Library" / "bin"
    fake_bin.mkdir(parents=True)
    monkeypatch.setenv("CONDA_PREFIX", str(tmp_path))
    msg = adapters._hydra_pyvips_probe_error(RuntimeError("cannot load library 'libvips-42.dll'"), adapters._hydra_libvips_candidate_dirs())
    assert "pyvips-binary" in msg
    assert "libvips" in msg


def test_hydra_load_attempts_auto_repair_when_pyvips_missing(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "Hydra"
    (repo / "models").mkdir(parents=True)
    (repo / "data").mkdir()
    (repo / "inference.py").write_text("# fake", encoding="utf-8")
    (repo / "models" / "hydra-3.5.safetensors").write_bytes(b"fake")
    calls = {"checks": 0, "repairs": 0}

    def fake_check(include_core: bool = True):  # type: ignore[no-untyped-def]
        calls["checks"] += 1
        if calls["checks"] == 1:
            return ["pyvips + libvips (cannot load library 'libvips-42.dll')"], ["first check"]
        return [], ["second check OK"]

    def fake_repair():  # type: ignore[no-untyped-def]
        calls["repairs"] += 1
        return ["pip pyvips-binary repair ran"]

    monkeypatch.setattr(adapters, "_hydra_check_runtime_dependencies", fake_check)
    monkeypatch.setattr(adapters, "_hydra_auto_repair_runtime_dependencies", fake_repair)
    adapter = adapters.RedRocketHydra35Adapter()
    adapter.load(device="cpu", model_id=str(repo))
    assert adapter.repo_path == repo
    assert calls["repairs"] == 1
    assert calls["checks"] >= 2


def test_hydra_repair_script_exists_and_mentions_pip_binary() -> None:
    text = Path("scripts/repair_hydra_runtime_dependencies.py").read_text(encoding="utf-8")
    assert "pyvips[binary]>=3.0.0" in text
    assert "pyvips-binary>=8.16.0" in text
    assert "--check-only" in text

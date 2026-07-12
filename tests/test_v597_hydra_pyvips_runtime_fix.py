from __future__ import annotations

import builtins
from pathlib import Path

import yaml

from data_curation_tool import __version__
from data_curation_tool.models.adapters import RedRocketHydra35Adapter
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths


def _make_hydra_repo(root: Path) -> Path:
    repo = root / "Hydra"
    (repo / "models").mkdir(parents=True)
    (repo / "data").mkdir()
    (repo / "inference.py").write_text("# fake inference", encoding="utf-8")
    (repo / "models" / "hydra-3.5.safetensors").write_bytes(b"fake")
    return repo


def test_release_version_is_5_8_5() -> None:
    assert __version__ == "5.8.48"


def test_hydra_environment_includes_pyvips_and_libvips() -> None:
    env = yaml.safe_load(Path("environment.yml").read_text(encoding="utf-8"))
    deps = env["dependencies"]
    assert "pyvips" in deps
    assert "libvips" in deps
    assert Path("install_hydra_runtime_deps.bat").exists()
    assert Path("install_hydra_runtime_deps.sh").exists()
    assert Path("scripts/check_hydra_runtime_dependencies.py").exists()


def test_hydra_catalog_advertises_pyvips_runtime_requirement(tmp_path: Path) -> None:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    registry = ModelRegistry(paths.models)
    hydra = {row["name"]: row for row in registry.list()}["redrocket-hydra-3-5"]
    assert "pyvips" in hydra["requirements"]
    assert "libvips" in hydra["requirements"]


def test_hydra_load_preflight_reports_missing_pyvips_before_subprocess(tmp_path: Path, monkeypatch) -> None:
    repo = _make_hydra_repo(tmp_path)
    adapter = RedRocketHydra35Adapter()
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "pyvips":
            raise ModuleNotFoundError("No module named 'pyvips'")
        if name in {"torch", "torchvision", "timm", "einops", "safetensors", "PIL", "numpy"}:
            return object()
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        adapter.load(device="cpu", model_id=str(repo), hydra_auto_repair_runtime=False)
    except RuntimeError as exc:
        msg = str(exc)
        assert "Hydra 3.5 runtime dependencies are missing" in msg
        assert "pyvips + libvips" in msg
        assert "pyvips[binary]" in msg
        assert "install_hydra_runtime_deps" in msg
    else:  # pragma: no cover - defensive
        raise AssertionError("Hydra load unexpectedly succeeded without pyvips")


def test_hydra_subprocess_uses_repaired_runtime_env() -> None:
    text = Path("data_curation_tool/models/adapters.py").read_text(encoding="utf-8")
    assert "env=_hydra_subprocess_env()" in text
    assert "CONDA_PREFIX" in text
    assert "Library" in text and "bin" in text

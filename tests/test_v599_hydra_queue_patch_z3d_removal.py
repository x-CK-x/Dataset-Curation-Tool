from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.models import adapters
from data_curation_tool.models.legacy_tagger_configs import LEGACY_TAGGER_CONFIGS
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths


def test_release_version_is_5_8_6() -> None:
    assert __version__ == "5.8.48"


def test_unavailable_z3d_legacy_tagger_is_removed(tmp_path: Path) -> None:
    assert "z3d-e621-convnext" not in LEGACY_TAGGER_CONFIGS
    registry = ModelRegistry(AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs").models)
    names = {row["name"] for row in registry.list()}
    assert "legacy-z3d-e621-convnext" not in names
    assert "legacy-eva02-clip-vit-large-7704" in names
    assert "legacy-eva02-vit-large-448-8046" in names
    assert "legacy-efficientnetv2-m-8035" in names


def test_hydra_queue_annotation_source_patch(tmp_path: Path) -> None:
    repo = tmp_path / "Hydra"
    loader = repo / "utils" / "loader.py"
    loader.parent.mkdir(parents=True)
    loader.write_text(
        "from multiprocessing import Queue as MpQueue\n"
        "import multiprocessing as mp\n"
        "def run(submission_queue: MpQueue[str], status_queue: Queue[int], other: mp.Queue[str]):\n"
        "    return submission_queue, status_queue, other\n",
        encoding="utf-8",
    )

    notes = adapters._hydra_patch_repo_source_compat(repo)
    patched = loader.read_text(encoding="utf-8")

    assert "MpQueue[str]" not in patched
    assert "Queue[int]" not in patched
    assert "mp.Queue[str]" not in patched
    assert "submission_queue: MpQueue" in patched
    assert "status_queue: Queue" in patched
    assert "other: mp.Queue" in patched
    assert (loader.with_suffix(".py.dctbak")).exists()
    assert (repo / ".dct_hydra_py311_queue_patch.json").exists()
    assert notes and "utils/loader.py" in notes[0]


def test_hydra_adapter_load_runs_queue_patch_before_marking_loaded(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "Hydra"
    (repo / "models").mkdir(parents=True)
    (repo / "data").mkdir()
    (repo / "utils").mkdir()
    (repo / "inference.py").write_text("# fake", encoding="utf-8")
    (repo / "models" / "hydra-3.5.safetensors").write_bytes(b"fake")
    (repo / "utils" / "loader.py").write_text("from multiprocessing import Queue as MpQueue\nx: MpQueue[str]\n", encoding="utf-8")

    monkeypatch.setattr(adapters, "_hydra_check_runtime_dependencies", lambda include_core=True: ([], []))
    adapter = adapters.RedRocketHydra35Adapter()
    adapter.load(device="cpu", model_id=str(repo))

    assert adapter.repo_path == repo
    assert "MpQueue[str]" not in (repo / "utils" / "loader.py").read_text(encoding="utf-8")

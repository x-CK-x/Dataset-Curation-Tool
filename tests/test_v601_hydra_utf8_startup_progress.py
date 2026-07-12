from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.models import adapters
from data_curation_tool.services.startup_progress_service import StartupProgressService


def test_release_version_is_5_8_11() -> None:
    assert __version__ == "5.8.48"


def test_hydra_subprocess_env_forces_utf8_stdout_encoding() -> None:
    env = adapters._hydra_subprocess_env()
    assert env["PYTHONIOENCODING"].lower() == "utf-8"
    assert env["PYTHONUTF8"] == "1"


def test_hydra_patch_injects_utf8_stdio_reconfigure(tmp_path: Path) -> None:
    repo = tmp_path / "Hydra"
    repo.mkdir(parents=True)
    (repo / "inference.py").write_text("import sys\nprint('ready')\n", encoding="utf-8")
    loader = repo / "utils" / "loader.py"
    loader.parent.mkdir(parents=True)
    loader.write_text(
        "class Loader:\n"
        "    @staticmethod\n"
        "    def heuristic_workers(workers, count, batch_size):\n"
        "        return 0\n"
        "\n"
        "def _worker_fn():\n"
        "    pass\n",
        encoding="utf-8",
    )

    notes = adapters._hydra_patch_repo_source_compat(repo)
    patched = (repo / "inference.py").read_text(encoding="utf-8")

    assert notes
    assert "DCT_HYDRA_UTF8_STDIO_PATCH" in patched
    assert "reconfigure(encoding='utf-8'" in patched
    assert (repo / ".dct_hydra_compat_patch_v3.json").exists()


def test_hydra_adapter_reads_subprocess_output_as_utf8() -> None:
    text = Path("data_curation_tool/models/adapters.py").read_text(encoding="utf-8")
    assert 'encoding="utf-8"' in text
    assert 'errors="replace"' in text
    assert 'PYTHONIOENCODING' in text


def test_hydra_adapter_uses_utf8_temp_csv_instead_of_stdout(tmp_path: Path, monkeypatch) -> None:
    import subprocess

    repo = tmp_path / "Hydra"
    repo.mkdir(parents=True)
    (repo / "inference.py").write_text("print('stub')\n", encoding="utf-8")
    (repo / "models").mkdir()
    (repo / "models" / "hydra-3.5.safetensors").write_text("stub", encoding="utf-8")
    (repo / "data").mkdir()
    image = tmp_path / "image.png"
    image.write_bytes(b"stub")

    adapter = adapters.RedRocketHydra35Adapter()
    adapter.repo_path = repo

    def fake_run(cmd, **kwargs):
        assert "-o" in cmd
        output_path = Path(cmd[cmd.index("-o") + 1])
        assert str(output_path) != "-"
        output_path.write_text("filename,tag_a,tag_♀\nimage.png,0.1000,0.9000\n", encoding="utf-8")
        assert kwargs.get("encoding") == "utf-8"
        assert kwargs.get("errors") == "replace"
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="ok")

    monkeypatch.setattr(adapters.subprocess, "run", fake_run)
    pred = adapter.predict(image, threshold=0.2, max_tags=10, hydra_model_path=repo / "models" / "hydra-3.5.safetensors", hydra_metadata_path=repo / "data")

    assert ("tag_♀", 0.9) in pred.tags
    assert pred.raw["output_mode"] == "utf8_csv_file"


def test_startup_progress_service_reports_elapsed_eta_and_steps() -> None:
    service = StartupProgressService()
    service.start("started")
    service.update(0.5, "halfway", phase="reconcile")
    snapshot = service.snapshot()
    assert snapshot["status"] == "running"
    assert snapshot["phase"] == "reconcile"
    assert snapshot["percent"] == 50.0
    assert snapshot["elapsed_seconds"] >= 0
    assert snapshot["eta_seconds"] is not None
    assert snapshot["steps"]
    service.complete("done")
    assert service.snapshot()["status"] == "completed"


def test_frontend_dashboard_polls_startup_status_and_renders_white_circle() -> None:
    js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "/api/system/startup-status" in js
    assert "startupProgressCard" in js
    assert "Startup Maintenance Progress" in js
    assert "startup-progress-circle" in css
    assert "#ffffff" in css or "#fff" in css

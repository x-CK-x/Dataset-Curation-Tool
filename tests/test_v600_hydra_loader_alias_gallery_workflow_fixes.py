from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.models import adapters
from data_curation_tool.services.workflow_automation_service import WORKFLOW_TEMPLATES


def test_release_version_is_5_8_7() -> None:
    assert __version__ == "5.8.48"


def test_hydra_loader_source_patch_adds_heuristic_max_workers_and_max_workers_kwarg(tmp_path: Path) -> None:
    repo = tmp_path / "Hydra"
    loader = repo / "utils" / "loader.py"
    loader.parent.mkdir(parents=True)
    loader.write_text(
        "from multiprocessing.queues import Queue as MpQueue\n"
        "class Loader:\n"
        "    def __init__(\n"
        "        self,\n"
        "        queue_depth: int,\n"
        "        config,\n"
        "        n_workers: int,\n"
        "        *,\n"
        "        share_memory: bool = True,\n"
        "    ) -> None:\n"
        "        self._config = config\n"
        "        self.n_workers_seen = n_workers\n"
        "    @staticmethod\n"
        "    def heuristic_workers(workers: int, count: int, batch_size: int) -> int:\n"
        "        if workers < 0:\n"
        "            workers = 1\n"
        "        return min(workers, count)\n"
        "\n"
        "def _worker_fn(submission_queue: MpQueue[str]):\n"
        "    return submission_queue\n",
        encoding="utf-8",
    )

    notes = adapters._hydra_patch_repo_source_compat(repo)
    patched = loader.read_text(encoding="utf-8")

    assert notes
    assert "MpQueue[str]" not in patched
    assert "max_workers" in patched
    assert "heuristic_max_workers" in patched
    assert (repo / ".dct_hydra_compat_patch_v2.json").exists()


def test_workflow_templates_cover_style_character_style_and_concept() -> None:
    labels = {t["key"] for t in WORKFLOW_TEMPLATES}
    assert "character_lora_auto_prep" in labels
    assert "style_lora_auto_prep" in labels
    assert "concept_lora_auto_prep" in labels
    assert "character_style_lora_auto_prep" in labels


def test_frontend_has_gallery_paging_clamp_and_non_deferred_force_render() -> None:
    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "async function goToGalleryPage(page)" in text
    assert "Math.max(1, Math.min(Number(page || 1)" in text
    assert "forceRenderPreservingScroll" in text
    assert "render(false, true)" in text
    assert "workflowDatasetGoalRows" in text
    assert "Character + Style / OC + style" in text

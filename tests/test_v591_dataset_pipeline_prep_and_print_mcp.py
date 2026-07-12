from __future__ import annotations

from pathlib import Path

from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.global_dataset_service import GlobalDatasetService
from data_curation_tool.services.mcp_tools_service import MCPToolsService
from data_curation_tool.services.pipeline_prep_service import PipelinePrepService
from data_curation_tool.services.three_d_service import ThreeDService


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_pipeline_prep_evaluates_prompts_and_applies_branch_sidecars_without_mutating_originals(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    db = Database(paths.database)
    settings = AppSettings(global_dataset_root=str(tmp_path / "global_dataset"))
    global_ds = GlobalDatasetService(db, paths, settings)

    src = tmp_path / "source.png"
    src.write_bytes(b"not-a-real-image-but-still-a-file")
    asset = global_ds.register_file(
        src,
        source="unit-test",
        source_site="danbooru",
        source_post_id="123",
        tags=["test_character", "blue eyes", "solo", "watermark"],
        caption="",
    )
    branch = global_ds.ensure_branch("character-style-branch", purpose="training prep")
    linked = global_ds.link_assets(branch_id=branch["id"], asset_ids=[asset["id"]], copy_sidecars=True)
    branch_tag_path = Path(linked["items"][0]["tag_path"])
    original_detail_before = global_ds.asset_detail(asset["id"])

    svc = PipelinePrepService(db, paths, settings, global_ds)
    payload = {"branch_name": "character-style-branch", "target_model": "illustrious", "adapter_family": "lora", "dataset_goal": "character_style"}
    metrics = svc.evaluate(payload)
    assert metrics["item_count"] == 1
    assert metrics["tag_coverage"] == 1
    assert metrics["rule_preset"]["rules"]["caption_rule"]

    prompt = svc.build_prompt({**payload, "max_items": 5})
    assert "Dataset branch metrics" in prompt["prompt"]
    assert "do not alter global originals" in prompt["prompt"].lower()

    dry_run = svc.apply_rules({**payload, "dry_run": True})
    assert dry_run["dry_run"] is True
    assert dry_run["edited_count"] == 1
    assert "watermark" in dry_run["edits"][0]["removed"]
    assert "watermark" in branch_tag_path.read_text(encoding="utf-8")

    applied = svc.apply_rules({**payload, "dry_run": False})
    assert applied["dry_run"] is False
    assert "watermark" not in branch_tag_path.read_text(encoding="utf-8")

    original_detail_after = global_ds.asset_detail(asset["id"])
    assert original_detail_before["tags"] == original_detail_after["tags"]


def test_mcp_catalog_contains_training_and_3d_print_handoff_tools(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    settings = AppSettings()
    status = MCPToolsService(paths, settings).status()
    keys = {row["key"] for row in status["tools"]}
    for key in ["prusaslicer", "orcaslicer", "bambu_studio", "curaengine", "slic3r", "kohya_ss", "onetrainer", "diffusers_trainer", "ltx_trainer", "external_webscraper"]:
        assert key in keys

    print_keys = {row["key"] for row in ThreeDService.print_providers()}
    for key in ["prusaslicer", "orcaslicer", "bambu_studio", "curaengine", "slic3r"]:
        assert key in print_keys


def test_registry_exposes_dataset_pipeline_training_and_slicer_rows(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    registry = ModelRegistry(paths.models)
    rows = {row["name"]: row for row in registry.list()}
    for name in ["diffusion-target-sdxl", "diffusion-target-wan22", "diffusion-target-ltx23", "mcp-prusaslicer-control", "mcp-curaengine-control"]:
        assert name in rows
    assert any(row["kind"] == "training_tool_interface" for row in rows.values())

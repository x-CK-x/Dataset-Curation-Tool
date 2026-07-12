from __future__ import annotations

from pathlib import Path

from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.dataset_pipeline_service import DatasetPipelineService
from data_curation_tool.services.global_dataset_service import GlobalDatasetService
from data_curation_tool.services.mcp_tools_service import MCPToolsService


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_dataset_pipeline_rules_evaluate_export_and_print_package(tmp_path):
    paths = make_paths(tmp_path)
    db = Database(paths.database)
    settings = AppSettings(global_dataset_root=str(tmp_path / "global_dataset"))
    settings.save(paths.settings)
    global_dataset = GlobalDatasetService(db, paths, settings)
    pipeline = DatasetPipelineService(paths, global_dataset)

    src = tmp_path / "source.png"
    src.write_bytes(b"fake image data for pipeline")
    asset = global_dataset.register_file(src, source="manual", source_site="e621", source_post_id="123", tags=["solo", "blue eyes"], caption="")
    branch = global_dataset.ensure_branch("character-lora-v1", purpose="test character branch")
    linked = global_dataset.link_assets(branch_id=branch["id"], asset_ids=[asset["id"]], copy_sidecars=True)
    tag_path = Path(linked["items"][0]["tag_path"])
    tag_path.write_text("ckchar, solo, blue eyes, hair, outfit", encoding="utf-8")

    rules = pipeline.build_rules({"target_model": "illustrious", "adapter_type": "lora", "dataset_goal": "character", "trigger_token": "ckchar"})
    assert rules["target_model"]["key"] == "illustrious"
    assert any(r["id"] == "identity-critical-tags" for r in rules["rules"])
    assert Path(rules["rules_path"]).exists()

    plan = pipeline.plan_pipeline({"branch_name": "character-lora-v1", "target_model": "illustrious", "adapter_type": "lora", "dataset_goal": "character", "trigger_token": "ckchar"})
    assert len(plan["stages"]) >= 6
    assert Path(plan["plan_path"]).exists()

    report = pipeline.evaluate_branch({"branch_name": "character-lora-v1", "target_model": "illustrious", "adapter_type": "lora", "dataset_goal": "character", "trigger_token": "ckchar"})
    assert report["ok"] is True
    assert report["metrics"]["item_count"] == 1
    assert report["metrics"]["trigger_coverage"] == 1.0

    export = pipeline.export_branch({"branch_name": "character-lora-v1", "target_model": "illustrious", "adapter_type": "lora", "dataset_goal": "character", "trigger_token": "ckchar", "training_tool": "kohya_ss", "include_media": False})
    assert export["ok"] is True
    assert Path(export["manifest_path"]).exists()
    assert Path(export["export_dir"]).joinpath("configs", "kohya_dataset_config.toml").exists()

    mesh = tmp_path / "asset.glb"
    mesh.write_bytes(b"glb payload")
    package = pipeline.create_3d_print_package({"asset_path": str(mesh), "package_name": "printer-test", "target_formats": ["stl", "3mf"], "slicer": "prusaslicer"})
    assert Path(package["manifest_path"]).exists()
    assert package["mcp_handoff"]["slicer"] == "prusaslicer"
    assert {x["format"] for x in package["output_targets"]} == {"stl", "3mf"}


def test_pipeline_model_catalog_and_mcp_tool_interfaces(tmp_path):
    paths = make_paths(tmp_path)
    registry = ModelRegistry(paths.models)
    names = {row["name"] for row in registry.list()}
    for name in [
        "target-sdxl-lora-prep",
        "target-krea2-style-prep",
        "target-ideogram4-structured-caption-prep",
        "target-wan22-video-lora-prep",
        "target-ltx23-lora-iclora-prep",
        "trainer-handoff-kohya-ss",
        "trainer-handoff-ltx",
        "slicer-handoff-prusaslicer",
    ]:
        assert name in names

    mcp = MCPToolsService(paths, AppSettings())
    tool_keys = {row["key"] for row in mcp.status()["tools"]}
    for key in ["prusaslicer", "orcaslicer", "cura", "bambu_studio", "meshlab", "kohya_ss", "onetrainer", "ltx_trainer"]:
        assert key in tool_keys

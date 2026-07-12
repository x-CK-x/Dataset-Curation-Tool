from __future__ import annotations

from pathlib import Path

from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.global_dataset_service import GlobalDatasetService
from data_curation_tool.services.mcp_tools_service import MCPToolsService
from data_curation_tool.services.three_d_service import ThreeDService


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_global_dataset_dedup_branch_sidecars_and_variants(tmp_path):
    paths = make_paths(tmp_path)
    db = Database(paths.database)
    settings = AppSettings(global_dataset_root=str(tmp_path / "global_dataset"))
    settings.save(paths.settings)
    svc = GlobalDatasetService(db, paths, settings)

    src_a = tmp_path / "source_a.png"
    src_b = tmp_path / "source_b.png"
    src_a.write_bytes(b"same-original-bytes")
    src_b.write_bytes(b"same-original-bytes")

    first = svc.register_file(src_a, source="manual", source_site="e621", source_post_id="100", tags=["blue_eyes", "solo"], caption="original caption")
    second = svc.register_file(src_b, source="manual", source_site="danbooru", source_post_id="200", tags=["blue_eyes"], caption="other caption")

    assert first["id"] == second["id"]
    assert first["created"] is True
    assert second["duplicate_avoided"] is True
    status = svc.status()
    assert status["asset_count"] == 1
    assert status["source_mapping_count"] == 2

    branch = svc.ensure_branch("character-lora-v1", purpose="editable branch")
    linked = svc.link_assets(branch_id=branch["id"], asset_ids=[first["id"]], copy_sidecars=True)
    assert linked["linked_count"] == 1
    tag_path = Path(linked["items"][0]["tag_path"])
    assert tag_path.exists()
    tag_path.write_text("branch only tag edit", encoding="utf-8")

    detail = svc.asset_detail(first["id"])
    assert "blue_eyes" in detail["tags"] or "blue eyes" in detail["tags"]
    assert "branch only tag edit" not in detail["tags"]

    variant = tmp_path / "variant.png"
    variant.write_bytes(b"augmented-variant-bytes")
    registered_variant = svc.register_variant(
        global_asset_id=first["id"],
        branch_id=branch["id"],
        variant_path=variant,
        variant_kind="augmentation",
        transform={"flip": True},
        tags=["augmented"],
        caption="variant caption",
    )
    assert Path(registered_variant["variant_path"]).exists()
    detail_after = svc.asset_detail(first["id"])
    assert len(detail_after["variants"]) == 1
    branch_items = svc.branch_items(branch["id"])
    assert len(branch_items["items"]) >= 2
    refs = svc.branch_references(asset_id=first["id"])
    assert refs["count"] >= 2
    assert any("branch only tag edit" in str(r.get("tag_text") or "") for r in refs["items"])


def test_new_3d_providers_and_zbrush_mcp_catalog(tmp_path):
    providers = {row["key"]: row for row in ThreeDService.generation_providers()}
    for key in ["dream_textures_blender_bridge", "quickmaker_blender_bridge", "blender_mcp_addon", "zbrush_mcp_bridge", "meshy_text_api", "meshy_image_api"]:
        assert key in providers

    paths = make_paths(tmp_path)
    settings = AppSettings()
    mcp = MCPToolsService(paths, settings)
    status = mcp.status()
    tool_keys = {row["key"] for row in status["tools"]}
    assert "zbrush" in tool_keys
    assert any(row["mcp_name"] == "dct-zbrush" for row in status["tools"])

    registry = ModelRegistry(paths.models)
    names = {row["name"] for row in registry.list()}
    for name in [
        "dream-textures-blender-addon",
        "quickmaker-blender-ai-suite",
        "meshy-v2-official-api",
        "blender-official-mcp-addon",
        "zbrush-python-mcp-refinement",
        "mcp-zbrush-control",
    ]:
        assert name in names

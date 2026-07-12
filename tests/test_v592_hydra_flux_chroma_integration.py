from __future__ import annotations

from pathlib import Path

from data_curation_tool.models.adapters import RedRocketHydra35Adapter
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DistributedNode
from data_curation_tool.services.distributed_service import DistributedService
from data_curation_tool.services.mcp_tools_service import MCPToolsService
from data_curation_tool.config import AppSettings
from data_curation_tool.services.dataset_pipeline_service import DIFFUSION_TARGETS
from data_curation_tool.services.pipeline_prep_service import PipelinePrepService, TRAINING_TARGETS


def _paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_registry_exposes_redrocket_hydra_35_as_preferred_tagger(tmp_path: Path) -> None:
    registry = ModelRegistry(_paths(tmp_path).models)
    rows = {row["name"]: row for row in registry.list()}
    hydra = rows["redrocket-hydra-3-5"]
    assert hydra["repo_id"] == "RedRocket/Hydra"
    assert hydra["kind"] == "tagger"
    for cap in ["tag", "rating", "hydra", "cam_attention", "cam_pca", "local_inference", "compare", "tag_editor"]:
        assert cap in hydra["capabilities"]
    assert hydra["download_supported"] is True
    assert "diffusion-target-flux1-dev" in rows
    assert "diffusion-target-chroma-flux" in rows


def test_hydra_adapter_builds_native_command_and_parses_service_outputs(tmp_path: Path) -> None:
    repo = tmp_path / "Hydra"
    (repo / "models").mkdir(parents=True)
    (repo / "data").mkdir()
    (repo / "inference.py").write_text("# fake", encoding="utf-8")
    adapter = RedRocketHydra35Adapter()
    adapter.repo_path = repo
    cmd = adapter._command(
        tmp_path / "image.png",
        device="cpu",
        hydra_metric="f0.5@0.2",
        hydra_implications="enforce-inherit",
        hydra_varlen=True,
        hydra_seqlen=512,
        hydra_underscores=True,
        hydra_exclude_tags=["bad_tag"],
        hydra_exclude_categories=["meta"],
    )
    joined = " ".join(str(x) for x in cmd)
    assert "inference.py" in joined
    assert "-o -" in joined
    assert "hydra-3.5.safetensors" in joined
    assert "f0.5@0.2" in joined
    assert "enforce-inherit" in joined
    assert "-V" in cmd
    assert "-S" in cmd and "512" in cmd
    assert "-x" in cmd and "bad_tag" in cmd
    assert "-C" in cmd and "meta" in cmd

    parsed = adapter._parse_service_response({"tags": [{"tag": "blue eyes", "score": 0.91}], "explicit": 0.2})
    assert ("blue_eyes", 0.91) in parsed
    pred = adapter._prediction_from_scores(parsed + [("safe", 0.77)], threshold=0.5, max_tags=10)
    assert ("blue_eyes", 0.91) in pred.tags
    assert ("safe", 0.77) in pred.classes


def test_flux_and_chroma_targets_are_available_in_pipeline_catalogs(tmp_path: Path) -> None:
    prep_keys = {row["key"] for row in TRAINING_TARGETS}
    for key in ["flux1-dev", "flux1-schnell", "flux1-kontext-dev", "flux1-fill-dev", "flux1-depth-dev", "flux1-canny-dev", "flux1-redux-dev", "chroma-flux"]:
        assert key in prep_keys
    pipeline_keys = {row["key"] for row in DIFFUSION_TARGETS}
    for key in ["flux1_dev", "flux1_schnell", "flux1_kontext_dev", "flux1_fill_dev", "flux1_depth_dev", "flux1_canny_dev", "flux1_redux_dev", "chroma_flux"]:
        assert key in pipeline_keys

    # _normalize_target should accept user-facing aliases.
    dummy = object.__new__(PipelinePrepService)
    assert PipelinePrepService._normalize_target(dummy, "flux") == "flux1-dev"
    assert PipelinePrepService._normalize_target(dummy, "chroma") == "chroma-flux"


def test_remote_model_dispatch_and_hydra_mcp_contract(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    svc = DistributedService(paths)
    svc.upsert_node(DistributedNode(name="gpu-a", host="a.local", base_url="http://a:7865", capabilities=["model", "hydra"], worker_mode="hydra-tagger"))
    svc.upsert_node(DistributedNode(name="download-only", host="b.local", base_url="http://b:7865", capabilities=["downloader"], worker_mode="downloader-only"))
    plan = svc.plan_model_run_shards({"model_name": "redrocket-hydra-3-5", "media_ids": [1, 2, 3], "task": "tag"}, include_local=True)
    assert plan["worker_count"] == 2
    assert {s["node"] for s in plan["shards"]} == {"local", "gpu-a"}
    assert sum(len(s["payload"]["media_ids"]) for s in plan["shards"]) == 3

    node = svc.get_node("gpu-a")
    cmd = svc.start_hydra_service_command(node, hydra_repo_path="/opt/Hydra", port=8081, device="cuda:0", seqlen=1024)
    assert "service.py" in cmd
    assert "8081" in cmd
    assert "/opt/Hydra" in cmd

    status = MCPToolsService(paths, AppSettings()).status()
    keys = {row["key"] for row in status["tools"]}
    assert "hydra_tagger" in keys

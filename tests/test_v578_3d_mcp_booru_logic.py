from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DownloadPreset, DownloadRequest
from data_curation_tool.services.downloader_service import DownloaderService, booru_logic_summary, expand_booru_logic_query, source_definitions
from data_curation_tool.services.preset_service import PresetService
from data_curation_tool.services.three_d_service import ThreeDService


def _client(tmp_path: Path) -> tuple[TestClient, AppPaths]:
    paths = AppPaths.create(
        runtime=tmp_path / "runtime",
        models=tmp_path / "models",
        outputs=tmp_path / "outputs",
    )
    return TestClient(create_app(paths)), paths


def _download_service(tmp_path: Path) -> DownloaderService:
    db = Database(tmp_path / "runtime" / "app.db")
    presets = PresetService(db, tmp_path / "runtime" / "presets")
    return DownloaderService(db, presets)


def test_booru_logic_expands_or_not_and_parentheses():
    clauses = expand_booru_logic_query("wolf AND (solo OR duo) AND NOT sketch", max_clauses=8)
    assert clauses == [
        {"positive": ["solo", "wolf"], "negative": ["sketch"]},
        {"positive": ["duo", "wolf"], "negative": ["sketch"]},
    ]

    compact = expand_booru_logic_query("cat && (rating:s || rating:q) && -animated", max_clauses=8)
    assert compact == [
        {"positive": ["cat", "rating:s"], "negative": ["animated"]},
        {"positive": ["cat", "rating:q"], "negative": ["animated"]},
    ]

    summary = booru_logic_summary("fox OR wolf", max_clauses=8)
    assert summary["count"] == 2
    assert summary["clauses"][0]["positive"] == ["fox"]


def test_logic_presets_expand_into_deduped_source_queries(tmp_path: Path):
    svc = _download_service(tmp_path)
    base = DownloadPreset(name="seed", source="e621", positive_tags=["female"], negative_tags=["comic"]).model_dump()
    request = DownloadRequest(
        preset_names=["seed"],
        confirmed_authorized=True,
        logic_query="(wolf OR fox) AND NOT sketch",
        logic_mode="boolean_expand",
        logic_max_clauses=8,
    )
    expanded = svc._expand_presets_for_logic([base], request)
    assert len(expanded) == 2
    # Current downloader behavior: a filled logic expression is the query source
    # for the run/preset and intentionally overrides stale positive/negative
    # boxes rather than merging with them.
    assert {tuple(row["positive_tags"]) for row in expanded} == {("fox",), ("wolf",)}
    assert all(row["negative_tags"] == ["sketch"] for row in expanded)
    assert all((row.get("options") or {}).get("_logic_overrode_manual_tags") for row in expanded)
    assert all((row.get("options") or {}).get("_logic_clause", {}).get("count") == 2 for row in expanded)


def test_download_source_definitions_advertise_logic_gate_support():
    rows = source_definitions()
    assert rows
    assert all(row["supports_logic_gates"] for row in rows)
    assert all("boolean_expand" in row["logic_gate_modes"] for row in rows)
    assert any(row["key"] == "e621" and "OR expands" in row["logic_gate_syntax"] for row in rows)


def test_3d_provider_catalog_covers_text_image_multi_image_and_video():
    providers = {row["key"]: row for row in ThreeDService.generation_providers()}
    expected = {
        "trellis2_image_local",
        "hunyuan3d_21_local_api",
        "hunyuan3d_text_local_api",
        "meshy_text_api",
        "meshy_multi_image_api",
        "tripo_text_api",
        "tripo_multi_image_api",
        "rodin_text_api",
        "rodin_multi_image_api",
        "comfyui_3d_workflow_api",
        "nerfstudio_video_to_3d_local",
        "generic_multi_image_to_3d_api",
        "generic_video_to_3d_api",
    }
    assert expected <= set(providers)
    assert any("text" in row.get("inputs", []) for row in providers.values())
    assert any("multi_image" in row.get("inputs", []) for row in providers.values())
    assert any("video" in row.get("inputs", []) for row in providers.values())
    assert "multi_image" in providers["meshy_multi_image_api"]["inputs"]
    assert "video" in providers["generic_video_to_3d_api"]["inputs"]


def test_mcp_tool_status_and_client_config_endpoint(tmp_path: Path):
    client, paths = _client(tmp_path)
    status = client.get("/api/mcp-tools/status")
    assert status.status_code == 200, status.text
    body = status.json()
    tools = {row["key"]: row for row in body["tools"]}
    assert {"blender", "krita", "audacity", "obs", "comfyui"} <= set(tools)
    assert all("manual_steps" in row and isinstance(row["manual_steps"], list) for row in tools.values())
    assert all("enabled" in row and "installed" in row for row in tools.values())

    config = client.get("/api/mcp-tools/client-config")
    assert config.status_code == 200, config.text
    cfg = config.json()
    assert "mcpServers" in cfg
    write = client.post("/api/mcp-tools/write-client-config")
    assert write.status_code == 200, write.text
    written_path = Path(write.json()["config_path"])
    assert written_path.exists()
    assert written_path.is_relative_to(paths.runtime / "mcp_servers")
    client.close()


def test_model_catalog_exposes_3d_generation_cloud_and_mcp_rows(tmp_path: Path):
    client, _ = _client(tmp_path)
    rows = {row["name"]: row for row in client.get("/api/models").json()}
    expected = {
        "trellis2-4b-pbr-image-to-3d",
        "hunyuan3d-21-pbr",
        "meshy-cloud-text-image-multiview",
        "tripo-cloud-text-image-multiview",
        "rodin-hyper3d-cloud-text-image-multiview",
        "mcp-blender-control",
        "mcp-krita-control",
        "mcp-audacity-control",
        "mcp-obs-control",
        "mcp-comfyui-control",
        "openrouter-deepseek-v4-pro",
    }
    assert expected <= set(rows)
    assert "multi_image_to_3d" in rows["meshy-cloud-text-image-multiview"]["capabilities"]
    assert "mcp" in rows["mcp-blender-control"]["capabilities"]
    assert rows["openrouter-deepseek-v4-pro"].get("cloud") is True
    client.close()


def test_frontend_includes_logic_gates_cloud_runtime_and_mcp_tools():
    root = Path(__file__).resolve().parents[1]
    source = (root / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "MCP Tools",
        "Logic gates",
        "Preview logic expansion",
        "Cloud model runtime defaults",
        "deepseek/deepseek-v4-pro",
        "threeDMultiImagePaths",
        "threeDVideoPath",
        "/api/mcp-tools/status",
        "/api/downloads/logic/preview",
    ):
        assert text in source

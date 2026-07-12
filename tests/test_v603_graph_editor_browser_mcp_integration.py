from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.graph_editor_service import GraphEditorService
from data_curation_tool.services.mcp_tools_service import MCPToolsService, _tool_defaults


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def test_release_version_is_5_8_11() -> None:
    assert __version__ == "5.8.48"


def test_graph_editor_catalog_ports_standalone_node_features(tmp_path: Path) -> None:
    svc = GraphEditorService(make_paths(tmp_path))
    catalog = svc.catalog()
    kinds = {row["kind"] for row in catalog["node_palette"]}
    for kind in {"text_input", "image_input", "audio_input", "video_input", "bundle_context", "model_call", "supervisor_controller", "external_tool_call", "output_artifact", "browser_search", "browser_open"}:
        assert kind in kinds
    features = catalog["graph_feature_contract"]["ported_features"]
    assert "pan_and_zoom_canvas" in features
    assert "port_based_node_connections" in features
    assert "browser_mcp_nodes" in features


def test_graph_editor_enriched_nodes_normalize_and_compile(tmp_path: Path) -> None:
    svc = GraphEditorService(make_paths(tmp_path))
    graph = svc.save_graph({
        "name": "Standalone-compatible graph",
        "nodes": [
            {"id": "text", "kind": "text_input", "label": "Prompt", "x": 10, "y": 20, "config": {"text": "curate dataset"}},
            {"id": "bundle", "kind": "bundle_context", "label": "Context bundle", "x": 280, "y": 20, "config": {"max_items": 4}},
            {"id": "model", "kind": "model_call", "label": "Assistant model", "x": 540, "y": 20, "config": {"model_ref_id": "dataset-assistant"}},
            {"id": "browser", "kind": "browser_search", "label": "Research", "x": 800, "y": 20, "config": {"query": "tagging best practices"}},
            {"id": "out", "kind": "output_artifact", "label": "Output", "x": 1060, "y": 20},
        ],
        "edges": [
            {"id": "e1", "from": "text", "to": "bundle"},
            {"id": "e2", "from": "bundle", "to": "model"},
            {"id": "e3", "from": "model", "to": "browser"},
            {"id": "e4", "from": "browser", "to": "out"},
        ],
    })
    by_id = {n["id"]: n for n in graph["nodes"]}
    assert by_id["bundle"]["config"]["policy"] == "drop_largest"
    assert by_id["model"]["config"]["input_modalities"] == ["text", "json"]
    workflow = svc.to_workflow(graph)
    step_types = [step["type"] for step in workflow["steps"]]
    assert "assistant_refine_labels" in step_types
    assert "manual_review_gate" in step_types
    assert all(step["id"] != "out" for step in workflow["steps"])


def test_browser_mcp_tools_are_configured_and_client_configured(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    settings = AppSettings()
    svc = MCPToolsService(paths, settings)
    defaults = _tool_defaults()
    for key in ["browser_default", "browser_edge", "browser_chrome", "browser_firefox", "browser_chromium", "browser_tor"]:
        assert key in defaults
        assert key in settings.external_mcp_tools
        assert "open_url" in defaults[key]["supports"]
    status = svc.status()
    status_keys = {row["key"] for row in status["tools"]}
    assert "browser_default" in status_keys
    assert "browser_firefox" in status_keys
    cfg = svc.client_config()
    assert "mcpServers" in cfg


def test_frontend_has_enhanced_graph_and_browser_mcp_strings() -> None:
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    bridge = Path("integrations/mcp_servers/dct_mcp_tool_bridge.py").read_text(encoding="utf-8")
    assert "graphEditorNodeAdvancedInspector" in app_js
    assert "Graph Event Console" in app_js
    assert "Right-click canvas" in app_js
    assert "browser_search" in app_js
    assert "agent-graph-canvas.flow-on" in css
    assert "search_web" in bridge
    assert "browser_firefox" in bridge



def test_scroll_and_startup_migration_regressions_are_wired() -> None:
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    migration_router = Path("data_curation_tool/routers/migration.py").read_text(encoding="utf-8")
    app_py = Path("data_curation_tool/app.py").read_text(encoding="utf-8")
    config_py = Path("data_curation_tool/config.py").read_text(encoding="utf-8")
    assert "dctShellScrollMemory" in app_js
    assert "lastCrossTabScrollSnapshot" in app_js
    assert "height: 100vh" in css
    assert "Migration-triggered maintenance started" in migration_router
    assert "tag_db_sync_if_empty_only: bool = False" in config_py
    assert 'empty_only=bool(getattr(c.settings, "tag_db_sync_if_empty_only", True))' in app_py

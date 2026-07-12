from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_JS = (ROOT / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
MIGRATION = (ROOT / "data_curation_tool" / "routers" / "migration.py").read_text(encoding="utf-8")


def test_graph_canvas_has_standalone_interaction_parity_hooks() -> None:
    assert "graphEditorCanvasPaletteGroups" in APP_JS
    assert "agent-graph-context-menu" in APP_JS
    assert "graphEditorScreenToWorld" in APP_JS
    assert "canvas.addEventListener('wheel'" in APP_JS
    assert "canvas.addEventListener('pointerdown'" in APP_JS
    assert "startConnection" in APP_JS
    assert "graphEditorAddEdgeByIds" in APP_JS
    assert "document.elementFromPoint" in APP_JS
    assert "graph-port.in[data-node-id]" in APP_JS


def test_right_click_does_not_create_vanilla_node_immediately() -> None:
    # The contextmenu handler should open a categorized palette and wait for the
    # user's node-type choice instead of immediately adding the currently
    # selected/default node kind.
    base = APP_JS.index("function graphEditorCanvas(graph)")
    cstart = APP_JS.index("const openCanvasMenu", base)
    contextmenu_slice = APP_JS[cstart:APP_JS.index("const zoomCanvas", cstart)]
    assert "state.graphEditorContextMenu" in contextmenu_slice
    assert "graphEditorAddNode(kind)" not in contextmenu_slice
    assert "graphEditorAddNode(row.kind" in APP_JS


def test_migration_progress_reserves_finalization_range() -> None:
    assert "0.02 + 0.88 * local" in MIGRATION
    assert "Reloading migrated custom model catalog" in MIGRATION
    assert "Reconciling migrated model assets" in MIGRATION
    assert "Checking {profile_key} tag dictionary status" in MIGRATION
    assert "progress(1.0, \"Migration-triggered maintenance complete\")" in MIGRATION


def test_post_migration_reconcile_is_active_profile_only() -> None:
    assert "c.tags.reconcile_export_cache(profile_key)" in MIGRATION
    assert "c.tags.reconcile_export_cache()" not in MIGRATION



def test_frontend_hydration_splits_boot_and_surfaces_progress() -> None:
    assert "frontendHydration" in APP_JS
    assert "async function refreshEssentialState" in APP_JS
    assert "async function refreshOptionalStateBackground" in APP_JS
    assert "visibleStartupStatus" in APP_JS
    assert "frontend_hydration" in APP_JS
    boot_slice = APP_JS[APP_JS.index("async function boot") : APP_JS.index("setInterval(async ()", APP_JS.index("async function boot"))]
    assert "await refreshEssentialState();" in boot_slice
    assert boot_slice.index("await refreshEssentialState();") < boot_slice.index("refreshOptionalStateBackground({ renderAfter: true })")
    assert "refreshOptionalStateBackground({ renderAfter: true })" in APP_JS

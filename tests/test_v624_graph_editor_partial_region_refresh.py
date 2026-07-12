from __future__ import annotations

from pathlib import Path

APP_JS = Path("data_curation_tool/static/app.js")


def test_graph_editor_uses_partial_canvas_and_inspector_refresh_for_interactions() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function graphEditorRefreshInteractiveRegions" in text
    assert "dct-graph-canvas-region" in text
    assert "dct-graph-inspector-region" in text
    assert "canvasRegion.replaceChildren(graphEditorCanvas(graph))" in text
    assert "inspectorRegion.replaceChildren(graphEditorNodeInspectorPanel(selectedNode))" in text
    assert "if (graphEditorRefreshInteractiveRegions()) return true;" in text
    assert "full app-shell render/defer queue" in text


def test_graph_polling_is_suppressed_during_active_canvas_interaction_without_deferring_clicks() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function graphEditorMarkCanvasInteraction" in text
    assert "function graphEditorHasActiveCanvasInteraction" in text
    assert "state.graphEditorDraggingNode = true" in text
    assert "state.graphEditorPanningCanvas = true" in text
    assert "state.graphEditorConnectingActive = true" in text
    assert "if (shouldSnapshot && !hardForce && typeof graphEditorHasActiveCanvasInteraction" in text
    assert "const bypassDeferral = Boolean(forceNow);" in text
    assert "const hardForce = forceNow === true || forceNow === 'hard';" in text
    assert "return render(true, hardForce ? 'hard' : true);" in text


def test_graph_chat_runtime_controls_have_safe_fallback_without_capsinput() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    fn_start = text.index("function inlineSelectedModelRuntimeControls")
    fn_end = text.index("function agentToolModelOptions", fn_start)
    fn = text[fn_start:fn_end]
    assert "capsInput" not in fn
    assert "const fallbackName = selectedName ||" in fn
    assert "rt = rt || modelRuntimeControls();" in fn
    assert "provider: 'local/configured'" in fn
    assert "Agentic Graph Chat" in text

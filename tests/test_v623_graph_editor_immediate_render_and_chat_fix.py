from __future__ import annotations

from pathlib import Path

APP_JS = Path("data_curation_tool/static/app.js")


def test_graph_editor_canvas_mutations_render_immediately_without_scroll_deferral() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function graphEditorRenderCanvasNow" in text
    assert "Graph canvas interactions must be immediate" in text
    assert "graphEditorActiveInteractionUntil: 0" in text
    assert "graphEditorMarkCanvasInteraction(1200)" in text
    assert "if (graphEditorRefreshInteractiveRegions()) return true" in text
    assert "render(true, 'hard')" in text
    assert "if (hardForce || tabSwitchRestore || !recentUserScroll(900))" in text
    assert "restoreScrollState(tab, { aggressive: hardForce || tabSwitchRestore })" in text
    assert "graphEditorHasActiveCanvasInteraction()" in text


def test_graph_editor_controls_use_immediate_canvas_render_for_actions() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "state.graphEditorAnimateFlow=!state.graphEditorAnimateFlow;graphEditorRenderCanvasNow();" in text
    assert "state.graphEditorViewport={x:0,y:0,scale:1};graphEditorRenderCanvasNow();" in text
    assert "state.graphEditorSelectedId=e.target.value" in text and "graphEditorRenderCanvasNow(); } }, graphEditorSelectOptions())" in text
    assert "toast('Graph saved'); graphEditorRenderCanvasNow();" in text
    assert "toast('Graph plan generated'); graphEditorRenderCanvasNow();" in text
    assert "id:'dct-graph-canvas-region'" in text
    assert "id:'dct-graph-inspector-region'" in text


def test_agentic_graph_chat_inline_runtime_controls_do_not_reference_capsinput() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    fn_start = text.index("function inlineSelectedModelRuntimeControls")
    fn_end = text.index("function agentToolModelOptions", fn_start)
    fn = text[fn_start:fn_end]
    assert "capsInput" not in fn
    assert "const selectedName = (typeof modelSelect === 'string' ? modelSelect : String(modelSelect?.value || '')).trim();" in fn
    assert "fallbackName" in fn
    assert "capabilities: []" in fn
    assert "rt = rt || modelRuntimeControls();" in fn
    assert "if (!m?.name || !rt) return null;" in fn
    assert "function agenticGraphChatView" in text
    assert "inlineSelectedModelRuntimeControls(model, rt, 'graph-chat')" in text


def test_pointer_clicks_cancel_restore_without_opening_scroll_deferral_window() -> None:
    text = APP_JS.read_text(encoding="utf-8")
    assert "function cancelPendingScrollRestoreOnly" in text
    assert "function markActiveUserScrollWindow" in text
    assert "Pointer and mouse clicks should cancel stale delayed scroll restores" in text
    assert "window.addEventListener('pointerdown', event => cancelScrollRestoreFromUserInput(event, { markScroll: false })" in text
    assert "window.addEventListener('mousedown', event => cancelScrollRestoreFromUserInput(event, { markScroll: false })" in text
    assert "cancelScrollRestoreFromUserInput(event, { markScroll: false })" in text
    assert "['wheel','touchmove'].forEach" in text
    assert "if (isGraphCanvasEventTarget(event?.target))" in text
    assert "cancelScrollRestoreFromUserInput(event, { markScroll: true, durationMs: 900 })" in text
    assert "actual scroll events, and scroll keys now open the active-scroll deferral window" in text

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_version_bumped_to_5848():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')
    assert 'v5.8.48 Update' in read('README.md')


def test_global_assistant_overlays_are_active_only_and_app_wide():
    js = read('data_curation_tool/static/app.js')
    css = read('data_curation_tool/static/styles.css')
    assert 'function globalAssistantOverlays' in js
    assert 'function patchGlobalAssistantOverlays' in js
    assert "id: 'global-assistant-overlays'" in js
    assert 'assistantQueueScopeEntries' in js
    assert "['assistant', 'tagSelection', 'graph', 'code']" in js
    assert 'globalAssistantOverlays()' in js
    assert 'setInterval(() => { try { patchGlobalAssistantOverlays(); patchContextBudgetPanels(); } catch (_) {} }, 850)' in js
    assert '.global-assistant-overlays' in css
    assert '.global-assistant-overlays:not(.active)' in css


def test_live_action_and_reasoning_trace_defaults_are_on():
    cfg = read('data_curation_tool/config.py')
    js = read('data_curation_tool/static/app.js')
    svc = read('data_curation_tool/services/model_service.py')
    for marker in [
        'assistant_show_live_action_notes: bool = True',
        'assistant_show_live_chain_of_thought: bool = True',
        'assistant_show_live_reasoning_trace: bool = True',
        'cleaned.setdefault("assistant_show_live_chain_of_thought", True)',
        'cleaned.setdefault("assistant_show_live_reasoning_trace", True)',
    ]:
        assert marker in cfg
    for marker in [
        'assistantShowLiveChainOfThought: true',
        'codeShowLiveChainOfThought: true',
        'liveReasoningTraceEnabled',
        'show_live_chain_of_thought',
        'show_live_reasoning_trace',
        'live chain-of-thought overlay',
    ]:
        assert marker in js
    assert 'options.setdefault("show_live_chain_of_thought", True)' in svc
    assert 'options.setdefault("show_live_reasoning_trace", True)' in svc


def test_completed_assistant_responses_preserve_visible_reasoning_trace():
    svc = read('data_curation_tool/services/model_service.py')
    js = read('data_curation_tool/static/app.js')
    assert 'VISIBLE_CHAIN_OF_THOUGHT' in svc
    assert 'def _clean_visible_reasoning_trace' in svc
    assert 'visible_reasoning_trace' in svc
    assert 'visible_chain_of_thought' in svc
    assert 'visible_reasoning_trace' in js
    assert 'Visible chain-of-thought / reasoning trace' in js


def test_settings_controls_persist_the_reasoning_overlay_default():
    js = read('data_curation_tool/static/app.js')
    assert 'const showLiveChain = el' in js
    assert 'assistant_show_live_chain_of_thought: showLiveChain.checked' in js
    assert 'assistant_show_live_reasoning_trace: showLiveChain.checked' in js
    assert 'show live chain-of-thought overlay' in js

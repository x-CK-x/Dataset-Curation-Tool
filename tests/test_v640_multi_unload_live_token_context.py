from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_v5846_version_and_docs():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')
    assert 'v5.8.48 Update' in read('README.md')
    assert 'V5_8_46_MULTI_UNLOAD_LIVE_TOKEN_CONTEXT.md' in read('README.md')
    assert '76-Multi-Unload-Live-Token-Context.md' in read('docs/wiki/_Sidebar.md')


def test_quick_tag_batch_unload_endpoint_and_frontend_batch_queue():
    router = read('data_curation_tool/routers/models.py')
    assert '@router.post("/unload-many")' in router
    assert 'model_names' in router
    assert 'batch_unload' in router
    app = read('data_curation_tool/static/app.js')
    assert 'async function queueModelUnloadMany' in app
    assert "'/api/models/unload-many'" in app
    assert "Queue Unload Selected" in app
    assert "Queued ${r.count" in app
    assert 'quickModelQueueDomSelectedValues' in app
    assert "o.dataset.queueSelected === '1'" in app


def test_live_token_context_budget_and_visible_trace_defaults():
    app = read('data_curation_tool/static/app.js')
    assert 'liveChatContextBudgets' in app
    assert 'startLiveContextBudgetTicker' in app
    assert "startLiveContextBudgetTicker('tagSelection'" in app
    assert 'patchContextBudgetPanels' in app
    assert 'data-context-budget-scope' in app
    assert 'Visible planning/action notes are enabled by default' in app
    assert "auto_condense_context: true" in app
    assert "auto_condense_context_threshold: 0.72" in app
    service = read('data_curation_tool/services/model_service.py')
    assert 'options.setdefault("auto_condense_context", True)' in service
    assert 'options.setdefault("auto_condense_context_threshold", 0.72)' in service
    assert 'auto_condense_context_enabled' in service
    assert 'precondensed_context' in service
    assert 'precondense_reason' in service


def test_hidden_cot_not_exposed_but_visible_plan_is_default():
    app = read('data_curation_tool/static/app.js')
    assert 'provider/private hidden chain-of-thought' in app
    assert 'not provider/private hidden chain-of-thought' in app
    service = read('data_curation_tool/services/model_service.py')
    assert 'hidden_chain_of_thought_exposed": False' in service
    assert 'Visible plan/action-notes' in service

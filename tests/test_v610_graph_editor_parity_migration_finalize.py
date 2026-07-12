from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_graph_editor_canvas_has_standalone_interactions_and_palette_fallback():
    js = read('data_curation_tool/static/app.js')
    assert 'Open Node Palette' in js
    assert 'graphEditorContextMenu' in js
    assert "addEventListener('contextmenu'" in js
    assert "addEventListener('wheel'" in js
    assert 'graphEditorScreenToWorld' in js
    assert 'graphEditorViewport' in js
    assert 'graphEditorIsControlTarget' in js
    assert 'setPointerCapture' in js
    assert 'graphEditorAddEdgeByIds' in js
    assert 'state.graphEditorConnectingFrom' in js
    assert 'graphEditorSuppressOutputClickUntil' in js
    assert 'click or drag an output port, then click any input port to finish' in js
    assert 'supervisor_controller' in js
    assert 'browser_search' in js and 'browser_open' in js
    assert 'graphEditorCanvasPaletteRows()' in js
    assert 'palette_category || t.category' in js


def test_migration_result_is_bounded_and_list_jobs_is_lightweight():
    migration_service = read('data_curation_tool/services/install_migration_service.py')
    jobs = read('data_curation_tool/jobs.py')
    router = read('data_curation_tool/routers/migration.py')
    assert 'files_omitted' in migration_service
    assert 'files_truncated' in migration_service
    assert 'files_result_limit' in migration_service
    assert 'Large migration result was summarized' in migration_service
    assert 'decode_result=False' in jobs
    assert 'result_available' in jobs
    assert 'tag_export_reconciliation' in router
    assert 'Finalizing compact migration result and releasing UI refresh' in router


def test_release_version_is_5817():
    init_py = read('data_curation_tool/__init__.py')
    pyproject = read('pyproject.toml')
    assert '__version__ = "5.8.48"' in init_py
    assert 'version = "5.8.48"' in pyproject

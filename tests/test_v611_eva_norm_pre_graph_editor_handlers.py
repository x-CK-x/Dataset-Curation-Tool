from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_release_version_is_5818():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')


def test_eva_legacy_tagger_patches_norm_pre_with_identity():
    src = read('data_curation_tool/models/adapters.py')
    assert 'norm_pre' in src
    assert '_eva_identity_module' in src
    assert 'torch.nn.Identity()' in src
    assert 'if value == "__identity__"' in src
    assert 'attempts <= 32' in src


def test_graph_editor_defines_missing_update_handlers_and_capture_canvas_events():
    js = read('data_curation_tool/static/app.js')
    assert 'function graphEditorUpdateNode(nodeId' in js
    assert 'function graphEditorUpdateNodeConfig(nodeId' in js
    assert 'function graphEditorChangeNodeKind(nodeId' in js
    assert 'function graphEditorRenderCanvasNow()' in js
    assert "canvas.oncontextmenu = openCanvasMenu" in js
    assert "canvas.onwheel = zoomCanvas" in js
    assert "canvas.onpointerdown = startPan" in js
    assert "addEventListener('contextmenu', openCanvasMenu, { capture:true })" in js
    assert "addEventListener('wheel', zoomCanvas, { passive:false, capture:true })" in js
    assert 'Open Node Palette' in js
    assert 'graphEditorAddNode(row.kind' in js

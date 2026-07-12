from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5841():
    assert '__version__ = "5.8.48"' in read("data_curation_tool/__init__.py")
    assert 'version = "5.8.48"' in read("pyproject.toml")
    assert "v5.8.48 Update" in read("README.md")


def test_quick_tag_multiselect_supports_shift_ctrl_and_preserves_selection():
    js = read("data_curation_tool/static/app.js")
    assert "function enableRangeMultiSelect" in js
    assert "ev.shiftKey" in js
    assert "ev.ctrlKey || ev.metaKey" in js
    assert "Ctrl/Cmd-click toggles models" in js
    assert "Shift-click selects" in js
    assert "Ctrl/Cmd+A selects all" in js
    assert "state.quickModelQueueSelection = restored" in js
    assert "option.selected = priorValues.has" in js
    assert "enableRangeMultiSelect(queueSelect, 'quickModelQueueSelection')" in js


def test_quick_tag_live_queue_includes_download_load_unload_and_inference():
    js = read("data_curation_tool/static/app.js")
    assert "function jobModelName" in js
    assert "function modelJobActionKind" in js
    assert "return 'download'" in js
    assert "return 'unload'" in js
    assert "return 'load'" in js
    assert "return 'inference'" in js
    assert "Quick Tag Model Queue" in js
    assert "data-model-names" in js
    assert "modelNames = [...new Set([state.quickModelSelection" in js
    assert "Download, load, unload, and inference statuses patch live per model" in js


def test_inference_watcher_patches_per_model_status_live():
    js = read("data_curation_tool/static/app.js")
    assert "const inferredModelName = jobModelName(job)" in js
    assert "setOptimisticModelStage(inferredModelName, 'inference'" in js
    assert "row.job_id = id" in js
    assert "updateLiveStatusDom();" in js


def test_graph_nodes_support_shift_and_ctrl_multiselect():
    js = read("data_curation_tool/static/app.js")
    assert "function graphEditorSelectNodeWithModifiers" in js
    assert "state.graphEditorLastSelectedNodeId" in js
    assert "if (range && state.graphEditorLastSelectedNodeId)" in js
    assert "if (ev.ctrlKey || ev.metaKey || ev.shiftKey)" in js
    assert "graphEditorSelectNodeWithModifiers(node.id, ev, nodes)" in js


def test_documentation_added():
    assert (ROOT / "docs" / "V5_8_41_QUICK_TAG_MULTISELECT_LIVE_QUEUE_GRAPH_SELECTION.md").exists()
    assert (ROOT / "docs" / "wiki" / "71-Quick-Tag-Multiselect-Live-Queue-Graph-Selection.md").exists()

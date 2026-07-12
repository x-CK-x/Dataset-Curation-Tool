from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5831():
    import data_curation_tool

    assert data_curation_tool.__version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_wd_pixai_rows_use_isolated_onnx_adapter_only_for_failed_rows():
    adapters = read("data_curation_tool/models/adapters.py")
    registry = read("data_curation_tool/models/registry.py")

    assert "class WDOnnxTaggerAdapter" in adapters
    assert "RGB -> BGR" in adapters
    assert "selected_tags.csv" in adapters
    assert "CUDAExecutionProvider" in adapters

    for model_id in [
        "wd-vit-tagger",
        "wd-swinv2-tagger",
        "wd-convnext-tagger-v3",
        "wd-eva02-large-tagger-v3",
        "pixai-tagger-v09",
    ]:
        idx = registry.index(f'ModelRecord("{model_id}"')
        row = registry[idx: registry.find('))', idx) + 2]
        assert "WDOnnxTaggerAdapter" in row
        assert "OptionalAdapterPlaceholder" not in row

    assert "deepghs/pixai-tagger-v0.9-onnx" in registry
    assert "pixai-labs/pixai-tagger-v0.9" in registry
    assert "wd_onnx_allow" in registry
    assert "*.onnx" in registry
    assert "*.csv" in registry


def test_graph_editor_selection_menu_shortcuts_and_ports():
    app = read("data_curation_tool/static/app.js")
    css = read("data_curation_tool/static/styles.css")

    assert "graphEditorSelectedNodeIds" in app
    assert "graphEditorSelectionBox" in app
    assert "graphEditorCopySelection" in app
    assert "graphEditorPasteClipboard" in app
    assert "graphEditorPortDescriptors" in app
    assert "source_port" in app and "target_port" in app
    assert "context-node-search" in app
    assert "context-filter-chip" in app
    assert "graphEditorPaletteRecentKinds" in app
    assert "Ctrl+drag" in app or "Ctrl+drag" in css
    assert "viewBox', '-5000 -5000 10000 10000'" in app
    assert "agent-graph-selection-box" in css
    assert "context-palette-tools" in css


def test_attention_visualizer_tag_autocomplete_and_augment_export_card():
    app = read("data_curation_tool/static/app.js")
    assert "function attentionVisualizerView" in app
    assert "tagAutocompleteControl" in app[app.index("function attentionVisualizerView"):app.index("function migrationSourcePathsFromText")]
    assert "function exportCard()" in app
    assert "Dataset export / handoff shortcuts" in app


def test_closed_loop_graph_template_and_sample_are_bundled():
    service = read("data_curation_tool/services/graph_editor_service.py")
    assert "closed_loop_model_training_improvement_graph" in service
    assert "Closed-loop model training improvement graph" in service
    assert "generation_eval" in service
    assert "improvement_plan" in service
    assert "context_supervisor" in service
    sample = ROOT / "docs/examples/agentic_closed_loop_training_curation_graph_sample.json"
    assert sample.exists()
    assert "Agentic curation graph" in sample.read_text(encoding="utf-8")

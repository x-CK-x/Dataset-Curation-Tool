from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from data_curation_tool import __version__
from data_curation_tool.models.adapters import WDOnnxTaggerAdapter
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.services.graph_editor_service import GraphEditorService


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5834() -> None:
    assert __version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_graph_edge_svg_world_origin_matches_node_world_origin() -> None:
    app = read("data_curation_tool/static/app.js")
    css = read("data_curation_tool/static/styles.css")
    graph_slice = app[app.index("function graphEditorCanvas(graph)"):app.index("function graphEditorNodeInspectorPanel", app.index("function graphEditorCanvas(graph)"))]

    assert "viewBox', '-5000 -5000 10000 10000'" in graph_slice
    assert "svg.style.left = '-5000px'" in graph_slice
    assert "svg.style.top = '-5000px'" in graph_slice
    assert "svg.style.width = '10000px'" in graph_slice
    assert "svg.style.height = '10000px'" in graph_slice
    assert ".agent-graph-canvas.functional .agent-graph-edges" in css
    edge_css = css[css.rindex(".agent-graph-canvas.functional .agent-graph-edges"):]
    assert "left: -5000px" in edge_css
    assert "top: -5000px" in edge_css
    assert "pointer-events: auto" in edge_css


def test_model_load_and_unload_queue_before_optional_placement_preflight() -> None:
    app = read("data_curation_tool/static/app.js")
    load_start = app.index("async function queueModelLoad")
    unload_start = app.index("async function queueModelUnload", load_start)
    table_start = app.index("function modelsTable", unload_start)
    load_slice = app[load_start:unload_start]
    unload_slice = app[unload_start:table_start]

    assert "modelLifecycleJobWatchers" in app
    assert "function watchModelLifecycleJob" in app
    assert "/api/jobs/${id}" in app[app.index("function watchModelLifecycleJob"):app.index("function watchModelInferenceJob")]
    assert "/api/models/placement/plan" not in load_slice
    assert "setOptimisticModelStage(name, 'load', 'queued'" in load_slice
    assert "type:'model_load'" in load_slice
    assert "watchModelLifecycleJob(r.job_id, name, 'load')" in load_slice
    assert "setOptimisticModelStage(name, 'load', 'unloading'" in unload_slice
    assert "type:'model_unload'" in unload_slice
    assert "watchModelLifecycleJob(r.job_id, name, 'unload')" in unload_slice
    # The queue path patches lifecycle state in place rather than forcing a
    # full shell render before the backend has even returned a job id.
    assert "render(true, true)" not in load_slice
    assert "render(true, true)" not in unload_slice


def test_gpu_selection_is_normalized_and_conflicts_are_rejected_front_and_back() -> None:
    app = read("data_curation_tool/static/app.js")
    service = read("data_curation_tool/services/model_service.py")

    assert "function normalizedModelDeviceSelection" in app
    assert "device = `cuda:${ids[0]}`" in app
    assert "GPU selection conflict" in app
    assert "Use matching values so the model cannot be placed on the wrong GPU" in app
    assert "GPU selection conflict" in service
    assert "Use matching values so the selected model cannot be placed on a different GPU" in service
    assert "actual_runtime_device" in app
    assert "DEVICE MISMATCH" in app


def test_onnx_repair_script_validates_real_api_and_reinstalls_one_gpu_distribution() -> None:
    script = read("scripts/repair_onnxruntime_runtime.py")
    for token in [
        "InferenceSession",
        "get_available_providers",
        "onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23",
        '"uninstall", "-y", "onnxruntime", "onnxruntime-gpu"',
        '"--force-reinstall"',
        "fresh_process_report",
    ]:
        assert token in script
    for rel in ["install.bat", "update.bat", "install.sh", "update.sh"]:
        text = read(rel)
        assert "repair_onnxruntime_runtime.py --ensure-gpu" in text


def test_wd_adapter_rejects_incomplete_onnx_namespace(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = SimpleNamespace(__file__="fake/onnxruntime/__init__.py", get_available_providers=lambda: ["CPUExecutionProvider"])
    monkeypatch.setitem(__import__("sys").modules, "onnxruntime", fake)
    with pytest.raises(RuntimeError, match="InferenceSession"):
        WDOnnxTaggerAdapter._onnxruntime_module()


def test_wd_adapter_honors_explicit_cuda_provider_and_device_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class FakeInput:
        name = "input"
        shape = [1, 448, 448, 3]

    class FakeSession:
        def __init__(self, path: str, providers=None):
            calls["path"] = path
            calls["providers"] = providers

        def get_providers(self):
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]

        def get_inputs(self):
            return [FakeInput()]

    fake_ort = SimpleNamespace(
        InferenceSession=FakeSession,
        get_available_providers=lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    adapter = WDOnnxTaggerAdapter("wd-test", "WD test", "example/test")
    monkeypatch.setattr(adapter, "_onnxruntime_module", lambda: fake_ort)
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"nonzero")

    adapter._load_onnx(model_path, "cuda:1")

    assert adapter.runtime == "onnxruntime"
    assert adapter.device_value == "cuda:1"
    assert calls["path"] == str(model_path)
    assert calls["providers"] == [
        ("CUDAExecutionProvider", {"device_id": 1}),
        "CPUExecutionProvider",
    ]


def test_wd_adapter_does_not_silently_use_cpu_for_explicit_cuda(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_ort = SimpleNamespace(
        InferenceSession=lambda *args, **kwargs: None,
        get_available_providers=lambda: ["CPUExecutionProvider"],
    )
    adapter = WDOnnxTaggerAdapter("wd-test", "WD test", "example/test")
    monkeypatch.setattr(adapter, "_onnxruntime_module", lambda: fake_ort)
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"nonzero")

    with pytest.raises(RuntimeError, match="CPU fallback is disabled"):
        adapter._load_onnx(model_path, "cuda:0")


def _write_tag_file(folder: Path) -> None:
    (folder / "selected_tags.csv").write_text(
        "tag_id,name,category\n0,test_tag,0\n",
        encoding="utf-8",
    )


def test_wd_and_pixai_local_integrity_accept_only_runnable_payload_sets(tmp_path: Path) -> None:
    model_root = tmp_path / "models"
    registry = ModelRegistry(model_root)

    wd = registry.get_record("wd-vit-tagger")
    wd_dir = wd.local_dir(model_root, prefer_existing=False)
    assert wd_dir is not None
    wd_dir.mkdir(parents=True, exist_ok=True)
    (wd_dir / "model.safetensors").write_bytes(b"weights")
    _write_tag_file(wd_dir)
    assert wd.is_downloaded(model_root) is False  # safetensors requires config.json
    (wd_dir / "config.json").write_text(
        '{"architecture":"vit_base_patch16_224","num_classes":1}',
        encoding="utf-8",
    )
    assert wd.is_downloaded(model_root) is True

    wd_onnx = registry.get_record("wd-swinv2-tagger")
    wd_onnx_dir = wd_onnx.local_dir(model_root, prefer_existing=False)
    assert wd_onnx_dir is not None
    wd_onnx_dir.mkdir(parents=True, exist_ok=True)
    (wd_onnx_dir / "model.onnx").write_bytes(b"weights")
    _write_tag_file(wd_onnx_dir)
    assert wd_onnx.is_downloaded(model_root) is True

    pixai = registry.get_record("pixai-tagger-v09")
    pixai_dir = pixai.local_dir(model_root, prefer_existing=False)
    assert pixai_dir is not None
    pixai_dir.mkdir(parents=True, exist_ok=True)
    (pixai_dir / "model.safetensors").write_bytes(b"not-supported-for-this-row")
    (pixai_dir / "config.json").write_text("{}", encoding="utf-8")
    _write_tag_file(pixai_dir)
    assert pixai.is_downloaded(model_root) is False
    (pixai_dir / "model.onnx").write_bytes(b"weights")
    assert pixai.is_downloaded(model_root) is True


def test_wd_pixai_changes_are_isolated_from_legacy_tagger_adapter() -> None:
    adapters = read("data_curation_tool/models/adapters.py")
    registry = read("data_curation_tool/models/registry.py")
    assert "class WDOnnxTaggerAdapter" in adapters
    assert "class LegacyVisionTaggerAdapter" in adapters
    wd_start = adapters.index("class WDOnnxTaggerAdapter")
    legacy_start = adapters.index("class LegacyVisionTaggerAdapter", wd_start)
    isolated_slice = adapters[wd_start:legacy_start]
    assert "timm_safetensors" in isolated_slice
    assert "CPU fallback is disabled" in isolated_slice
    for model_id in [
        "pixai-tagger-v09",
        "wd-convnext-tagger-v3",
        "wd-eva02-large-tagger-v3",
        "wd-swinv2-tagger",
        "wd-vit-tagger",
    ]:
        idx = registry.index(f'ModelRecord("{model_id}"')
        assert "WDOnnxTaggerAdapter" in registry[idx:registry.find("))", idx) + 2]


def test_all_certified_graph_templates_build_validate_and_complete(tmp_path: Path) -> None:
    service = GraphEditorService(SimpleNamespace(runtime=tmp_path))
    catalog = service.catalog()
    keys = set(catalog.get("certified_template_keys") or [])
    expected = {
        "guaranteed_graph_runtime_smoke_test",
        "guaranteed_empty_branch_readiness_workflow",
        "guaranteed_multimodal_manifest_preview",
        "certified_tag_normalization_preview",
        "certified_dataset_qa_export_plan",
        "certified_closed_loop_training_improvement_preview",
    }
    assert expected.issubset(keys)
    assert catalog.get("certified_template_count") >= 10
    assert catalog.get("template_self_test_endpoint") == "/api/graph-editor/templates/self-test"

    result = service.certify_templates()
    assert result["ok"] is True
    assert result["status"] == "passed"
    assert result["tested"] >= 10
    assert result["passed"] >= 10
    assert result["failed"] == 0
    assert expected.issubset({item["key"] for item in result["items"]})
    for item in result["items"]:
        assert item["ok"] is True
        assert item["status"] == "completed"
        assert item["completed_node_count"] == item["node_count"]
        assert item["external_dependencies"] == []


def test_certified_workflow_self_test_is_exposed_in_api_and_gui() -> None:
    router = read("data_curation_tool/routers/graph_editor.py")
    app = read("data_curation_tool/static/app.js")
    assert '@router.post("/templates/self-test")' in router
    assert "certify_templates(keys)" in router
    assert "function selfTestCertifiedAgenticWorkflows" in app
    assert "/api/graph-editor/templates/self-test" in app
    assert "Self-Test All Certified Workflows" in app
    assert "Self-Test Selected" in app


def test_new_workflow_readmes_and_release_docs_are_bundled() -> None:
    for rel, marker in [
        ("docs/agentic_workflows/certified_tag_normalization_preview.md", "Tag Normalization"),
        ("docs/agentic_workflows/certified_dataset_qa_export_plan.md", "Dataset QA"),
        ("docs/agentic_workflows/certified_closed_loop_training_improvement_preview.md", "Closed-Loop"),
        ("docs/V5_8_34_GRAPH_EDGES_MODEL_LIFECYCLE_ONNX_WORKFLOW_CERTIFICATION.md", "v5.8.34"),
        ("docs/wiki/64-Graph-Edges-Model-Lifecycle-ONNX-Workflow-Certification.md", "v5.8.34"),
    ]:
        path = ROOT / rel
        assert path.exists()
        assert marker.lower() in path.read_text(encoding="utf-8").lower()

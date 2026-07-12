from __future__ import annotations

from types import SimpleNamespace

from data_curation_tool import __version__
from data_curation_tool.services.graph_editor_service import GraphEditorService


def read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def test_version_bumped_to_5833():
    assert __version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_hf_download_progress_is_bridged_to_lifecycle():
    registry = read("data_curation_tool/models/registry.py")
    assert "download_progress_tqdm_class" in registry
    assert "progress(frac, msg)" in registry
    assert "download_kwargs[\"tqdm_class\"] = tqdm_class" in registry
    assert "start_directory_progress_monitor" in registry


def test_model_service_unsticks_completed_local_download_payloads():
    service = read("data_curation_tool/services/model_service.py")
    assert "_complete_active_download_if_local_payload_ready" in service
    assert "Local model payload detected; download marked complete" in service
    assert "self._complete_active_download_if_local_payload_ready(request.model_name)" in service
    assert "Finalizing local model catalog entry" in service


def test_frontend_download_watcher_and_readme_tab_are_registered():
    app = read("data_curation_tool/static/app.js")
    assert "modelDownloadJobWatchers" in app
    assert "function watchModelDownloadJob" in app
    assert "watchModelDownloadJob(r.job_id, name)" in app
    assert "Agentic Workflow READMEs" in app
    assert "function agenticWorkflowReadmesView" in app
    assert "guaranteed_graph_runtime_smoke_test" in app
    assert "guaranteed_empty_branch_readiness_workflow" in app
    assert "guaranteed_multimodal_manifest_preview" in app


def test_guaranteed_graph_templates_exist_in_catalog_and_execute(tmp_path):
    svc = GraphEditorService(SimpleNamespace(runtime=tmp_path))
    catalog = svc.catalog()
    keys = {row.get("key") for row in catalog.get("workflow_templates") or []}
    expected = {
        "guaranteed_graph_runtime_smoke_test",
        "guaranteed_empty_branch_readiness_workflow",
        "guaranteed_multimodal_manifest_preview",
    }
    assert expected.issubset(keys)
    for key in sorted(expected):
        graph = svc.create_from_template({"template_key": key, "name": key})
        assert graph.get("validation", {}).get("ok") is True
        assert graph.get("metadata", {}).get("known_good_runtime") is True
        result = svc.execute_session(
            graph,
            {
                "dry_run": True,
                "approve_unsafe_steps": False,
                "stop_on_approval_gate": True,
                "allow_model_calls": False,
            },
        )
        assert result["ok"] is True
        assert result["status"] == "completed"
        assert result["node_results"]


def test_workflow_readme_docs_are_bundled():
    assert "Known-Good Agentic Workflow Templates" in read("docs/agentic_workflows/README.md")
    assert "Guaranteed smoke test" in read("docs/agentic_workflows/guaranteed_graph_runtime_smoke_test.md")
    assert "empty branch readiness" in read("docs/agentic_workflows/guaranteed_empty_branch_readiness_workflow.md")
    assert "multimodal preview" in read("docs/agentic_workflows/guaranteed_multimodal_manifest_preview.md")
    assert "Agentic Workflow READMEs" in read("docs/V5_8_33_DOWNLOAD_PROGRESS_AND_GUARANTEED_GRAPHS.md")

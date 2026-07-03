from __future__ import annotations

from pathlib import Path

from data_curation_tool.schemas import ModelTagSelectionRequest


def test_frontend_global_dropdown_hold_and_deferred_scheduled_render():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Native SELECT menus live outside the DOM" in app_js
    assert "releaseDropdownInteractionSoon" in app_js
    assert "Math.max(Number(holdMs || 0), 90000)" in app_js
    assert "setTimeout(() => { state.renderScheduled = false; renderOrDeferForEditing(); }, delay)" in app_js


def test_frontend_manual_tag_selection_controls_and_candidates():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "selection-toolbar" in app_js
    assert "0 highlighted" in app_js
    assert "toggleEditorSelectedTag" in app_js
    assert "Select by Category" in app_js
    assert "Deselect by Category" in app_js
    assert "candidate_tags: manualTags" in app_js
    assert "highlighted/manual only" in app_js
    assert "getCandidateTags: () => editorManualCandidateTags(item)" in app_js


def test_tag_selection_schema_accepts_full_runtime_placement_payload():
    payload = ModelTagSelectionRequest(
        media_ids=[1],
        model_name="gemma-4-e4b-it",
        operation="preview",
        device="cuda:0",
        device_ids=[0],
        sharding_strategy="balanced_low_0",
        max_memory={"0": "23GiB"},
        torch_dtype="bfloat16",
        quantization="none",
        runtime_engine="transformers",
        tensor_parallel_size=1,
        candidate_tags=["blue_hair"],
        candidate_tags_by_media={"1": ["blue_hair"]},
        options={"manual_only": True},
    )
    assert payload.device_ids == [0]
    assert payload.sharding_strategy == "balanced_low_0"
    assert payload.max_memory["0"] == "23GiB"
    assert payload.candidate_tags == ["blue_hair"]
    assert payload.candidate_tags_by_media["1"] == ["blue_hair"]


def test_backend_vlm_tag_selection_path_is_not_heuristic_only():
    service = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    assert "VLM/LLM tag-selection started" in service
    assert "self.registry.chat(request.model_name, prompt" in service
    assert "chat_model_used" in service
    assert "manual_selection_used" in service
    assert "candidate_tags_by_media" in service
    assert "Highlighted/manual candidate tags" in service


def test_frontend_keeps_vlm_preview_candidates_that_are_not_in_current_draft():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    styles = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "selectedCandidateTagsOutsideDraft" in app_js
    assert "Highlighted candidate tags not yet in the draft" in app_js
    assert "Add Highlighted Candidates to Draft" in app_js
    assert "Clear Candidate Highlights" in app_js
    assert "pruneEditorSelection" not in app_js
    assert ".assistant-candidate-tags" in styles


def test_gpu_plan_reports_detected_but_torch_unusable_gpu(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from data_curation_tool.app import create_app
    from data_curation_tool.paths import AppPaths
    from data_curation_tool.services import model_service as model_service_module

    def fake_detect_devices():
        return {
            "devices": [
                {
                    "id": "cuda:0",
                    "index": 0,
                    "name": "RTX 3090 test GPU",
                    "type": "cuda",
                    "total_memory_gb": 24.0,
                    "used_memory_gb": 0.0,
                    "free_memory_gb": 24.0,
                    "torch_ready": False,
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr(model_service_module, "detect_devices", fake_detect_devices)
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    client = TestClient(create_app(paths))
    response = client.post(
        "/api/models/placement/plan",
        json={
            "model_name": "gemma-4-e4b-it",
            "device": "cuda:0",
            "device_ids": [0],
            "sharding_strategy": "none",
            "max_memory": {"0": "23GiB"},
            "torch_dtype": "auto",
            "quantization": "none",
            "runtime_engine": "transformers",
            "tensor_parallel_size": 1,
            "options": {},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["can_load"] is False
    assert any("PyTorch CUDA is not ready" in error for error in payload["errors"])
    assert payload["devices"][0]["torch_ready"] is False
    client.close()

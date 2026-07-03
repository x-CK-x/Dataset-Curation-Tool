from __future__ import annotations

from pathlib import Path

from data_curation_tool.schemas import ModelChatRequest, ModelRunRequest, ModelTagSelectionRequest


def test_blank_frontend_runtime_values_are_coerced_to_safe_defaults():
    chat = ModelChatRequest(model_name="gemma-4-e4b-it", prompt="hello", quantization="", runtime_engine="", torch_dtype="", sharding_strategy="", device="")
    assert chat.quantization == "none"
    assert chat.runtime_engine == "transformers"
    assert chat.torch_dtype == "auto"
    assert chat.sharding_strategy == "none"
    assert chat.device == "auto"

    run = ModelRunRequest(model_name="redrocket-jtp-3", quantization="", runtime_engine="", torch_dtype="")
    assert run.quantization == "none"
    assert run.runtime_engine == "transformers"
    assert run.torch_dtype == "auto"

    select = ModelTagSelectionRequest(model_name="gemma-4-e4b-it", quantization="", runtime_engine="")
    assert select.quantization == "none"
    assert select.runtime_engine == "transformers"


def test_frontend_sanitizes_runtime_payload_and_keeps_models_tab_in_place():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function runtimeBodyFromControls" in app_js
    assert "selectValueOr(rt.quant, 'none')" in app_js
    assert "selectValueOr(rt.runtime, 'transformers')" in app_js
    assert "inlineSelectedModelRuntimeControls" in app_js
    assert "Queue Download" in app_js and "Load Into Memory" in app_js and "Check VRAM" in app_js
    # Models-tab model actions should now stay in place and rely on the explicit Open Last Job button.
    assert "Model download'} queued as job ${r.job_id} using ${modelDownloadModeLabel()}.`);\n    render();" in app_js
    assert "toast(`Model job ${r.job_id} queued`);\n            await refreshCompletedModelJobById(r.job_id);\n            render();" in app_js


def test_selection_cache_and_chat_history_controls_exist():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "selectedMediaCache" in app_js
    assert "selectedMediaItemsCached" in app_js
    assert "Delete from here" in app_js
    assert "Clear memory" in app_js
    assert "Clear chat" in app_js
    router = Path("data_curation_tool/routers/models.py").read_text(encoding="utf-8")
    service = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    assert "/chat/conversations/{conversation_id}/messages/{message_id}" in router
    assert "/chat/conversations/{conversation_id}/clear" in router
    assert "def delete_conversation_message" in service
    assert "def clear_conversation" in service

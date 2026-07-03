from __future__ import annotations

from pathlib import Path

from data_curation_tool.services.model_service import ModelService


def test_frontend_has_bottom_chat_composers_and_finish_buttons():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    css = Path("data_curation_tool/static/styles.css").read_text(encoding="utf-8")
    assert "chat-composer-input" in app_js
    assert "Finish Last Output" in app_js
    assert "continue_last_output" in app_js
    assert "auto_continue_incomplete" in app_js
    assert "tagSelectionChatDraft" in app_js
    assert "codeChatDraft" in app_js
    assert "chat-composer" in css


def test_model_service_has_completion_guards_for_chat_and_tag_tasks():
    src = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    assert "_response_looks_incomplete" in src
    assert "_continue_incomplete_response_prompt" in src
    assert "_continue_incomplete_tag_task_prompt" in src
    assert "[TASK_COMPLETE]" in src
    assert "max_tag_continuation_rounds" in src
    assert "No tag changes were applied" in src


def test_merge_continuation_text_removes_overlap():
    service = object.__new__(ModelService)
    assert service._merge_continuation_text("alpha beta gamma", "gamma delta") == "alpha beta gamma delta"
    assert service._strip_completion_markers("tags: a, b\n[TASK_COMPLETE]") == "tags: a, b"
    assert service._has_task_completion_marker("done [TASK_COMPLETE]") is True


def test_incomplete_response_heuristic_catches_mid_sentence_tail():
    service = object.__new__(ModelService)
    assert service._response_looks_incomplete("This is a longer answer that clearly continues because", {"max_new_tokens": 64}) is True
    assert service._response_looks_incomplete("This is a complete answer.", {"max_new_tokens": 64}) is False

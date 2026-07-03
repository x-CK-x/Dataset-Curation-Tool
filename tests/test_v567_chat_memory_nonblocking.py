from __future__ import annotations

from pathlib import Path


def test_clear_memory_creates_context_reset_and_zero_budget():
    service = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    router = Path("data_curation_tool/routers/models.py").read_text(encoding="utf-8")
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")

    assert "context_reset_message_id" in service
    assert "Earlier visible transcript messages were intentionally excluded" in service
    assert "last_context_budget" in service and "context_cleared" in service
    assert "reset_context=bool(payload.get(\"reset_context\", True))" in router
    assert "setScopeContextCleared" in app_js
    assert "zeroContextBudget" in app_js
    assert "Visible transcript remains only as a UI record" in app_js


def test_chat_composers_are_nonblocking_and_queue_messages():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")

    assert "tagSelectionChatQueue" in app_js
    assert "tagSelectionChatCurrent" in app_js
    assert "codeChatQueue" in app_js
    assert "codeChatCurrent" in app_js
    assert "sendQueuedTagSelectionChat" in app_js
    assert "sendQueuedCodeChat" in app_js
    assert "Queue Message" in app_js
    assert "You · queued #" in app_js
    assert "A response is still running; this message will be queued" in app_js
    assert "disabled: !composerCfg.onSend" in app_js
    assert "disabled: Boolean(composerCfg.disabled)" not in app_js

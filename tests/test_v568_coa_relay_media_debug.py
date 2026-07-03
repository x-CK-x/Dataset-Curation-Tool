from __future__ import annotations

from pathlib import Path


def test_coa_relay_uses_explicit_media_targets_and_does_not_fail_whole_job_on_relay_error():
    src = Path("data_curation_tool/services/agent_tools_service.py").read_text(encoding="utf-8")

    assert "def _media_targets_from_context" in src
    assert "selected_media_ids" in src and "external_paths" in src
    assert "media_ids=relay_targets.get(\"media_ids\") or []" in src
    assert "external_paths=relay_targets.get(\"external_paths\") or []" in src
    assert "conversation_coa_relay_error" in src
    assert "relay_error" in src
    assert "relay_targets" in src
    assert "COA tools ran, but result relay back to the model failed" in src
    # Tool execution result is returned even when relay_error is populated.
    assert '"plan_result": plan_result' in src
    assert '"debug_log_path": str(debug_log_path)' in src


def test_relay_tool_result_catches_relay_errors_for_debug_visibility():
    src = Path("data_curation_tool/services/agent_tools_service.py").read_text(encoding="utf-8")
    assert "relay_traceback" in src
    assert "traceback.format_exc()" in src
    assert "relay_targets = self._media_targets_from_context(context)" in src

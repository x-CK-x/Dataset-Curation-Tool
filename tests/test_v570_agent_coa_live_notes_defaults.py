from __future__ import annotations

from pathlib import Path

import data_curation_tool.services.agent_tools_service as agent_module
from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.agent_tools_service import AgentToolsService


def _svc(tmp_path: Path) -> AgentToolsService:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return AgentToolsService(paths, AppSettings(), None)


def test_agent_tool_defaults_match_interactive_local_coa_expectations():
    s = AppSettings()
    assert s.agent_tools_enabled is True
    assert s.agent_tools_require_approval is True
    assert s.agent_tools_allow_shell is True
    assert s.agent_tools_allow_python is True
    assert s.agent_tools_allow_file_write is True
    assert s.agent_tools_allow_browser is True
    assert s.agent_tools_allow_existing_browser_profile is True
    assert s.agent_tools_allow_high_risk is True
    assert s.agent_tools_allow_any_path is True
    assert s.agent_tools_enable_approved_coa_execution is True
    assert s.agent_tools_auto_relay_after_execution is True
    assert s.agent_tools_sandbox_mode == "local"
    assert s.agent_tools_confirmation_mode == "always"
    assert s.agent_tools_auto_reattempt_enabled is True
    assert s.assistant_show_live_action_notes is True
    assert any("Downloads" in p for p in s.agent_tools_allowed_roots)
    assert any("Desktop" in p for p in s.agent_tools_allowed_roots)
    assert any("Documents" in p for p in s.agent_tools_allowed_roots)


def test_powershell_wrapper_is_stripped_before_nested_execution(tmp_path: Path):
    svc = _svc(tmp_path)
    old_name = agent_module.os.name
    agent_module.os.name = "nt"
    try:
        command, shell = svc._normalize_shell_invocation(
            '"%SystemRoot%\\system32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "python -c \'import json; print(123)\'"',
            "powershell",
        )
    finally:
        agent_module.os.name = old_name
    assert shell == "powershell"
    assert command == "python -c 'import json; print(123)'"
    assert "powershell.exe" not in command.lower()
    assert "-command" not in command.lower()


def test_agent_tools_define_resource_and_model_spawn_tools(tmp_path: Path):
    svc = _svc(tmp_path)
    names = {row["name"] for row in svc.tool_definitions()}
    assert "inspect_model_resources" in names
    assert "run_model_chat" in names


def test_frontend_has_live_action_overlay_and_controls():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function liveActionNotesOverlay" in src
    assert "show_live_action_notes" in src
    assert "COA confirmation mode" in src
    assert "auto re-attempt failed COAs" in src
    assert "orchestrator may spawn other models" in src


def test_hidden_cot_flag_remains_private_but_visible_notes_exist():
    src = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    assert '"hidden_chain_of_thought_exposed": False' in src
    assert '"live_action_notes_enabled"' in src

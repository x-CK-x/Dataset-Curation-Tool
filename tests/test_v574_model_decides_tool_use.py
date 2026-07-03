from __future__ import annotations

from pathlib import Path

from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.agent_tools_service import AgentToolsService


def _svc(tmp_path: Path) -> AgentToolsService:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return AgentToolsService(paths, AppSettings(), None)


def test_agent_settings_default_to_model_decided_tool_use():
    s = AppSettings()
    assert s.agent_tools_model_decides_when_to_use_tools is True
    assert s.agent_tools_allow_plain_chat_without_tools is True
    assert s.agent_tools_app_gui_action_routing is True
    assert s.agent_tools_show_tool_decision_badges is True


def test_tool_definitions_include_app_gui_action(tmp_path: Path):
    svc = _svc(tmp_path)
    names = {row["name"] for row in svc.tool_definitions()}
    assert "app_gui_action" in names
    assert "run_shell_command" in names
    assert "run_model_chat" in names


def test_infer_tool_decision_distinguishes_no_tool_gui_and_local(tmp_path: Path):
    svc = _svc(tmp_path)
    no_tool = svc.infer_tool_decision(goal="Explain what this tag means", response_text="This can be answered directly.", tool_calls=[])
    assert no_tool["mode"] == "answer_directly"
    assert no_tool["tools_needed"] is False

    gui = svc.infer_tool_decision(goal="Open the Jobs tab", plan={"tool_decision": {"mode": "app_gui_action", "reason": "Use app UI"}}, tool_calls=[{"tool": "app_gui_action", "arguments": {"action": "open_tab", "target": "Jobs"}}])
    assert gui["mode"] == "app_gui_action"
    assert gui["gui_action_needed"] is True
    assert gui["tools_needed"] is False

    local = svc.infer_tool_decision(goal="Read a file", tool_calls=[{"tool": "run_shell_command", "arguments": {"shell": "powershell", "command": "Get-Content file.txt"}}])
    assert local["mode"] == "local_tools"
    assert local["tools_needed"] is True


def test_chat_prompt_contract_allows_direct_answers_and_gui_actions():
    src = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    assert "tool availability does NOT mean every prompt needs a tool" in src
    assert "DIRECT_ANSWER" in src
    assert "APP_GUI_ACTION" in src
    assert "TOOL_COA" in src
    assert "do NOT output empty JSON" in src
    assert '"agent_tool_decision"' in src


def test_frontend_shows_tool_decision_badges_and_no_tool_plan_ui():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "agentToolDecisionPill" in src
    assert "agentToolDecisionBadge" in src
    assert "Assess / Plan Tool Use If Needed" in src
    assert "allow no-tool/direct chat" in src
    assert "show tool-decision badges" in src

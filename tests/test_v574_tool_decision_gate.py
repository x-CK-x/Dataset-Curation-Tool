from __future__ import annotations

from pathlib import Path

from data_curation_tool.config import AppSettings
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.agent_tools_service import AgentToolsService


def _svc(tmp_path: Path) -> AgentToolsService:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return AgentToolsService(paths, AppSettings(), None)


def test_tool_decision_settings_default_to_model_decides_not_tool_forced():
    s = AppSettings()
    assert s.agent_tools_model_decides_when_to_use_tools is True
    assert s.agent_tools_allow_plain_chat_without_tools is True
    assert s.agent_tools_app_gui_action_routing is True
    assert s.agent_tools_show_tool_decision_badges is True


def test_agent_tool_definitions_include_app_gui_action(tmp_path: Path):
    svc = _svc(tmp_path)
    names = {row["name"] for row in svc.tool_definitions()}
    assert "app_gui_action" in names
    status = svc.status()
    assert status["model_decides_when_to_use_tools"] is True
    assert status["allow_plain_chat_without_tools"] is True
    assert status["app_gui_action_routing"] is True


def test_infer_tool_decision_preserves_direct_answer_no_tool(tmp_path: Path):
    svc = _svc(tmp_path)
    decision = svc.infer_tool_decision(goal="Explain this tag.", response_text="This tag means the character is smiling.", plan={}, tool_calls=[])
    assert decision["mode"] == "answer_directly"
    assert decision["tools_needed"] is False
    assert decision["gui_action_needed"] is False


def test_app_gui_action_parses_and_executes_as_safe_app_request(tmp_path: Path):
    svc = _svc(tmp_path)
    text = '{"tool_calls":[{"tool":"app_gui_action","arguments":{"action":"open_tab","target":"Jobs","note":"Show job logs"},"risk":"low"}]}'
    calls = svc.parse_tool_calls(text)
    assert calls and calls[0]["tool"] == "app_gui_action"
    result = svc.execute_tool_call(calls[0], approved=True)
    assert result["ok"] is True
    assert result["type"] == "app_gui_action"
    assert result["action"] == "open_tab"
    assert result["target"] == "Jobs"


def test_model_prompt_contract_says_tools_are_not_required_for_every_prompt():
    src = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    assert "tool availability does NOT mean every prompt needs a tool" in src
    assert "DIRECT_ANSWER" in src
    assert "APP_GUI_ACTION" in src
    assert "TOOL_COA" in src
    assert "If no tool is needed" in src


def test_frontend_exposes_tool_decision_controls_and_badges():
    src = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function agentToolDecisionPill" in src
    assert "model decides if tools are needed" in src
    assert "allow no-tool/direct chat" in src
    assert "enable app/GUI action routing" in src
    assert "show tool-decision badges" in src

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/agent-tools", tags=["agent-tools"])


class AgentPlanRequest(BaseModel):
    goal: str
    model_name: str = "dataset-assistant"
    context: str = ""
    media_ids: list[int] = Field(default_factory=list)
    external_paths: list[str] = Field(default_factory=list)
    surface: str = "agent-tools"
    conversation_id: int | None = None
    token_profile: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: str = "none"
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: str = "none"
    runtime_engine: str = "transformers"
    tensor_parallel_size: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class AgentCommandRequest(BaseModel):
    command: str
    shell: str = "auto"
    cwd: str | None = None
    timeout_seconds: int | None = None
    user_approved: bool = False
    allow_high_risk: bool = False
    confirmation_text: str = ""


class AgentPythonRequest(BaseModel):
    script: str
    requirements: list[str] = Field(default_factory=list)
    create_venv: bool = True
    cwd: str | None = None
    timeout_seconds: int | None = None
    user_approved: bool = False
    allow_high_risk: bool = False
    confirmation_text: str = ""


class AgentPathRequest(BaseModel):
    path: str
    user_approved: bool = False
    max_entries: int = 500
    max_chars: int = 120000


class AgentWriteFileRequest(BaseModel):
    path: str
    content: str
    user_approved: bool = False
    create_backup: bool = True


class AgentFetchUrlRequest(BaseModel):
    url: str
    user_approved: bool = False
    timeout_seconds: int = 60
    max_chars: int = 120000


class AgentBrowserOpenRequest(BaseModel):
    url: str = "about:blank"
    private: bool = True
    headless: bool = False
    use_existing_profile: bool = False
    profile_path: str | None = None
    user_approved: bool = False


class AgentToolCallRequest(BaseModel):
    tool_call: dict[str, Any]
    user_approved: bool = False
    allow_high_risk: bool = False
    confirmation_text: str = ""


class AgentParseToolCallsRequest(BaseModel):
    text: str


class AgentRunPlanRequest(BaseModel):
    plan: dict[str, Any] | list[dict[str, Any]] | str
    user_approved: bool = False
    allow_high_risk: bool = False
    confirmation_text: str = ""
    enable_for_this_run: bool = False



class AgentConversationCoaRequest(BaseModel):
    conversation_id: int
    message_id: int | None = None


class AgentRunConversationCoaRequest(BaseModel):
    conversation_id: int
    message_id: int | None = None
    coa_index: int = 0
    user_approved: bool = False
    allow_high_risk: bool = False
    confirmation_text: str = ""
    enable_for_this_run: bool = False
    relay_result: bool = True
    model_name: str = "dataset-assistant"
    surface: str = "agent-tools"
    context: str = ""
    token_profile: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: str = "none"
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: str = "none"
    runtime_engine: str = "transformers"
    tensor_parallel_size: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class AgentRelayResultRequest(BaseModel):
    job_id: int
    model_name: str = "dataset-assistant"
    conversation_id: int | None = None
    surface: str = "agent-tools"
    context: str = ""
    token_profile: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: str = "none"
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: str = "none"
    runtime_engine: str = "transformers"
    tensor_parallel_size: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
def status(request: Request):
    return ctx(request).agent_tools.status()


@router.get("/definitions")
def definitions(request: Request):
    return {"tools": ctx(request).agent_tools.tool_definitions()}


@router.post("/smoke-test")
def smoke_test(request: Request, force: bool = True):
    try:
        return ctx(request).agent_tools.smoke_test_tools(force=force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent tool smoke test failed: {exc}") from exc


@router.get("/debug-logs")
def debug_logs(request: Request, limit: int = 50):
    return ctx(request).agent_tools.list_debug_logs(limit=limit)


@router.get("/debug-log")
def debug_log(request: Request, path: str, max_chars: int = 240000):
    try:
        return ctx(request).agent_tools.read_debug_log(path, max_chars=max_chars)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/risk")
def risk(payload: AgentCommandRequest, request: Request):
    return ctx(request).agent_tools.risk_assessment(payload.command, payload.shell)


@router.post("/parse-tool-calls")
def parse_tool_calls(payload: AgentParseToolCallsRequest, request: Request):
    return {"tool_calls": ctx(request).agent_tools.parse_tool_calls(payload.text)}


@router.post("/plan")
def plan(payload: AgentPlanRequest, request: Request):
    try:
        runtime = {"device": payload.device or "auto", "device_ids": payload.device_ids or [], "sharding_strategy": payload.sharding_strategy or "none", "max_memory": payload.max_memory or {}, "torch_dtype": payload.torch_dtype or "auto", "quantization": payload.quantization or "none", "runtime_engine": payload.runtime_engine or "transformers", "tensor_parallel_size": payload.tensor_parallel_size or 1}
        options = dict(payload.options or {})
        if payload.token_profile:
            options["token_profile"] = payload.token_profile
        return ctx(request).agent_tools.propose_plan(goal=payload.goal, model_name=payload.model_name, context=payload.context, surface=payload.surface, conversation_id=payload.conversation_id, runtime=runtime, options=options, media_ids=payload.media_ids, external_paths=payload.external_paths)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent tool plan failed: {exc}") from exc


@router.post("/command")
def command(payload: AgentCommandRequest, request: Request):
    c = ctx(request)
    try:
        def task(progress, job_id: int):
            return c.agent_tools.run_command(command=payload.command, shell=payload.shell, cwd=payload.cwd, timeout_seconds=payload.timeout_seconds, approved=payload.user_approved, allow_high_risk=payload.allow_high_risk, confirmation_text=payload.confirmation_text, progress=progress)
        job_id = c.jobs.submit_with_job_id("agent_tool_command", payload.model_dump(), task)
        return {"queued": True, "job_id": job_id, "type": "agent_tool_command"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/python")
def python(payload: AgentPythonRequest, request: Request):
    c = ctx(request)
    try:
        params = {**payload.model_dump(), "script": payload.script[:2000] + ("...[truncated]" if len(payload.script) > 2000 else "")}
        def task(progress, job_id: int):
            return c.agent_tools.run_python(script=payload.script, cwd=payload.cwd, timeout_seconds=payload.timeout_seconds, approved=payload.user_approved, allow_high_risk=payload.allow_high_risk, confirmation_text=payload.confirmation_text, progress=progress, requirements=payload.requirements, create_venv=payload.create_venv)
        job_id = c.jobs.submit_with_job_id("agent_tool_python", params, task)
        return {"queued": True, "job_id": job_id, "type": "agent_tool_python"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/run-plan")
def run_plan(payload: AgentRunPlanRequest, request: Request):
    c = ctx(request)
    try:
        params = payload.model_dump()
        def task(progress, job_id: int):
            return c.agent_tools.run_tool_plan(plan=payload.plan, approved=payload.user_approved, allow_high_risk=payload.allow_high_risk, confirmation_text=payload.confirmation_text, enable_for_this_run=payload.enable_for_this_run, progress=progress)
        job_id = c.jobs.submit_with_job_id("agent_tool_plan_run", params, task)
        return {"queued": True, "job_id": job_id, "type": "agent_tool_plan_run"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/execute-tool-call")
def execute_tool_call(payload: AgentToolCallRequest, request: Request):
    c = ctx(request)
    try:
        def task(progress, job_id: int):
            return c.agent_tools.execute_tool_call(payload.tool_call, approved=payload.user_approved, allow_high_risk=payload.allow_high_risk, confirmation_text=payload.confirmation_text, progress=progress)
        job_id = c.jobs.submit_with_job_id("agent_tool_call", payload.model_dump(), task)
        return {"queued": True, "job_id": job_id, "type": "agent_tool_call"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc





@router.post("/conversation-coas")
def conversation_coas(payload: AgentConversationCoaRequest, request: Request):
    try:
        return ctx(request).agent_tools.conversation_coa_options(payload.conversation_id, payload.message_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run-conversation-coa")
def run_conversation_coa(payload: AgentRunConversationCoaRequest, request: Request):
    c = ctx(request)
    try:
        runtime = {"device": payload.device or "auto", "device_ids": payload.device_ids or [], "sharding_strategy": payload.sharding_strategy or "none", "max_memory": payload.max_memory or {}, "torch_dtype": payload.torch_dtype or "auto", "quantization": payload.quantization or "none", "runtime_engine": payload.runtime_engine or "transformers", "tensor_parallel_size": payload.tensor_parallel_size or 1}
        options = dict(payload.options or {})
        if payload.token_profile:
            options["token_profile"] = payload.token_profile
        params = payload.model_dump()
        def task(progress, job_id: int):
            return c.agent_tools.run_conversation_coa(
                conversation_id=payload.conversation_id,
                message_id=payload.message_id,
                coa_index=payload.coa_index,
                approved=payload.user_approved,
                allow_high_risk=payload.allow_high_risk,
                confirmation_text=payload.confirmation_text,
                enable_for_this_run=payload.enable_for_this_run,
                model_name=payload.model_name,
                surface=payload.surface,
                context=payload.context,
                runtime=runtime,
                options=options,
                relay_result=payload.relay_result,
                progress=progress,
            )
        job_id = c.jobs.submit_with_job_id("agent_tool_conversation_coa", params, task)
        return {"queued": True, "job_id": job_id, "type": "agent_tool_conversation_coa"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/relay-result")
def relay_result(payload: AgentRelayResultRequest, request: Request):
    c = ctx(request)
    try:
        job = c.jobs.get_job(payload.job_id)
        if not job:
            raise ValueError(f"Job not found: {payload.job_id}")
        runtime = {"device": payload.device or "auto", "device_ids": payload.device_ids or [], "sharding_strategy": payload.sharding_strategy or "none", "max_memory": payload.max_memory or {}, "torch_dtype": payload.torch_dtype or "auto", "quantization": payload.quantization or "none", "runtime_engine": payload.runtime_engine or "transformers", "tensor_parallel_size": payload.tensor_parallel_size or 1}
        options = dict(payload.options or {})
        if payload.token_profile:
            options["token_profile"] = payload.token_profile
        return c.agent_tools.relay_tool_result(job=job, model_name=payload.model_name, conversation_id=payload.conversation_id, surface=payload.surface, context=payload.context, runtime=runtime, options=options)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent tool result relay failed: {exc}") from exc


@router.post("/files/list")
def list_path(payload: AgentPathRequest, request: Request):
    try:
        return ctx(request).agent_tools.list_path(payload.path, approved=payload.user_approved, max_entries=payload.max_entries)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/files/read")
def read_file(payload: AgentPathRequest, request: Request):
    try:
        return ctx(request).agent_tools.read_file(payload.path, approved=payload.user_approved, max_chars=payload.max_chars)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/files/write")
def write_file(payload: AgentWriteFileRequest, request: Request):
    try:
        return ctx(request).agent_tools.write_file(payload.path, payload.content, approved=payload.user_approved, create_backup=payload.create_backup)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fetch-url")
def fetch_url(payload: AgentFetchUrlRequest, request: Request):
    try:
        return ctx(request).agent_tools.fetch_url_text(payload.url, approved=payload.user_approved, timeout_seconds=payload.timeout_seconds, max_chars=payload.max_chars)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/browser/open")
def open_browser(payload: AgentBrowserOpenRequest, request: Request):
    try:
        return ctx(request).agent_tools.open_browser(url=payload.url, private=payload.private, headless=payload.headless, use_existing_profile=payload.use_existing_profile, profile_path=payload.profile_path, approved=payload.user_approved)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

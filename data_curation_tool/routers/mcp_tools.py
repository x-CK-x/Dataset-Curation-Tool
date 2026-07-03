from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/mcp-tools", tags=["mcp-tools"])


class MCPToolSettingsPayload(BaseModel):
    tools: dict[str, dict[str, Any]] = Field(default_factory=dict)


@router.get("/status")
def status(request: Request):
    return ctx(request).mcp_tools.status()


@router.get("/client-config")
def client_config(request: Request):
    return ctx(request).mcp_tools.client_config()


@router.post("/write-client-config")
def write_client_config(request: Request):
    return ctx(request).mcp_tools.write_client_config()


@router.put("/settings")
def update_tool_settings(payload: MCPToolSettingsPayload, request: Request):
    c = ctx(request)
    current = dict(getattr(c.settings, "external_mcp_tools", {}) or {})
    for key, value in payload.tools.items():
        if not isinstance(value, dict):
            continue
        row = dict(current.get(key) or {})
        row.update(value)
        current[key] = row
    c.settings.external_mcp_tools = current
    c.db.set_setting("external_mcp_tools", current)
    c.settings.save(c.paths.settings)
    return c.mcp_tools.write_client_config()

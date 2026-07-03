from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .deps import ctx

router = APIRouter(prefix="/cloud", tags=["cloud-providers"])


class RunPodRunRequest(BaseModel):
    endpoint_id: str
    input: dict[str, Any] = Field(default_factory=dict)
    sync: bool = False
    token_profile: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    timeout: int = 300


class GenericCloudRequest(BaseModel):
    method: str = "GET"
    path: str = "/instances"
    params: dict[str, Any] = Field(default_factory=dict)
    body: dict[str, Any] | None = None
    token_profile: str | None = None
    timeout: int = 120


@router.post("/runpod/run")
def run_runpod(payload: RunPodRunRequest, request: Request):
    try:
        return ctx(request).cloud.runpod(endpoint_id=payload.endpoint_id, input_payload=payload.input, sync=payload.sync, token_profile=payload.token_profile, extra=payload.extra, timeout=payload.timeout)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/vastai/request")
def vastai_request(payload: GenericCloudRequest, request: Request):
    try:
        return ctx(request).cloud.vastai(method=payload.method, path=payload.path, params=payload.params, body=payload.body, token_profile=payload.token_profile, timeout=payload.timeout)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/lambda/request")
def lambda_request(payload: GenericCloudRequest, request: Request):
    try:
        return ctx(request).cloud.lambda_labs(method=payload.method, path=payload.path, params=payload.params, body=payload.body, token_profile=payload.token_profile, timeout=payload.timeout)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

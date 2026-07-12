from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from .deps import ctx
from ..schemas import (
    WorkflowCreateRequest,
    WorkflowPlanRequest,
    WorkflowRefineRequest,
    WorkflowRunRequest,
    WorkflowUpdateRequest,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/catalog")
def catalog(request: Request):
    return ctx(request).workflows.catalog()


@router.get("")
def list_workflows(request: Request):
    return {"items": ctx(request).workflows.list_workflows()}


@router.post("")
def create_workflow(payload: WorkflowCreateRequest, request: Request):
    try:
        return ctx(request).workflows.create_from_request(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def list_runs(request: Request, limit: int = 50):
    return {"items": ctx(request).workflows.list_runs(limit=limit)}


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, request: Request):
    workflow = ctx(request).workflows.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}")
def update_workflow(workflow_id: str, payload: WorkflowUpdateRequest, request: Request):
    try:
        workflow = dict(payload.workflow or {})
        workflow["id"] = workflow_id
        return ctx(request).workflows.save_workflow(workflow)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str, request: Request):
    return ctx(request).workflows.delete_workflow(workflow_id)


@router.post("/plan")
def plan_from_goal(payload: WorkflowPlanRequest, request: Request):
    try:
        return ctx(request).workflows.plan_from_goal(payload, use_model=payload.use_model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/refine")
def refine_workflow(workflow_id: str, payload: WorkflowRefineRequest, request: Request):
    try:
        return ctx(request).workflows.refine_workflow(workflow_id, payload, use_model=payload.use_model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/validate")
def validate_workflow(workflow_id: str, request: Request):
    try:
        workflow = ctx(request).workflows.get_workflow(workflow_id)
        return ctx(request).workflows.validate_workflow(workflow or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/dry-run")
def dry_run_workflow(workflow_id: str, payload: WorkflowRunRequest, request: Request):
    try:
        return ctx(request).workflows.dry_run(workflow_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{workflow_id}/run")
def run_workflow(workflow_id: str, payload: WorkflowRunRequest, request: Request):
    c = ctx(request)
    workflow = c.workflows.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    def task(progress):
        return c.workflows.run_workflow(workflow, payload, progress=progress)

    job_id = c.jobs.submit("automation_workflow", {"workflow_id": workflow_id, **payload.model_dump()}, task)
    return {"ok": True, "job_id": job_id, "workflow_id": workflow_id, "status": "queued"}

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from .deps import ctx
from ..schemas import (
    GraphEditorCreateRequest,
    GraphEditorPlanRequest,
    GraphEditorRefineRequest,
    GraphEditorRunRequest,
    GraphEditorSaveRequest,
)

router = APIRouter(prefix="/graph-editor", tags=["graph-editor"])


@router.get("/catalog")
def catalog(request: Request):
    return ctx(request).graph_editor.catalog()


@router.get("")
def list_graphs(request: Request):
    return {"items": ctx(request).graph_editor.list_graphs()}


@router.post("")
def create_graph(payload: GraphEditorCreateRequest, request: Request):
    try:
        return ctx(request).graph_editor.create_from_template(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def list_runs(request: Request, limit: int = 50):
    return {"items": ctx(request).graph_editor.list_runs(limit=limit)}


@router.post("/templates/self-test")
def self_test_templates(payload: dict | None, request: Request):
    try:
        data = dict(payload or {})
        keys = data.get("template_keys") or data.get("keys")
        if keys is not None and not isinstance(keys, list):
            raise ValueError("template_keys must be a list when provided.")
        return ctx(request).graph_editor.certify_templates(keys)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/plan")
def plan_from_goal(payload: GraphEditorPlanRequest, request: Request):
    try:
        return ctx(request).graph_editor.plan_from_goal(payload, use_model=payload.use_model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/events")
def list_events(request: Request, channel: str | None = None, limit: int = 200):
    return {"items": ctx(request).graph_editor.list_events(channel=channel, limit=limit)}


@router.post("/events")
def publish_event(payload: dict, request: Request):
    return ctx(request).graph_editor.publish_event(payload or {})


@router.delete("/events")
def clear_events(request: Request, channel: str | None = None):
    return ctx(request).graph_editor.clear_events(channel=channel)



@router.post("/execute-session")
def execute_unsaved_session(payload: dict, request: Request):
    try:
        data = dict(payload or {})
        graph = data.get("graph") or data
        run_payload = data.get("payload") or data
        return ctx(request).graph_editor.execute_session(graph, run_payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/execute-node")
def execute_unsaved_node(payload: dict, request: Request):
    try:
        data = dict(payload or {})
        graph = data.get("graph") or {}
        node_id = data.get("node_id") or data.get("id")
        return ctx(request).graph_editor.execute_node(graph, str(node_id or ""), data.get("payload") or data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/events")
def list_events_static_compat(request: Request, channel: str | None = None, limit: int = 200):
    return {"items": ctx(request).graph_editor.list_events(channel=channel, limit=limit)}


@router.post("/events")
def publish_event_static_compat(payload: dict, request: Request):
    return ctx(request).graph_editor.publish_event(payload or {})


@router.delete("/events")
def clear_events_static_compat(request: Request, channel: str | None = None):
    return ctx(request).graph_editor.clear_events(channel=channel)

@router.get("/{graph_id}")
def get_graph(graph_id: str, request: Request):
    graph = ctx(request).graph_editor.get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return graph


@router.put("/{graph_id}")
def update_graph(graph_id: str, payload: GraphEditorSaveRequest, request: Request):
    try:
        graph = dict(payload.graph or {})
        graph["id"] = graph_id
        return ctx(request).graph_editor.save_graph(graph)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{graph_id}")
def delete_graph(graph_id: str, request: Request):
    return ctx(request).graph_editor.delete_graph(graph_id)


@router.post("/{graph_id}/refine")
def refine_graph(graph_id: str, payload: GraphEditorRefineRequest, request: Request):
    try:
        return ctx(request).graph_editor.refine_graph(graph_id, payload, use_model=payload.use_model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/validate")
def validate_graph(graph_id: str, request: Request):
    try:
        return ctx(request).graph_editor.validate_graph(graph_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/to-workflow")
def graph_to_workflow(graph_id: str, request: Request):
    try:
        return {"ok": True, "workflow": ctx(request).graph_editor.to_workflow(graph_id)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/save-as-workflow")
def save_as_workflow(graph_id: str, payload: GraphEditorRunRequest, request: Request):
    try:
        return ctx(request).graph_editor.save_as_workflow(graph_id, workflow_id=payload.workflow_id or None)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/dry-run")
def dry_run(graph_id: str, payload: GraphEditorRunRequest, request: Request):
    try:
        return ctx(request).graph_editor.dry_run(graph_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/run")
def run_graph(graph_id: str, payload: GraphEditorRunRequest, request: Request):
    try:
        return ctx(request).graph_editor.run_as_job(graph_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/simulate")
def simulate_graph(graph_id: str, payload: GraphEditorRunRequest, request: Request):
    try:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        return ctx(request).graph_editor.simulate(graph_id, data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-workflow/{workflow_id}")
def import_workflow(workflow_id: str, request: Request):
    try:
        return ctx(request).graph_editor.import_workflow(workflow_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/execute-session")
def execute_saved_session(graph_id: str, payload: dict, request: Request):
    try:
        return ctx(request).graph_editor.execute_session(graph_id, dict(payload or {}))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/execute-node/{node_id}")
def execute_saved_node(graph_id: str, node_id: str, payload: dict, request: Request):
    try:
        return ctx(request).graph_editor.execute_node(graph_id, node_id, dict(payload or {}))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

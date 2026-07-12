from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..schemas import GraphEditorCreateRequest, GraphEditorPlanRequest, GraphEditorRefineRequest, GraphEditorRunRequest, GraphEditorSaveRequest

router = APIRouter(prefix="/graphs", tags=["agentic-graphs-compat"])


def ctx(request: Request):
    return request.app.state.context


def _service(request: Request):
    return ctx(request).graph_editor


def _legacy_catalog(catalog: dict):
    """Expose aliases matching the older standalone graph editor contract.

    The current GUI uses /api/graph-editor, but keeping /api/graphs available
    makes the feature friendlier to older local tools, saved scripts, and the
    earlier E3-style frontend shape.
    """
    node_palette = catalog.get("node_palette") or []
    return {
        **catalog,
        "node_catalog": node_palette,
        "templates": catalog.get("workflow_templates") or [],
        "execution_backend": "automation_workflows",
        "compatibility": "e3_graph_editor_style_routes",
    }


@router.get("/catalog")
def catalog(request: Request):
    return _legacy_catalog(_service(request).catalog())


@router.get("")
def list_graphs(request: Request):
    items = _service(request).list_graphs()
    return {"items": items, "count": len(items)}


@router.post("")
def create_graph(payload: GraphEditorCreateRequest, request: Request):
    try:
        return _service(request).create_from_template(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def list_runs(request: Request):
    items = _service(request).list_runs()
    return {"items": items, "count": len(items)}


@router.post("/plan")
def plan_graph(payload: GraphEditorPlanRequest, request: Request):
    try:
        return _service(request).plan_from_goal(payload, use_model=payload.use_model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/from-workflow/{workflow_id}")
def from_workflow(workflow_id: str, request: Request):
    try:
        return _service(request).import_workflow(workflow_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/events")
def list_events(request: Request, channel: str | None = None, limit: int = 200):
    return {"items": _service(request).list_events(channel=channel, limit=limit)}


@router.post("/events")
def publish_event(payload: dict, request: Request):
    return _service(request).publish_event(payload or {})


@router.delete("/events")
def clear_events(request: Request, channel: str | None = None):
    return _service(request).clear_events(channel=channel)



@router.post("/execute-session")
def execute_unsaved_session(payload: dict, request: Request):
    try:
        data = dict(payload or {})
        graph = data.get("graph") or data
        run_payload = data.get("payload") or data
        return _service(request).execute_session(graph, run_payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/execute-node")
def execute_unsaved_node(payload: dict, request: Request):
    try:
        data = dict(payload or {})
        return _service(request).execute_node(data.get("graph") or {}, str(data.get("node_id") or ""), data.get("payload") or data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/events")
def list_events_static_compat(request: Request, channel: str | None = None, limit: int = 200):
    return {"items": _service(request).list_events(channel=channel, limit=limit)}


@router.post("/events")
def publish_event_static_compat(payload: dict, request: Request):
    return _service(request).publish_event(payload or {})


@router.delete("/events")
def clear_events_static_compat(request: Request, channel: str | None = None):
    return _service(request).clear_events(channel=channel)

@router.get("/{graph_id}")
def get_graph(graph_id: str, request: Request):
    graph = _service(request).get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return graph


@router.put("/{graph_id}")
def update_graph(graph_id: str, payload: GraphEditorSaveRequest, request: Request):
    try:
        graph = dict(payload.graph or {})
        graph["id"] = graph_id
        return _service(request).save_graph(graph)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{graph_id}")
def delete_graph(graph_id: str, request: Request):
    return _service(request).delete_graph(graph_id)


@router.post("/{graph_id}/validate")
def validate_graph(graph_id: str, request: Request):
    try:
        return _service(request).validate_graph(graph_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/compile")
def compile_graph(graph_id: str, request: Request, payload: GraphEditorRunRequest | None = None):
    try:
        workflow = _service(request).to_workflow(graph_id)
        saved = None
        if payload and payload.save_compiled_workflow:
            saved = _service(request).save_as_workflow(graph_id, workflow_id=payload.workflow_id or None)
        return {"ok": True, "workflow": workflow, "saved": saved}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/dry-run")
def dry_run_graph(graph_id: str, request: Request, payload: GraphEditorRunRequest | None = None):
    try:
        return _service(request).dry_run(graph_id, payload or GraphEditorRunRequest(dry_run=True))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/run")
def run_graph(graph_id: str, request: Request, payload: GraphEditorRunRequest | None = None):
    try:
        return _service(request).run_as_job(graph_id, payload or GraphEditorRunRequest())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/refine")
def refine_graph(graph_id: str, payload: GraphEditorRefineRequest, request: Request):
    try:
        return _service(request).refine_graph(graph_id, payload, use_model=payload.use_model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/simulate")
def simulate_graph(graph_id: str, request: Request, payload: GraphEditorRunRequest | None = None):
    try:
        data = payload.model_dump() if payload and hasattr(payload, "model_dump") else (dict(payload or {}) if payload else {})
        return _service(request).simulate(graph_id, data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/execute-session")
def execute_session(graph_id: str, request: Request, payload: dict | None = None):
    try:
        return _service(request).execute_session(graph_id, payload or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{graph_id}/execute-node/{node_id}")
def execute_node(graph_id: str, node_id: str, request: Request, payload: dict | None = None):
    try:
        return _service(request).execute_node(graph_id, node_id, payload or {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

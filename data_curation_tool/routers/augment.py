from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException

from .deps import ctx
from ..schemas import AugmentRequest, ExportRequest, ExternalImageToolRequest, ExternalAppDiscoveryRequest
from ..services.external_app_service import APP_SPECS

router = APIRouter(prefix="/augment", tags=["augment"])


@router.post("/run")
def run_augment(payload: AugmentRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.augment.run(payload, progress)

    job_id = c.jobs.submit("augmentation", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}


@router.get("/external-tools")
def list_external_tools(request: Request, refresh: bool = False, deep_scan: bool = False):
    return ctx(request).external_apps.discover_all(refresh=refresh, deep_scan=deep_scan, save=False)


@router.post("/external-tools/discover")
def discover_external_tools(payload: ExternalAppDiscoveryRequest, request: Request):
    service = ctx(request).external_apps
    keys = payload.tool_names or list(APP_SPECS)
    return {
        "tools": [service.discover(key, refresh=payload.refresh, deep_scan=payload.deep_scan, save=payload.save_discovered_paths) for key in keys],
        "home": str(__import__("pathlib").Path.home()),
        "deep_scan": payload.deep_scan,
    }


@router.post("/external-tool/launch-now")
def launch_external_tool_now(payload: ExternalImageToolRequest, request: Request):
    # Interactive app errors must be returned immediately instead of being hidden
    # in the Jobs tab.
    try:
        return ctx(request).external_apps.launch(payload)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"The application could not be launched: {exc}") from exc


@router.post("/external-tool")
def run_external_tool(payload: ExternalImageToolRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.augment.run_external_tool(payload, progress)

    job_id = c.jobs.submit("external_image_tool", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}


@router.post("/export")
def run_export(payload: ExportRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.exports.run(payload, progress)

    job_id = c.jobs.submit("export", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}

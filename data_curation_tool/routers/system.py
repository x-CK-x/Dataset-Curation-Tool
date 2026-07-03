from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException

from .deps import ctx
from ..schemas import FolderPickRequest, FilePickRequest, OpenLocalPathRequest
from ..services.dialog_service import pick_folder, pick_file
from ..services.gpu_service import detect_devices

router = APIRouter(tags=["system"])


@router.get("/system/devices")
def devices(request: Request):
    return detect_devices()


@router.post("/system/pick-folder")
def pick_dataset_folder(payload: FolderPickRequest, request: Request):
    return pick_folder(payload.title, payload.initial_dir)


@router.post("/system/pick-file")
def pick_local_file(payload: FilePickRequest, request: Request):
    return pick_file(payload.title, payload.initial_dir, payload.filetypes or None)


@router.post("/system/open-path")
def open_local_path(payload: OpenLocalPathRequest, request: Request):
    path = Path(payload.path).expanduser()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path does not exist: {path}")
    try:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not open local path: {exc}") from exc
    return {"ok": True, "path": str(path.resolve())}




@router.post("/system/restart")
def restart_application(request: Request):
    """Best-effort self-restart for settings that are intentionally startup-applied.

    The normal run scripts still remain the most reliable restart path.  This
    endpoint exists for the red "apply on restart" button in the Settings UI and
    uses the current Python executable/module with the active runtime/model/output
    folders and host/port settings.
    """
    c = ctx(request)
    python = sys.executable or "python"
    host = str(getattr(c.settings, "host", "127.0.0.1") or "127.0.0.1")
    port = str(getattr(c.settings, "port", 7865) or 7865)
    base_cmd = [python, "-m", "data_curation_tool", "--host", host, "--port", port, "--runtime", str(c.paths.runtime), "--models", str(c.paths.models), "--outputs", str(c.paths.outputs), "--open-browser"]

    def relaunch_and_exit() -> None:
        time.sleep(0.75)
        try:
            if os.name == "nt":
                quoted = " ".join(subprocess.list2cmdline([arg]) for arg in base_cmd)
                subprocess.Popen(["cmd", "/c", f"timeout /t 2 /nobreak > nul & {quoted}"], cwd=str(c.paths.root), close_fds=True)
            else:
                subprocess.Popen(["sh", "-c", "sleep 2; exec \"$@\"", "dct-restart", *base_cmd], cwd=str(c.paths.root), close_fds=True)
        finally:
            os._exit(0)

    threading.Thread(target=relaunch_and_exit, daemon=True).start()
    return {"ok": True, "message": "Restart requested. The browser may briefly disconnect while the local app relaunches."}


@router.get("/system/summary")
def summary(request: Request):
    c = ctx(request)
    datasets = c.db.query_one("SELECT COUNT(*) AS c FROM datasets")["c"]
    media = c.db.query_one("SELECT COUNT(*) AS c FROM media WHERE active=1")["c"]
    tags = c.db.query_one("SELECT COUNT(*) AS c FROM tags")["c"]
    duplicates = c.db.query_one("SELECT COUNT(*) AS c FROM duplicates")["c"]
    jobs = c.db.query_one("SELECT COUNT(*) AS c FROM jobs")["c"]
    return {"datasets": datasets, "media": media, "tags": tags, "duplicates": duplicates, "jobs": jobs}


@router.get("/system/feature-audit")
def feature_audit(request: Request):
    c = ctx(request)
    models = c.models.list_models()
    model_names = {m["name"] for m in models}
    downloader_sources = [s["key"] for s in c.downloads.validate_source_configurations()["sources"]]
    return {
        "version": getattr(__import__("data_curation_tool"), "__version__", "unknown"),
        "feature_groups": [
            "fast tag dictionaries/autocomplete/category colors",
            "txt/json/embedded metadata import",
            "metadata schema picker/concatenator",
            "gallery/tag editor/compare/batch tag workflows",
            "assistant/chat/orchestration with local/cloud models",
            "reference finder/source browser/geckodriver",
            "separate detection/bbox and segmentation/mask workflows",
            "persistent editable spatial layers, revision history, box/mask composition, and advanced manual mask tools",
            "pose2d/pose3d/animation tools",
            "FlexAvatar single-image/few-shot/monocular complete 3D head avatars with isolated runtime, fitting, animation, and research training bundles",
            "Topaz/Krita/ComfyUI home-directory discovery and handoff",
            "Krita and Blender bridge hooks",
            "video frame extraction/audio extraction/recording",
            "booru/json downloader with pacing/concurrency",
            "model download/load/unload/device placement",
            "previous-install asset migration for models and tag exports",
        ],
        "redrocket_models_present": {
            "redrocket-jtp-3": "redrocket-jtp-3" in model_names,
            "redrocket-e6-visual-ratings": "redrocket-e6-visual-ratings" in model_names,
        },
        "flexavatar_present": "flexavatar-flex-1" in model_names and bool(getattr(c, "flexavatar", None)),
        "download_sources": downloader_sources,
        "model_count": len(models),
    }

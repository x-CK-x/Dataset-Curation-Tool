from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import DatasetCreate, DatasetImportMany

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("")
def list_datasets(request: Request):
    return [item.model_dump() for item in ctx(request).datasets.list()]


@router.post("/import")
def import_dataset(payload: DatasetCreate, request: Request):
    c = ctx(request)

    def task(progress):
        return c.datasets.import_folder(payload, progress=progress)

    job_id = c.jobs.submit("dataset_import", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}


@router.post("/import-many")
def import_many(payload: DatasetImportMany, request: Request):
    c = ctx(request)

    def task(progress):
        results = []
        total = max(len(payload.folders), 1)
        for idx, folder in enumerate(payload.folders, start=1):
            def subprogress(frac, msg, base=idx - 1):
                progress((base + frac) / total, f"Folder {idx}/{total}: {msg}")
            results.append(c.datasets.import_folder(folder, progress=subprogress))
        return {"folders": len(payload.folders), "results": results}

    job_id = c.jobs.submit("dataset_import_many", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}

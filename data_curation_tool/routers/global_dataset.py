from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import (
    GlobalAssetRegisterRequest,
    GlobalAssetSearchRequest,
    GlobalBranchCreateRequest,
    GlobalBranchLinkRequest,
    GlobalDatasetSettingsUpdate,
    GlobalFolderIngestRequest,
    GlobalVariantRegisterRequest,
)

router = APIRouter(prefix="/global-dataset", tags=["global-dataset"])


@router.get("/status")
def status(request: Request):
    return ctx(request).global_dataset.status()


@router.put("/settings")
def update_settings(payload: GlobalDatasetSettingsUpdate, request: Request):
    return ctx(request).global_dataset.update_settings(payload)


@router.get("/assets")
def assets(request: Request, q: str = "", source_site: str | None = None, tags: str = "", page: int = 1, page_size: int = 80):
    tag_list = [x.strip() for x in (tags or "").split(",") if x.strip()]
    return ctx(request).global_dataset.search_assets(q=q, source_site=source_site, tags=tag_list, page=page, page_size=page_size)


@router.post("/assets/search")
def search_assets(payload: GlobalAssetSearchRequest, request: Request):
    return ctx(request).global_dataset.search_assets(q=payload.q, source_site=payload.source_site, tags=payload.tags, page=payload.page, page_size=payload.page_size)


@router.get("/assets/{asset_id}")
def asset_detail(asset_id: int, request: Request):
    return ctx(request).global_dataset.asset_detail(asset_id)


@router.post("/register-file")
def register_file(payload: GlobalAssetRegisterRequest, request: Request):
    return ctx(request).global_dataset.register_file(
        payload.path,
        source=payload.source,
        source_site=payload.source_site,
        source_post_id=payload.source_post_id,
        source_url=payload.source_url,
        tags=payload.tags,
        caption=payload.caption,
        metadata=payload.metadata,
        copy_to_store=payload.copy_to_store,
    )


@router.post("/ingest-folder")
def ingest_folder(payload: GlobalFolderIngestRequest, request: Request):
    c = ctx(request)

    def task(progress):
        return c.global_dataset.ingest_folder(payload, progress=progress)

    job_id = c.jobs.submit("global_dataset_ingest", payload.model_dump(), task)
    return {"job_id": job_id, "status": "queued"}


@router.get("/branches")
def branches(request: Request):
    return ctx(request).global_dataset.branches()


@router.post("/branches")
def create_branch(payload: GlobalBranchCreateRequest, request: Request):
    return ctx(request).global_dataset.ensure_branch(payload.name, purpose=payload.purpose, root_path=payload.root_path, settings=payload.settings)


@router.get("/branches/{branch_id}/items")
def branch_items(branch_id: int, request: Request):
    return ctx(request).global_dataset.branch_items(branch_id)


@router.get("/branch-references")
def branch_references(request: Request, asset_id: int | None = None, branch_id: int | None = None, limit: int = 500):
    return ctx(request).global_dataset.branch_references(asset_id=asset_id, branch_id=branch_id, limit=limit)


@router.post("/branches/link")
def link_branch_assets(payload: GlobalBranchLinkRequest, request: Request):
    return ctx(request).global_dataset.link_assets(
        branch_id=payload.branch_id,
        branch_name=payload.branch_name,
        asset_ids=payload.asset_ids,
        media_ids=payload.media_ids,
        copy_sidecars=payload.copy_sidecars,
        include=payload.include,
        note=payload.note,
    )


@router.post("/variants")
def register_variant(payload: GlobalVariantRegisterRequest, request: Request):
    return ctx(request).global_dataset.register_variant(
        global_asset_id=payload.global_asset_id,
        branch_id=payload.branch_id,
        branch_name=payload.branch_name,
        variant_path=payload.variant_path,
        variant_kind=payload.variant_kind,
        transform=payload.transform,
        tags=payload.tags,
        caption=payload.caption,
        copy_to_branch=payload.copy_to_branch,
    )

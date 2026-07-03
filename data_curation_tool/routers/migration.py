from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import AssetMigrationRequest, AssetMigrationSettingsRequest

router = APIRouter(prefix="/migration", tags=["migration"])


@router.get("/defaults")
def migration_defaults(request: Request):
    c = ctx(request)
    return {
        "source_paths": list(getattr(c.settings, "previous_install_paths", []) or []),
        "migrate_on_startup": bool(getattr(c.settings, "migrate_assets_on_startup", False)),
        "include": getattr(c.settings, "migration_include_assets", {}) or {},
        "mode": getattr(c.settings, "migration_mode", "copy") or "copy",
        "conflict": getattr(c.settings, "migration_conflict_policy", "skip_existing") or "skip_existing",
        "newest_first": bool(getattr(c.settings, "migration_newest_first", True)),
        "delete_source_duplicates": bool(getattr(c.settings, "migration_delete_source_duplicates", False)),
        "current_root": str(c.paths.root),
        "current_models": str(c.paths.models),
        "current_runtime": str(c.paths.runtime),
    }


@router.post("/scan")
def scan_migration_sources(payload: AssetMigrationRequest, request: Request):
    c = ctx(request)
    return c.migration.scan(payload.source_paths, include=payload.include, newest_first=payload.newest_first)


@router.post("/run")
def run_migration(payload: AssetMigrationRequest, request: Request):
    c = ctx(request)
    params = payload.model_dump()

    def task(progress):
        result = c.migration.migrate(
            payload.source_paths,
            include=payload.include,
            mode=payload.mode,
            conflict=payload.conflict,
            dry_run=payload.dry_run,
            newest_first=payload.newest_first,
            delete_source_duplicates=payload.delete_source_duplicates,
            progress=progress,
        )
        if not payload.dry_run:
            try:
                c.registry.register_custom_models(getattr(c.settings, "custom_models", []) or [])
                c.registry.load_custom_models(c.paths.runtime / "custom_models.json")
                c.settings.save(c.paths.settings)
                result["custom_model_catalog_reloaded"] = True
            except Exception as exc:
                result["custom_model_catalog_reload_error"] = str(exc)
            try:
                result["model_reconciliation"] = c.models.reconcile_local_assets()
            except Exception as exc:
                result["model_reconciliation_error"] = str(exc)
            try:
                result["tag_dictionary_status"] = c.tags.dictionary_status()
            except Exception as exc:
                result["tag_dictionary_status_error"] = str(exc)
        return result

    job_id = c.jobs.submit("asset_migration", params, task)
    return {"job_id": job_id, "dry_run": payload.dry_run}


@router.put("/startup-settings")
def save_migration_startup_settings(payload: AssetMigrationSettingsRequest, request: Request):
    c = ctx(request)
    values = {
        "previous_install_paths": payload.source_paths,
        "migrate_assets_on_startup": payload.migrate_on_startup,
        "migration_include_assets": payload.include,
        "migration_mode": payload.mode,
        "migration_conflict_policy": payload.conflict,
        "migration_newest_first": payload.newest_first,
        "migration_delete_source_duplicates": payload.delete_source_duplicates,
    }
    for key, value in values.items():
        setattr(c.settings, key, value)
        c.db.set_setting(key, value)
    c.settings.save(c.paths.settings)
    return {"ok": True, **values}

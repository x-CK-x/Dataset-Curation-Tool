from __future__ import annotations

import time

from fastapi import APIRouter, Request

from .deps import ctx
from .. import __version__
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
        "skip_internet_refresh": bool(getattr(c.settings, "migration_skip_post_online_tag_sync", True)),
        "parallel_file_transfers": bool(getattr(c.settings, "migration_parallel_file_transfers", True)),
        "file_transfer_workers": int(getattr(c.settings, "migration_file_transfer_workers", 4) or 4),
        "fast_same_volume_moves": bool(getattr(c.settings, "migration_fast_same_volume_moves", True)),
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
    startup_progress = getattr(c, "startup_progress", None)
    mirror_startup = bool(startup_progress is not None and not payload.dry_run)

    if mirror_startup:
        try:
            # Manual migration queued; startup maintenance will resume.
            startup_progress.start("Migration-triggered maintenance started: manual migration queued", phase="startup_migration", job_type="asset_migration", trigger="manual_migration")
            startup_progress.update(0.01, "Migration-triggered maintenance started: waiting for migration worker", phase="startup_migration", job_type="asset_migration", trigger="manual_migration")
        except Exception:
            pass

    def task(progress, job_id: int | None = None):
        started = time.monotonic()
        if mirror_startup:
            try:
                startup_progress.attach_job(job_id, "asset_migration", trigger="manual_migration", message=f"Migration job #{job_id} started" if job_id else "Migration job started")
                startup_progress.update(0.02, "Preparing migration/reconciliation", phase="startup_migration", job_id=job_id, job_type="asset_migration", trigger="manual_migration")
            except Exception:
                pass

        def mirrored_progress(value: float, message: str = ""):
            try:
                local = max(0.0, min(1.0, float(value or 0.0)))
            except Exception:
                local = 0.0
            # Keep the Jobs row close to the real migration progress.  Older
            # builds compressed raw file migration into only the first 75%, which
            # made long model moves look stuck around 70% even when 95%+ of the
            # bytes were already handled.  Reserve only the final 10% for
            # reconciliation/finalization so the visible progress matches the
            # slow step the user is watching.
            overall = 0.02 + 0.88 * local
            visible_message = message or "Migrating assets"
            if mirror_startup:
                try:
                    startup_progress.update(overall, visible_message, phase="startup_migration")
                except Exception:
                    pass
            progress(overall, visible_message)

        try:
            result = c.migration.migrate(
                payload.source_paths,
                include=payload.include,
                mode=payload.mode,
                conflict=payload.conflict,
                dry_run=payload.dry_run,
                newest_first=payload.newest_first,
                delete_source_duplicates=payload.delete_source_duplicates,
                progress=mirrored_progress if mirror_startup else progress,
                parallel_file_transfers=payload.parallel_file_transfers,
                file_transfer_workers=payload.file_transfer_workers,
                fast_same_volume_moves=payload.fast_same_volume_moves,
            )
            if not payload.dry_run:
                include_models = bool((payload.include or {}).get("models", True))
                include_custom_models = bool((payload.include or {}).get("custom_models", True))
                include_tag_assets = bool((payload.include or {}).get("tag_exports", True) or (payload.include or {}).get("tag_database", True))
                try:
                    if include_custom_models:
                        progress(0.91, "Reloading migrated custom model catalog")
                        if mirror_startup:
                            startup_progress.update(0.91, "Reloading migrated custom model catalog", phase="startup_migration")
                        c.registry.register_custom_models(getattr(c.settings, "custom_models", []) or [])
                        c.registry.load_custom_models(c.paths.runtime / "custom_models.json")
                        c.settings.save(c.paths.settings)
                        result["custom_model_catalog_reloaded"] = True
                    else:
                        progress(0.91, "Skipping custom model catalog reload; custom models were not included")
                        result["custom_model_catalog_reloaded"] = "skipped"
                except Exception as exc:
                    result["custom_model_catalog_reload_error"] = str(exc)
                try:
                    if include_models:
                        progress(0.93, "Reconciling migrated model assets")
                        if mirror_startup:
                            startup_progress.update(0.93, "Reconciling migrated model assets", phase="startup_migration")
                        c.models.invalidate_model_catalog_cache()
                        result["model_reconciliation"] = c.models.reconcile_local_assets()
                        c.models.invalidate_model_catalog_cache()
                    else:
                        progress(0.93, "Skipping model asset reconciliation; models were not included")
                        result["model_reconciliation"] = "skipped"
                except Exception as exc:
                    result["model_reconciliation_error"] = str(exc)
                try:
                    profile_key = getattr(c.settings, "default_tag_profile", "e621") or "e621"
                    if include_tag_assets:
                        progress(0.95, f"Reconciling migrated {profile_key} tag-export cache")
                        if mirror_startup:
                            startup_progress.update(0.95, f"Reconciling migrated {profile_key} tag-export cache", phase="startup_migration")
                        # Keep the finalization phase fast.  A full multi-profile
                        # scan can be very slow after migration; reconcile the active
                        # profile here and let users sync other booru profiles on
                        # demand from Tag Dictionaries.
                        result["tag_export_reconciliation"] = c.tags.reconcile_export_cache(profile_key)
                    else:
                        progress(0.95, f"Skipping {profile_key} tag-export reconciliation; tag assets were not included")
                        result["tag_export_reconciliation"] = "skipped"
                    progress(0.96, f"Checking {profile_key} tag dictionary status")
                    result["tag_dictionary_status"] = c.tags.dictionary_status(profile_key)
                    result["tag_dictionary_profile"] = profile_key
                    local_only = bool(getattr(payload, "skip_internet_refresh", True) or getattr(c.settings, "migration_skip_post_online_tag_sync", True))
                    if local_only:
                        progress(0.97, f"Importing/reusing cached {profile_key} tag exports without internet")
                        if mirror_startup:
                            startup_progress.update(0.97, f"Importing/reusing cached {profile_key} tag exports without internet", phase="startup_migration")
                        cached_result = None
                        try:
                            status_total = int((result.get("tag_dictionary_status") or {}).get("total") or 0) if isinstance(result.get("tag_dictionary_status"), dict) else 0
                        except Exception:
                            status_total = 0
                        tag_status = result.get("tag_dictionary_status") if isinstance(result.get("tag_dictionary_status"), dict) else {}
                        if include_tag_assets and (status_total <= 0 or bool(tag_status.get("incomplete"))):
                            def cached_progress(value: float, message: str = ""):
                                try:
                                    local = max(0.0, min(1.0, float(value or 0.0)))
                                except Exception:
                                    local = 0.0
                                overall = 0.97 + 0.02 * local
                                if mirror_startup:
                                    try:
                                        startup_progress.update(overall, message or "Importing cached tag exports", phase="startup_migration")
                                    except Exception:
                                        pass
                                progress(overall, message or "Importing cached tag exports")
                            cached_result = c.tags.import_cached_exports(profile_key, replace_existing=True, progress=cached_progress)
                            result["tag_dictionary_cached_import"] = cached_result
                            result["tag_dictionary_status"] = c.tags.dictionary_status(profile_key)
                        result["tag_dictionary_post_migration_sync"] = "skipped; local-only migration mode reused migrated tag exports/database rows and did not use the network"
                    elif getattr(c.settings, "auto_sync_tag_db_on_startup", True) and c.tags.should_auto_sync_default_export(
                        profile_key,
                        empty_only=bool(getattr(c.settings, "tag_db_sync_if_empty_only", True)),
                        cache_hours=int(getattr(c.settings, "tag_db_export_cache_hours", 168) or 168),
                    ):
                        progress(0.97, f"Synchronizing {profile_key} tag dictionary after migration")
                        if mirror_startup:
                            startup_progress.update(0.97, f"Synchronizing {profile_key} tag dictionary after migration", phase="startup_migration")

                        def tag_progress(value: float, message: str = ""):
                            try:
                                local = max(0.0, min(1.0, float(value or 0.0)))
                            except Exception:
                                local = 0.0
                            overall = 0.97 + 0.02 * local
                            if mirror_startup:
                                try:
                                    startup_progress.update(overall, message or "Post-migration tag dictionary sync", phase="startup_migration")
                                except Exception:
                                    pass
                            progress(overall, message or "Post-migration tag dictionary sync")

                        result["tag_dictionary_post_migration_sync"] = c.tags.import_default_exports(
                            profile_key=profile_key,
                            user_agent=getattr(c.settings, "downloader_user_agent", None) or f"DataCurationTool/{__version__}",
                            cache_hours=int(getattr(c.settings, "tag_db_export_cache_hours", 168) or 168),
                            progress=tag_progress,
                            replace_existing=True,
                        )
                    else:
                        result["tag_dictionary_post_migration_sync"] = "skipped; cache already fresh, recently checked, or disabled"
                except Exception as exc:
                    result["tag_dictionary_status_error"] = str(exc)
                progress(1.0, "Migration-triggered maintenance complete")
                if mirror_startup:
                    elapsed = round(time.monotonic() - started, 3)
                    try:
                        startup_progress.update(0.995, "Finalizing compact migration result and releasing UI refresh", phase="startup_migration")
                        startup_progress.complete(f"Migration-triggered maintenance complete in {elapsed}s")
                    except Exception:
                        pass
            return result
        except Exception as exc:
            if mirror_startup:
                try:
                    startup_progress.fail(exc, "Migration-triggered maintenance stopped")
                except Exception:
                    pass
            raise

    job_id = c.jobs.submit_with_job_id("asset_migration", params, task)
    if mirror_startup:
        try:
            startup_progress.attach_job(job_id, "asset_migration", trigger="manual_migration", message=f"Migration job #{job_id} queued")
            startup_progress.update(0.015, f"Migration job #{job_id} queued", phase="startup_migration", job_id=job_id, job_type="asset_migration", trigger="manual_migration")
        except Exception:
            pass
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
        "migration_skip_post_online_tag_sync": payload.skip_internet_refresh,
        "migration_local_only_existing_assets": payload.skip_internet_refresh,
        "migration_parallel_file_transfers": payload.parallel_file_transfers,
        "migration_file_transfer_workers": payload.file_transfer_workers,
        "migration_fast_same_volume_moves": payload.fast_same_volume_moves,
    }
    for key, value in values.items():
        setattr(c.settings, key, value)
        c.db.set_setting(key, value)
    c.settings.save(c.paths.settings)
    return {"ok": True, **values}

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
if os.environ.get("DCT_CUDA_VISIBLE_DEVICES"):
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["DCT_CUDA_VISIBLE_DEVICES"]
elif os.environ.get("DCT_CLEAR_CUDA_VISIBLE_DEVICES", "1") != "0":
    # Clear accidental global GPU masking before torch is imported anywhere.
    # Set DCT_CUDA_VISIBLE_DEVICES=0,1 to intentionally restrict devices, or
    # DCT_CLEAR_CUDA_VISIBLE_DEVICES=0 to preserve a pre-set mask.
    os.environ.pop("CUDA_VISIBLE_DEVICES", None)

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import AppSettings
from .context import AppContext
from .database import Database
from .jobs import JobManager
from .models.registry import ModelRegistry
from .paths import AppPaths
from .routers import augment, database, datasets, distributed, downloads, export, jobs, krita, media, media_tools, metadata, models, orchestration, presets, settings, system, tags, voice, reference, browser, blender, spatial, three_d, flexavatar, comfy_bridge, migration, code_assistant, cloud, agent_tools, mcp_tools
from .services.augmentation_service import AugmentationService
from .services.dataset_service import DatasetService
from .services.distributed_service import DistributedService
from .services.downloader_service import DownloaderService
from .services.export_service import ExportService
from .services.metadata_service import MetadataService
from .services.media_service import MediaService
from .services.krita_service import KritaService
from .services.model_service import ModelService
from .services.orchestration_service import OrchestrationService
from .services.preset_service import PresetService
from .services.tag_service import TagService
from .services.video_service import VideoService
from .services.voice_service import VoiceService
from .services.reference_service import ReferenceService
from .services.browser_service import BrowserService
from .services.external_app_service import ExternalAppService
from .services.three_d_service import ThreeDService
from .services.flexavatar_service import FlexAvatarService
from .services.comfy_bridge_service import ComfyBridgeService
from .services.install_migration_service import InstallMigrationService
from .services.code_assistant_service import CodeAssistantService
from .services.cloud_provider_service import CloudProviderService
from .services.agent_tools_service import AgentToolsService
from .services.mcp_tools_service import MCPToolsService
from .schemas import ModelLoadRequest
from .utils import set_tag_text_mode


def build_context(paths: AppPaths) -> AppContext:
    app_settings = AppSettings.load(paths.settings)
    set_tag_text_mode(getattr(app_settings, "tag_text_mode", "underscores"))
    if not app_settings.model_cache_dir:
        app_settings.model_cache_dir = str(paths.models / "hf")
        app_settings.save(paths.settings)
    db = Database(paths.database)
    tag_service = TagService(db, paths, separator=app_settings.tag_separator)
    media_service = MediaService(db, paths)
    metadata_service = MetadataService(db, paths, media_service, tag_service)
    dataset_service = DatasetService(
        db,
        media_service,
        tag_service,
        app_settings.duplicate_hamming_threshold,
        import_workers=app_settings.import_worker_count,
        user_agent=app_settings.downloader_user_agent,
        tag_db_cache_hours=app_settings.tag_db_export_cache_hours,
        metadata_service=metadata_service,
        metadata_extract_on_import=getattr(app_settings, "metadata_extract_on_import", False),
        metadata_apply_when_no_sidecar=getattr(app_settings, "metadata_apply_when_no_sidecar", True),
        metadata_tag_source=getattr(app_settings, "metadata_default_tag_source", "positive_prompt"),
        metadata_caption_source=getattr(app_settings, "metadata_default_caption_source", "positive_prompt"),
    )
    if hasattr(dataset_service, "set_metadata_service"):
        dataset_service.set_metadata_service(metadata_service)
    registry = ModelRegistry(paths.models)
    registry.set_external_model_roots(getattr(app_settings, "external_model_roots", []) or [])
    custom_rows = list(getattr(app_settings, "custom_models", []) or [])
    runtime_custom_catalog = paths.runtime / "custom_models.json"
    if runtime_custom_catalog.exists():
        try:
            import json
            payload = json.loads(runtime_custom_catalog.read_text(encoding="utf-8"))
            runtime_rows = payload.get("models") if isinstance(payload, dict) else payload
            if isinstance(runtime_rows, list):
                seen = {str((r or {}).get("name") or (r or {}).get("repo_id") or (r or {}).get("local_path") or "").lower() for r in custom_rows if isinstance(r, dict)}
                for row in runtime_rows:
                    if not isinstance(row, dict):
                        continue
                    key = str(row.get("name") or row.get("repo_id") or row.get("local_path") or "").lower()
                    if key and key not in seen:
                        seen.add(key)
                        custom_rows.append(row)
        except Exception:
            pass
    registry.register_custom_models(custom_rows)
    if custom_rows != list(getattr(app_settings, "custom_models", []) or []):
        app_settings.custom_models = custom_rows
        app_settings.save(paths.settings)
    model_service = ModelService(db, registry, media_service, tag_service, app_settings)
    model_service.metadata_service = metadata_service
    browser_service = BrowserService(paths)
    preset_service = PresetService(db, paths.presets)
    external_app_service = ExternalAppService(db, paths, app_settings, media_service)
    return AppContext(
        paths=paths,
        settings=app_settings,
        db=db,
        jobs=JobManager(db, max_workers=max(1, int(app_settings.max_concurrent_jobs or app_settings.backend_worker_count or 1))),
        registry=registry,
        media=media_service,
        metadata=metadata_service,
        tags=tag_service,
        datasets=dataset_service,
        models=model_service,
        augment=AugmentationService(db, media_service, external_app_service),
        exports=ExportService(db, media_service),
        presets=preset_service,
        downloads=DownloaderService(db, preset_service, app_settings.downloader_user_agent, tag_service),
        distributed=DistributedService(),
        voice=VoiceService(paths, app_settings, registry),
        video=VideoService(db, media_service, paths.outputs),
        krita=KritaService(db, paths, media_service, tag_service),
        orchestration=OrchestrationService(db, media_service, tag_service, model_service, registry),
        reference=(reference_service := ReferenceService(db, paths, media_service, tag_service, model_service)),
        browser=browser_service,
        external_apps=external_app_service,
        three_d=ThreeDService(paths, media_service, reference_service),
        flexavatar=FlexAvatarService(paths, media_service, app_settings),
        comfy=ComfyBridgeService(paths, media_service, metadata_service, tag_service),
        migration=InstallMigrationService(paths, db, tag_service, app_settings),
        code=CodeAssistantService(model_service),
        cloud=CloudProviderService(app_settings),
        agent_tools=AgentToolsService(paths, app_settings, model_service, browser=browser_service),
        mcp_tools=MCPToolsService(paths, app_settings),
    )


def create_app(paths: AppPaths | None = None) -> FastAPI:
    paths = paths or AppPaths.create()
    context = build_context(paths)
    app = FastAPI(title="Data Curation Tool Modern", version=__version__)
    app.state.context = context

    app.include_router(system.router, prefix="/api")
    app.include_router(datasets.router, prefix="/api")
    app.include_router(media.router, prefix="/api")
    app.include_router(metadata.router, prefix="/api")
    app.include_router(media_tools.router, prefix="/api")
    app.include_router(krita.router, prefix="/api")
    app.include_router(tags.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    app.include_router(orchestration.router, prefix="/api")
    app.include_router(augment.router, prefix="/api")
    app.include_router(database.router, prefix="/api")
    app.include_router(export.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(presets.router, prefix="/api")
    app.include_router(downloads.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(distributed.router, prefix="/api")
    app.include_router(voice.router, prefix="/api")
    app.include_router(reference.router, prefix="/api")
    app.include_router(browser.router, prefix="/api")
    app.include_router(blender.router, prefix="/api")
    app.include_router(spatial.router, prefix="/api")
    app.include_router(three_d.router, prefix="/api")
    app.include_router(flexavatar.router, prefix="/api")
    app.include_router(comfy_bridge.router, prefix="/api")
    app.include_router(migration.router, prefix="/api")
    app.include_router(code_assistant.router, prefix="/api")
    app.include_router(cloud.router, prefix="/api")
    app.include_router(agent_tools.router, prefix="/api")
    app.include_router(mcp_tools.router, prefix="/api")

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.on_event("startup")
    def startup_tag_dictionary_sync() -> None:
        c = app.state.context
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        try:
            desired_tag_mode = getattr(c.settings, "tag_text_mode", "underscores") or "underscores"
            active_tag_mode = getattr(c.settings, "tag_text_mode_active", "underscores") or "underscores"
            if desired_tag_mode != active_tag_mode:
                result = c.tags.apply_tag_text_mode(desired_tag_mode, old_mode=active_tag_mode)
                c.settings.tag_text_mode_active = desired_tag_mode
                c.settings.tag_text_mode_restart_required = False
                c.db.set_setting("tag_text_mode_active", desired_tag_mode)
                c.db.set_setting("tag_text_mode_restart_required", False)
                c.settings.save(c.paths.settings)
                print(f"[Data Curation Tool] Applied tag text mode migration: {active_tag_mode} -> {desired_tag_mode} ({result})")
        except Exception as exc:
            print(f"[Data Curation Tool] Tag text mode startup migration failed: {exc}")
        try:
            if getattr(c.settings, "agent_tools_smoke_test_on_startup", True):
                c.agent_tools.smoke_test_tools(force=True)
        except Exception as exc:
            print(f"[Data Curation Tool] Agent tool startup smoke test failed: {exc}")
        try:
            if getattr(c.settings, "voice_stt_load_policy", "on_demand") == "always" or getattr(c.settings, "voice_tts_load_policy", "on_demand") == "always":
                def voice_preload_task(progress):
                    progress(0.05, "Loading always-on STT/TTS voice model(s)")
                    result = c.voice.preload_from_settings()
                    progress(1.0, "Voice model preload complete")
                    return result
                c.jobs.submit("voice_model_preload", {"stt": getattr(c.settings, "voice_stt_model_name", None), "tts": getattr(c.settings, "voice_tts_model_name", None)}, voice_preload_task)
        except Exception as exc:
            print(f"[Data Curation Tool] Voice model startup preload queue failed: {exc}")
        startup_sources = list(getattr(c.settings, "previous_install_paths", []) or [])
        env_sources = [x.strip() for x in os.environ.get("DCT_PREVIOUS_INSTALLS", "").split(os.pathsep) if x.strip()]
        if env_sources:
            startup_sources.extend(env_sources)
        should_migrate = bool(getattr(c.settings, "migrate_assets_on_startup", False)) or os.environ.get("DCT_MIGRATE_ON_STARTUP") == "1"
        if should_migrate and startup_sources:
            try:
                c.migration.migrate(
                    startup_sources,
                    include=getattr(c.settings, "migration_include_assets", {}) or {},
                    mode=os.environ.get("DCT_MIGRATION_MODE") or getattr(c.settings, "migration_mode", "copy") or "copy",
                    conflict=getattr(c.settings, "migration_conflict_policy", "skip_existing") or "skip_existing",
                    newest_first=bool(getattr(c.settings, "migration_newest_first", True)),
                    delete_source_duplicates=bool(getattr(c.settings, "migration_delete_source_duplicates", False)),
                    dry_run=False,
                    progress=None,
                )
                try:
                    c.registry.load_custom_models(c.paths.runtime / "custom_models.json")
                    c.models.reconcile_local_assets()
                    c.tags.reconcile_export_cache()
                except Exception as exc:
                    print(f"[Data Curation Tool] Startup asset reconciliation failed: {exc}")
            except Exception as exc:
                print(f"[Data Curation Tool] Startup asset migration failed: {exc}")
        else:
            try:
                c.registry.load_custom_models(c.paths.runtime / "custom_models.json")
                c.models.reconcile_local_assets()
                c.tags.reconcile_export_cache()
            except Exception:
                pass
        if getattr(c.settings, "assistant_model_auto_load", False):
            assistant_name = getattr(c.settings, "assistant_model_name", "dataset-assistant") or "dataset-assistant"
            if assistant_name and not c.models.is_model_loaded(assistant_name):
                c.models.lifecycle.update(assistant_name, "load", state="queued", progress=0.0, message="Assistant auto-load queued")
                def assistant_load_task(progress, job_id: int, _name=assistant_name):
                    device = (getattr(c.settings, "preferred_devices", None) or ["auto"])[0] or "auto"
                    request = ModelLoadRequest(model_name=_name, device=device, device_ids=getattr(c.settings, "default_model_device_ids", []) or [], sharding_strategy=getattr(c.settings, "default_model_sharding_strategy", "none") or "none", torch_dtype=getattr(c.settings, "default_model_dtype", "auto") or "auto", quantization=getattr(c.settings, "default_model_quantization", "none") or "none", runtime_engine=getattr(c.settings, "default_model_runtime_engine", "transformers") or "transformers", tensor_parallel_size=int(getattr(c.settings, "default_tensor_parallel_size", 1) or 1))
                    return c.models.load(request, progress=progress, job_id=job_id)
                job_id = c.jobs.submit_with_job_id("model_load", {"model_name": assistant_name, "startup_auto_load": True}, assistant_load_task)
                c.models.lifecycle.update(assistant_name, "load", job_id=job_id)
        if os.environ.get("DCT_SKIP_STARTUP_TAG_SYNC") == "1":
            return
        if not getattr(c.settings, "auto_sync_tag_db_on_startup", True):
            return
        profile_key = c.settings.default_tag_profile or "e621"
        if not c.tags.should_auto_sync_default_export(
            profile_key,
            empty_only=False,
            cache_hours=int(getattr(c.settings, "tag_db_export_cache_hours", 336) or 336),
        ):
            return

        def task(progress):
            return c.tags.import_default_exports(
                profile_key=profile_key,
                user_agent=c.settings.downloader_user_agent or "DataCurationTool/5.32.0",
                cache_hours=int(getattr(c.settings, "tag_db_export_cache_hours", 336) or 336),
                progress=progress,
                replace_existing=True,
            )

        c.jobs.submit("tag_dictionary_startup_sync", {"profile_key": profile_key}, task)

    @app.on_event("shutdown")
    def shutdown_background_jobs() -> None:
        c = app.state.context
        if getattr(c, "jobs", None):
            c.jobs.shutdown(wait=False)

    @app.get("/docs/{filename:path}", include_in_schema=False)
    def project_doc(filename: str):
        doc = (paths.root / "docs" / filename).resolve()
        docs_root = (paths.root / "docs").resolve()
        try:
            doc.relative_to(docs_root)
        except Exception:
            return FileResponse(static_dir / "index.html")
        if doc.exists() and doc.is_file():
            return FileResponse(doc)
        return FileResponse(static_dir / "index.html")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/health")
    def health():
        return {"ok": True, "version": __version__, "time": datetime.now(timezone.utc), "database": str(paths.database)}

    return app

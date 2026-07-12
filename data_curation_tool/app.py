from __future__ import annotations

from datetime import datetime, timezone
import os
import threading
import time
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
from .routers import augment, database, datasets, distributed, downloads, export, jobs, krita, media, media_tools, metadata, models, orchestration, presets, settings, system, tags, voice, reference, character_reference, browser, blender, spatial, three_d, flexavatar, comfy_bridge, migration, code_assistant, cloud, agent_tools, mcp_tools, global_dataset, pipeline_prep, dataset_pipeline, workflows, graph_editor, agentic_graphs, attention, multimodal_dataset_builder, integrity_classifiers
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
from .services.global_dataset_service import GlobalDatasetService
from .services.dataset_pipeline_service import DatasetPipelineService
from .services.pipeline_prep_service import PipelinePrepService
from .services.character_reference_service import CharacterReferenceService
from .services.workflow_automation_service import WorkflowAutomationService
from .services.graph_editor_service import GraphEditorService
from .services.startup_progress_service import StartupProgressService
from .services.attention_visualization_service import AttentionVisualizationService
from .services.multimodal_dataset_service import MultimodalDatasetService
from .services.integrity_classifier_service import IntegrityClassifierService
from .schemas import ModelLoadRequest
from .utils import set_tag_text_mode


def _clean_tag_text_mode(value: object, fallback: str = "underscores") -> str:
    mode = str(value or fallback or "underscores").strip().lower()
    return mode if mode in {"underscores", "spaces"} else fallback


def _hydrate_tag_text_mode_from_db(settings: AppSettings, db: Database, settings_path: Path) -> None:
    """Keep the tag-format setting durable across app launches and package swaps.

    Earlier builds mirrored Settings changes into both runtime/settings.json and
    the SQLite settings table, but app startup only trusted settings.json.  That
    made manual file replacement or a stale JSON file appear to "forget" the
    user's tag-format choice until they selected it again.  Treat the SQLite
    value as a recovery mirror when present, then immediately re-save JSON so
    future starts are deterministic.
    """
    changed = False
    desired = db.get_setting("tag_text_mode", None)
    active = db.get_setting("tag_text_mode_active", None)
    restart_required = db.get_setting("tag_text_mode_restart_required", None)
    if desired in {"underscores", "spaces"} and desired != getattr(settings, "tag_text_mode", "underscores"):
        settings.tag_text_mode = str(desired)
        changed = True
    if active in {"underscores", "spaces"} and active != getattr(settings, "tag_text_mode_active", "underscores"):
        settings.tag_text_mode_active = str(active)
        changed = True
    settings.tag_text_mode = _clean_tag_text_mode(getattr(settings, "tag_text_mode", "underscores"))
    settings.tag_text_mode_active = _clean_tag_text_mode(getattr(settings, "tag_text_mode_active", "underscores"))
    derived_restart_required = settings.tag_text_mode != settings.tag_text_mode_active
    if isinstance(restart_required, bool):
        derived_restart_required = restart_required or derived_restart_required
    if getattr(settings, "tag_text_mode_restart_required", False) != derived_restart_required:
        settings.tag_text_mode_restart_required = derived_restart_required
        changed = True
    if changed:
        settings.save(settings_path)
        db.set_setting("tag_text_mode", settings.tag_text_mode)
        db.set_setting("tag_text_mode_active", settings.tag_text_mode_active)
        db.set_setting("tag_text_mode_restart_required", settings.tag_text_mode_restart_required)


def build_context(paths: AppPaths) -> AppContext:
    app_settings = AppSettings.load(paths.settings)
    db = Database(paths.database)
    _hydrate_tag_text_mode_from_db(app_settings, db, paths.settings)
    set_tag_text_mode(getattr(app_settings, "tag_text_mode", "underscores"))
    if not app_settings.model_cache_dir:
        app_settings.model_cache_dir = str(paths.models / "hf")
        app_settings.save(paths.settings)
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
    # Include both the configured external roots and the effective Hugging Face
    # cache directory.  Migration can preserve models under models/hf,
    # models/huggingface, .cache/huggingface/hub, or an older install's direct
    # model_cache_dir.  Registering these roots here lets the catalog/load path
    # resolve migrated snapshots instead of starting a fresh download.
    external_roots = list(getattr(app_settings, "external_model_roots", []) or [])
    if getattr(app_settings, "model_cache_dir", None):
        try:
            cache_path = Path(str(app_settings.model_cache_dir)).expanduser()
            external_roots.append(str(cache_path))
            if cache_path.name.lower() in {"hf", "huggingface", "hub", "checkpoints", "direct", "ultralytics"}:
                external_roots.append(str(cache_path.parent))
        except Exception:
            pass
    registry.set_external_model_roots(external_roots)
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
    global_dataset_service = GlobalDatasetService(db, paths, app_settings)
    pipeline_prep_service = PipelinePrepService(db, paths, app_settings, global_dataset_service, model_service=model_service)
    context_holder: dict[str, AppContext] = {}
    workflow_service = WorkflowAutomationService(paths, app_context_getter=lambda: context_holder["context"])
    graph_editor_service = GraphEditorService(paths, app_context_getter=lambda: context_holder["context"])
    startup_progress_service = StartupProgressService()
    attention_service = AttentionVisualizationService(paths, media_service, model_service)
    multimodal_service = MultimodalDatasetService(db, paths)
    # Cross-service job manager is shared with Agent Tools so orchestrator/assistant
    # tool calls can enqueue model load/run/unload jobs that remain visible in the Jobs UI.
    job_manager = JobManager(db, max_workers=max(1, int(app_settings.max_concurrent_jobs or app_settings.backend_worker_count or 1)))
    model_service.pipeline_prep = pipeline_prep_service
    app_context = AppContext(
        paths=paths,
        settings=app_settings,
        db=db,
        jobs=job_manager,
        registry=registry,
        media=media_service,
        metadata=metadata_service,
        tags=tag_service,
        datasets=dataset_service,
        models=model_service,
        augment=AugmentationService(db, media_service, external_app_service),
        exports=ExportService(db, media_service),
        presets=preset_service,
        downloads=DownloaderService(db, preset_service, app_settings.downloader_user_agent, tag_service, global_dataset_service, app_settings),
        distributed=DistributedService(paths),
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
        agent_tools=AgentToolsService(paths, app_settings, model_service, browser=browser_service, jobs=job_manager),
        mcp_tools=MCPToolsService(paths, app_settings),
        global_dataset=global_dataset_service,
        dataset_pipeline=DatasetPipelineService(paths, global_dataset_service),
        pipeline_prep=pipeline_prep_service,
        character_reference=CharacterReferenceService(db, paths, media_service, global_dataset_service),
        workflows=workflow_service,
        graph_editor=graph_editor_service,
        startup_progress=startup_progress_service,
        attention=attention_service,
        multimodal=multimodal_service,
        integrity_classifiers=IntegrityClassifierService(db, paths, media_service, tag_service),
    )
    context_holder["context"] = app_context
    return app_context


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
    app.include_router(character_reference.router, prefix="/api")
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
    app.include_router(global_dataset.router, prefix="/api")
    app.include_router(dataset_pipeline.router, prefix="/api")
    app.include_router(pipeline_prep.router, prefix="/api")
    app.include_router(workflows.router, prefix="/api")
    app.include_router(graph_editor.router, prefix="/api")
    app.include_router(agentic_graphs.router, prefix="/api")
    app.include_router(attention.router, prefix="/api")
    app.include_router(multimodal_dataset_builder.router, prefix="/api")
    app.include_router(integrity_classifiers.router, prefix="/api")

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    def _run_deferred_startup_initialization(c, progress, job_id: int) -> dict:
        started = time.monotonic()
        result: dict[str, object] = {"job_id": job_id, "steps": []}

        def record(name: str, status: str, detail: object | None = None) -> None:
            row = {"name": name, "status": status}
            if detail is not None:
                row["detail"] = detail
            result.setdefault("steps", []).append(row)

        def emit(value: float, message: str) -> None:
            safe = max(0.0, min(0.995, float(value or 0.0)))
            try:
                c.startup_progress.update(safe, message, phase="startup")
            except Exception:
                pass
            progress(safe, message)

        def span(start_value: float, end_value: float):
            def _inner(value: float, message: str = "") -> None:
                try:
                    v = max(0.0, min(1.0, float(value or 0.0)))
                except Exception:
                    v = 0.0
                emit(start_value + (end_value - start_value) * v, message)
            return _inner

        emit(0.01, "Starting application initialization")
        try:
            desired_tag_mode = getattr(c.settings, "tag_text_mode", "underscores") or "underscores"
            active_tag_mode = getattr(c.settings, "tag_text_mode_active", "underscores") or "underscores"
            if desired_tag_mode != active_tag_mode:
                emit(0.04, f"Applying tag text mode migration: {active_tag_mode} -> {desired_tag_mode}")
                migration_result = c.tags.apply_tag_text_mode(desired_tag_mode, old_mode=active_tag_mode)
                c.settings.tag_text_mode_active = desired_tag_mode
                c.settings.tag_text_mode_restart_required = False
                c.db.set_setting("tag_text_mode_active", desired_tag_mode)
                c.db.set_setting("tag_text_mode_restart_required", False)
                c.settings.save(c.paths.settings)
                try:
                    c.tags.invalidate_cache(None)
                    c.tags.dictionary_status(getattr(c.settings, "default_tag_profile", "e621") or "e621")
                except Exception as refresh_exc:
                    record("tag_text_mode_status_refresh", "warning", str(refresh_exc))
                record("tag_text_mode_migration", "completed", migration_result)
            else:
                record("tag_text_mode_migration", "skipped", "already active")
        except Exception as exc:
            record("tag_text_mode_migration", "failed", str(exc))
            print(f"[Data Curation Tool] Tag text mode startup migration failed: {exc}")
        emit(0.14, "Tag mode startup checks complete")

        try:
            if getattr(c.settings, "agent_tools_smoke_test_on_startup", True):
                emit(0.16, "Checking local agent tools")
                c.agent_tools.smoke_test_tools(force=False)
                record("agent_tools_smoke_test", "completed_or_cached")
            else:
                record("agent_tools_smoke_test", "skipped")
        except Exception as exc:
            record("agent_tools_smoke_test", "failed", str(exc))
            print(f"[Data Curation Tool] Agent tool startup smoke test failed: {exc}")
        emit(0.23, "Agent tool startup checks complete")

        try:
            if getattr(c.settings, "voice_stt_load_policy", "on_demand") == "always" or getattr(c.settings, "voice_tts_load_policy", "on_demand") == "always":
                emit(0.25, "Queueing always-on voice model preload")
                def voice_preload_task(voice_progress):
                    voice_progress(0.05, "Loading always-on STT/TTS voice model(s)")
                    voice_result = c.voice.preload_from_settings()
                    voice_progress(1.0, "Voice model preload complete")
                    return voice_result
                voice_job = c.jobs.submit("voice_model_preload", {"stt": getattr(c.settings, "voice_stt_model_name", None), "tts": getattr(c.settings, "voice_tts_model_name", None)}, voice_preload_task)
                record("voice_model_preload", "queued", {"job_id": voice_job})
            else:
                record("voice_model_preload", "skipped")
        except Exception as exc:
            record("voice_model_preload", "failed", str(exc))
            print(f"[Data Curation Tool] Voice model startup preload queue failed: {exc}")
        emit(0.30, "Voice startup checks complete")

        startup_sources = list(getattr(c.settings, "previous_install_paths", []) or [])
        env_sources = [x.strip() for x in os.environ.get("DCT_PREVIOUS_INSTALLS", "").split(os.pathsep) if x.strip()]
        if env_sources:
            startup_sources.extend(env_sources)
        should_migrate = bool(getattr(c.settings, "migrate_assets_on_startup", False)) or os.environ.get("DCT_MIGRATE_ON_STARTUP") == "1"
        try:
            if should_migrate and startup_sources:
                emit(0.34, "Migrating/reconciling assets from previous install paths")
                migration_result = c.migration.migrate(
                    startup_sources,
                    include=getattr(c.settings, "migration_include_assets", {}) or {},
                    mode=os.environ.get("DCT_MIGRATION_MODE") or getattr(c.settings, "migration_mode", "copy") or "copy",
                    conflict=getattr(c.settings, "migration_conflict_policy", "skip_existing") or "skip_existing",
                    newest_first=bool(getattr(c.settings, "migration_newest_first", True)),
                    delete_source_duplicates=bool(getattr(c.settings, "migration_delete_source_duplicates", False)),
                    dry_run=False,
                    progress=span(0.34, 0.52),
                    parallel_file_transfers=bool(getattr(c.settings, "migration_parallel_file_transfers", True)),
                    file_transfer_workers=int(getattr(c.settings, "migration_file_transfer_workers", 4) or 4),
                    fast_same_volume_moves=bool(getattr(c.settings, "migration_fast_same_volume_moves", True)),
                )
                record("asset_migration", "completed", migration_result)
            else:
                record("asset_migration", "skipped")
            profile_key = getattr(c.settings, "default_tag_profile", "e621") or "e621"
            emit(0.54, f"Reconciling model assets and {profile_key} tag export cache")
            c.registry.load_custom_models(c.paths.runtime / "custom_models.json")
            c.models.reconcile_local_assets()
            # Keep routine startup fast after the first successful run.  The full
            # multi-profile cache scan can be expensive once many booru profiles
            # are supported, so startup only reconciles the active/default profile.
            # A manual migration or dictionary sync can still reconcile additional
            # profiles on demand.
            c.tags.reconcile_export_cache(profile_key)
            record("asset_reconciliation", "completed", {"profile_key": profile_key})
        except Exception as exc:
            record("asset_reconciliation", "failed", str(exc))
            print(f"[Data Curation Tool] Startup asset migration/reconciliation failed: {exc}")
        emit(0.62, "Asset startup checks complete")

        try:
            if getattr(c.settings, "assistant_model_auto_load", False):
                assistant_name = getattr(c.settings, "assistant_model_name", "dataset-assistant") or "dataset-assistant"
                if assistant_name and not c.models.is_model_loaded(assistant_name):
                    emit(0.64, f"Queueing assistant model auto-load: {assistant_name}")
                    c.models.lifecycle.update(assistant_name, "load", state="queued", progress=0.0, message="Assistant auto-load queued")
                    def assistant_load_task(model_progress, model_job_id: int, _name=assistant_name):
                        device = (getattr(c.settings, "preferred_devices", None) or ["auto"])[0] or "auto"
                        request = ModelLoadRequest(model_name=_name, device=device, device_ids=getattr(c.settings, "default_model_device_ids", []) or [], sharding_strategy=getattr(c.settings, "default_model_sharding_strategy", "none") or "none", torch_dtype=getattr(c.settings, "default_model_dtype", "auto") or "auto", quantization=getattr(c.settings, "default_model_quantization", "none") or "none", runtime_engine=getattr(c.settings, "default_model_runtime_engine", "transformers") or "transformers", tensor_parallel_size=int(getattr(c.settings, "default_tensor_parallel_size", 1) or 1))
                        return c.models.load(request, progress=model_progress, job_id=model_job_id)
                    auto_job = c.jobs.submit_with_job_id("model_load", {"model_name": assistant_name, "startup_auto_load": True}, assistant_load_task)
                    c.models.lifecycle.update(assistant_name, "load", job_id=auto_job)
                    record("assistant_model_auto_load", "queued", {"job_id": auto_job, "model_name": assistant_name})
                else:
                    record("assistant_model_auto_load", "skipped", "already loaded or not configured")
            else:
                record("assistant_model_auto_load", "skipped")
        except Exception as exc:
            record("assistant_model_auto_load", "failed", str(exc))
            print(f"[Data Curation Tool] Assistant model startup auto-load failed: {exc}")
        emit(0.70, "Assistant startup checks complete")

        try:
            if os.environ.get("DCT_SKIP_STARTUP_TAG_SYNC") == "1":
                record("tag_dictionary_startup_sync", "skipped", "DCT_SKIP_STARTUP_TAG_SYNC=1")
            elif not getattr(c.settings, "auto_sync_tag_db_on_startup", True):
                record("tag_dictionary_startup_sync", "skipped", "disabled in settings")
            elif should_migrate and startup_sources and getattr(c.settings, "migration_skip_post_online_tag_sync", True):
                record("tag_dictionary_startup_sync", "skipped", "startup migration is configured for local-only/no-internet tag cache reuse")
            else:
                profile_key = c.settings.default_tag_profile or "e621"
                startup_interval = int(getattr(c.settings, "tag_db_startup_sync_interval_hours", 168) or 168)
                cache_hours = int(getattr(c.settings, "tag_db_export_cache_hours", 168) or 168)
                emit(0.72, f"Checking {profile_key} tag dictionary cache")
                needs_sync = c.tags.should_auto_sync_default_export(
                    profile_key,
                    empty_only=bool(getattr(c.settings, "tag_db_sync_if_empty_only", True)),
                    cache_hours=cache_hours,
                )
                status = c.tags.dictionary_status(profile_key)
                try:
                    total_rows = int((status or {}).get("total") or 0)
                except Exception:
                    total_rows = 0
                first_run_missing = bool(needs_sync and total_rows <= 0)
                if needs_sync and (first_run_missing or not c.tags.startup_sync_recently_checked(profile_key, startup_interval)):
                    # Empty first-run installs must bootstrap immediately even if an old failed/partial
                    # check marker exists.  Non-empty/stale installs remain gated by the weekly interval.
                    c.tags.mark_startup_sync_checked(profile_key, status="checked")
                    emit(0.76, f"Synchronizing {profile_key} tag dictionary")
                    sync_result = c.tags.import_default_exports(
                        profile_key=profile_key,
                        user_agent=c.settings.downloader_user_agent or f"DataCurationTool/{__version__}",
                        cache_hours=cache_hours,
                        progress=span(0.76, 0.98),
                        replace_existing=True,
                        force_download=bool(first_run_missing),
                    )
                    c.tags.mark_startup_sync_checked(profile_key, status="completed", detail={"imported": sync_result.get("imported", 0) if isinstance(sync_result, dict) else None, "first_run_missing": first_run_missing})
                    record("tag_dictionary_startup_sync", "completed", sync_result)
                elif needs_sync:
                    record("tag_dictionary_startup_sync", "skipped", f"startup network sync already checked within {startup_interval} hour(s); use Sync Now to force an update")
                else:
                    c.tags.mark_startup_sync_checked(profile_key, status="skipped_fresh")
                    record("tag_dictionary_startup_sync", "skipped", "cache already fresh or local migrated dictionary is sufficient")
        except Exception as exc:
            record("tag_dictionary_startup_sync", "failed", str(exc))
            print(f"[Data Curation Tool] Tag dictionary startup sync failed: {exc}")
        progress(1.0, "Startup initialization complete")
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        return result

    @app.on_event("startup")
    def startup_tag_dictionary_sync() -> None:
        c = app.state.context
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        try:
            existing = c.db.query_one("SELECT id FROM jobs WHERE type=? AND status IN ('queued','running') ORDER BY id DESC LIMIT 1", ("startup_initialization",))
            if existing:
                return
        except Exception:
            pass
        def task(progress, job_id: int):
            c.startup_progress.start("Starting application initialization")
            try:
                result = _run_deferred_startup_initialization(c, progress, job_id)
                c.startup_progress.complete("Startup initialization complete")
                return result
            except Exception as exc:
                c.startup_progress.fail(exc, "Startup initialization failed")
                raise

        c.jobs.submit_with_job_id(
            "startup_initialization",
            {"version": __version__, "profile_key": getattr(c.settings, "default_tag_profile", "e621") or "e621"},
            task,
        )

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

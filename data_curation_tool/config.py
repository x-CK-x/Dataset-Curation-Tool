from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_CATEGORY_COLORS = {
    "general": "#6574cd",
    "artist": "#a855f7",
    "character": "#10b981",
    "copyright": "#f59e0b",
    "species": "#06b6d4",
    "meta": "#64748b",
    "rating": "#ef4444",
    "invalid": "#71717a",
    "inferred": "#84cc16",
    "caption": "#0ea5e9",
}




def _default_cloud_model_runtime_defaults() -> dict[str, Any]:
    """Default provider/model options used by cloud LLM/VLM/API adapters."""
    return {
        "openrouter": {
            "enabled": True,
            "token_profile": "",
            "model_id": "deepseek/deepseek-v4-pro",
            "context_shrinker_model": "deepseek/deepseek-v4-flash",
            "context_shrink_policy": "auto_middle_out",
            "max_input_tokens": 250000,
            "max_output_tokens": 4096,
            "provider_route": {"allow_fallbacks": True, "order": []},
            "transforms": ["middle-out"],
        },
        "openai": {
            "enabled": True,
            "token_profile": "",
            "model_id": "",
            "context_shrinker_model": "",
            "context_shrink_policy": "auto_summary",
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
        },
        "anthropic": {
            "enabled": True,
            "token_profile": "",
            "model_id": "",
            "context_shrinker_model": "",
            "context_shrink_policy": "auto_summary",
            "max_input_tokens": 180000,
            "max_output_tokens": 4096,
        },
        "generic": {
            "enabled": False,
            "token_profile": "",
            "endpoint": "",
            "model_id": "",
            "context_shrinker_model": "",
            "context_shrink_policy": "off",
            "max_input_tokens": 64000,
            "max_output_tokens": 2048,
        },
    }


def _default_external_mcp_tools() -> dict[str, dict[str, Any]]:
    """External creative tools are enabled automatically when detected."""
    base = {
        "blender": ("Blender", ""),
        "krita": ("Krita", ""),
        "audacity": ("Audacity", ""),
        "obs": ("OBS Studio", "ws://127.0.0.1:4455"),
        "comfyui": ("ComfyUI", "http://127.0.0.1:8188"),
        "zbrush": ("ZBrush", ""),
        "prusaslicer": ("PrusaSlicer", ""),
        "orcaslicer": ("OrcaSlicer", ""),
        "bambu_studio": ("Bambu Studio", ""),
        "curaengine": ("CuraEngine", ""),
        "slic3r": ("Slic3r", ""),
        "kohya_ss": ("Kohya SS / sd-scripts", ""),
        "onetrainer": ("OneTrainer", ""),
        "diffusers_trainer": ("Hugging Face Diffusers Trainer Scripts", ""),
        "ltx_trainer": ("LTX Trainer", ""),
        "external_webscraper": ("External Webscraper Bridge", ""),
        "browser_default": ("Default Browser MCP", ""),
        "browser_edge": ("Microsoft Edge Browser MCP", ""),
        "browser_chrome": ("Google Chrome Browser MCP", ""),
        "browser_firefox": ("Mozilla Firefox Browser MCP", ""),
        "browser_chromium": ("Chromium Browser MCP", ""),
        "browser_tor": ("Tor Browser MCP", ""),
    }
    return {
        key: {
            "label": label,
            "enabled": True,
            "auto_enable_if_installed": True,
            "executable_path": "",
            "endpoint": endpoint,
            "mcp_command": "",
            "mcp_args": [],
            "transport": "stdio",
        }
        for key, (label, endpoint) in base.items()
    }

def _default_agent_tool_roots() -> list[str]:
    """Human-friendly local roots enabled by default for approved agent tools.

    These are intentionally generic user folders rather than project-specific
    paths, so a clean Windows install can read files from Downloads/Desktop/
    Documents after explicit COA approval without requiring the user to discover
    the allowed-roots setting first.
    """
    roots: list[str] = []
    home = Path.home()
    for name in ("Downloads", "Desktop", "Documents"):
        try:
            roots.append(str((home / name).resolve(strict=False)))
        except Exception:
            roots.append(str(home / name))
    return roots


@dataclass
class AppSettings:
    host: str = "127.0.0.1"
    port: int = 7865
    open_browser: bool = False
    enable_write_sql: bool = False
    default_page_size: int = 80
    tag_separator: str = ", "
    auto_save_sidecars: bool = True
    duplicate_hamming_threshold: int = 6
    category_colors: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_CATEGORY_COLORS))
    huggingface_token: str | None = None
    openrouter_token: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    # Multiple named tokens/profiles per provider.  Legacy single-token fields
    # above are still supported as defaults for backwards compatibility.
    api_token_profiles: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {
        "huggingface": [],
        "openrouter": [],
        "openai": [],
        "anthropic": [],
        "xai": [],
        "runpod": [],
        "vastai": [],
        "lambda_labs": [],
        "meshy": [],
        "tripo": [],
        "rodin": [],
        "krea": [],
        "ideogram": [],
    })
    model_cache_dir: str | None = None
    external_model_roots: list[str] = field(default_factory=list)
    preferred_devices: list[str] = field(default_factory=lambda: ["auto"])
    device_profiles: dict[str, Any] = field(default_factory=lambda: {"default": {"devices": ["auto"], "dtype": "auto", "max_vram_fraction": 0.92}})
    strict_driver_free_memory_checks: bool = False
    # Default to showing/using the full physical VRAM budget for placement planning.
    # Users can still cap individual GPUs with max_memory or device_profiles.
    model_vram_use_full_physical_capacity: bool = True
    # Runtime VRAM hygiene.  Long chat sessions can temporarily allocate large
    # KV caches and CUDA workspaces even when the model weights fit.  These
    # controls let the app clean temporary allocations, optionally disable
    # generation KV cache under pressure, and move idle/pressured models to CPU
    # RAM instead of leaving them in VRAM until the app exits.
    model_vram_cleanup_after_inference: bool = True
    model_vram_aggressive_gc_after_inference: bool = True
    model_vram_reset_peak_stats_after_inference: bool = True
    model_vram_auto_cpu_offload_enabled: bool = False
    # Skip CPU offload when system RAM is already pressured; CPU offload can
    # otherwise turn a VRAM pressure fix into an overnight system-RAM exhaustion.
    model_vram_skip_cpu_offload_when_system_ram_percent: float = 82.0
    model_system_ram_cleanup_warning_percent: float = 88.0
    model_system_ram_critical_percent: float = 94.0
    model_chat_storage_max_context_chars: int = 60000
    model_chat_storage_max_response_chars: int = 90000
    # disabled, on_pressure, after_chat, after_every_inference
    model_vram_auto_cpu_offload_policy: str = "on_pressure"
    model_vram_auto_cpu_offload_threshold: float = 0.82
    model_vram_idle_cpu_offload_seconds: int = 300
    model_vram_disable_generation_cache_on_pressure: bool = True
    model_vram_context_pressure_threshold: float = 0.70
    model_vram_cleanup_debug: bool = False
    downloader_user_agent: str = "DataCurationTool/5.36.0"
    authorized_sources_only: bool = True
    tag_suggestion_count: int = 40
    default_tag_profile: str = "e621"
    default_ordering_strategy: str = "booru"
    retain_imported_tag_order: bool = False
    # Global tag text policy. Desired can be changed at runtime, but the active
    # database/text policy is applied on startup so autocomplete dictionaries,
    # aliases, implications, media tag tables, and sidecars stay consistent.
    tag_text_mode: str = "underscores"  # underscores, spaces
    tag_text_mode_active: str = "underscores"
    tag_text_mode_restart_required: bool = False
    model_temperature: float = 0.2
    model_max_new_tokens: int = 512
    classifier_threshold: float = 0.70
    backend_worker_count: int = 4
    max_concurrent_jobs: int = 4
    download_max_concurrent_items: int = 4
    download_default_sort_order: str = "newest_to_oldest"
    downloader_parallel_presets: bool = False
    downloader_download_all_posts_default: bool = True
    downloader_dedupe_across_presets: bool = True
    downloader_store_membership_index: bool = True
    downloader_allow_duplicate_category_files: bool = False
    frontend_options: dict[str, Any] = field(default_factory=lambda: {"theme": "dark", "gallery_page_size": 80, "show_advanced": True})
    model_defaults: dict[str, Any] = field(default_factory=lambda: {"llm": {}, "vlm": {}, "classifier": {}, "tagger": {}, "cloud": {}})
    custom_models: list[dict[str, Any]] = field(default_factory=list)
    model_runtime_profiles: dict[str, Any] = field(default_factory=lambda: {"default": {"runtime_engine": "transformers", "shard_across_devices": False, "device_ids": [0], "dtype": "auto", "quantization": "none", "max_memory": {}}})
    default_model_runtime_engine: str = "transformers"
    default_model_sharding: bool = False
    default_model_sharding_strategy: str = "none"
    default_model_device_ids: list[int] = field(default_factory=lambda: [0])
    default_model_dtype: str = "auto"
    default_model_quantization: str = "none"
    default_tensor_parallel_size: int = 1
    assistant_model_name: str = "dataset-assistant"
    orchestrator_model_name: str = "dataset-assistant"
    assistant_model_auto_load: bool = False
    assistant_allow_orchestration: bool = True
    # Visible planning/deliberation controls. This is a user-visible plan layer,
    # not provider/private hidden chain-of-thought extraction.
    assistant_thinking_mode: str = "balanced"  # off, fast, balanced, deep
    assistant_reasoning_effort: str = "medium"  # none, low, medium, high, max
    assistant_show_visible_plan: bool = True
    assistant_planning_passes: int = 1
    assistant_plan_max_tokens: int = 768
    assistant_min_chat_tokens: int = 1024
    assistant_deep_chat_tokens: int = 4096
    assistant_max_auto_reflection_rounds: int = 1
    downloader_parallel_workers: int = 4
    model_download_parallel_workers: int = 1
    model_download_serial_queue: bool = True
    downloader_category_limit: int = 100
    downloader_per_tag_limit: int = 10
    downloader_api_delay_seconds: float = 7.0
    downloader_file_delay_seconds: float = 7.0
    downloader_request_timeout_seconds: int = 60
    downloader_max_retries: int = 3
    downloader_retry_backoff_seconds: float = 2.0
    orchestration_defaults: dict[str, Any] = field(default_factory=lambda: {"dry_run": True, "max_items": 100, "device_policy": "auto"})
    previous_install_paths: list[str] = field(default_factory=list)
    migrate_assets_on_startup: bool = False
    migration_include_assets: dict[str, bool] = field(default_factory=lambda: {"models": True, "tag_exports": True, "tag_database": True, "custom_tags": True, "custom_models": True, "presets": False, "downloads": False, "outputs": False})
    migration_mode: str = "move"
    migration_conflict_policy: str = "skip_existing"
    migration_newest_first: bool = True
    migration_delete_source_duplicates: bool = False
    # Migration should reuse cached assets/database rows from the previous install
    # and avoid network refreshes unless the user explicitly opts in.
    migration_local_only_existing_assets: bool = True
    migration_skip_post_online_tag_sync: bool = True
    migration_parallel_file_transfers: bool = True
    migration_file_transfer_workers: int = 4
    migration_fast_same_volume_moves: bool = True
    auto_sync_tag_db_on_startup: bool = True
    tag_db_sync_if_empty_only: bool = False
    tag_db_export_cache_hours: int = 168
    # Startup network sync gate.  Even when a dictionary is stale/incomplete,
    # automatic startup network checks should not run on every launch.
    tag_db_startup_sync_interval_hours: int = 168
    import_worker_count: int = 0
    metadata_extract_on_import: bool = False
    metadata_apply_when_no_sidecar: bool = True
    metadata_default_tag_source: str = "positive_prompt"
    metadata_default_caption_source: str = "positive_prompt"
    metadata_auto_extract_on_import: bool = False
    media_tools_default_frame_fps: float = 1.0
    media_tools_audio_format: str = "wav"
    media_frame_output_dir: str | None = None
    audio_recording_dir: str | None = None
    krita_bridge_output_dir: str | None = None
    krita_executable: str | None = None
    krita_handoff_dir: str | None = None

    # Human-approved local agent/tool execution.  Models can propose structured
    # tool calls, but local actions are still approved and logged by the user.
    agent_tools_enabled: bool = True
    agent_tools_require_approval: bool = True
    agent_tools_allow_shell: bool = True
    agent_tools_allow_python: bool = True
    agent_tools_allow_file_write: bool = True
    agent_tools_allow_browser: bool = True
    agent_tools_allow_existing_browser_profile: bool = True
    agent_tools_allow_high_risk: bool = True
    agent_tools_allow_any_path: bool = True
    agent_tools_enable_approved_coa_execution: bool = True
    agent_tools_auto_relay_after_execution: bool = True
    agent_tools_workspace: str | None = None
    agent_tools_allowed_roots: list[str] = field(default_factory=_default_agent_tool_roots)
    agent_tools_browser_profile_path: str | None = None
    agent_tools_sandbox_mode: str = "local"
    agent_tools_docker_image: str = "python:3.11-slim"
    agent_tools_default_timeout_seconds: int = 120
    agent_tools_max_timeout_seconds: int = 1800
    agent_tools_max_output_chars: int = 120000
    agent_tools_smoke_test_on_startup: bool = True
    agent_tools_allow_python_venv_install: bool = True
    agent_tools_default_python_venv: str = "agent-tools-default"
    # COA confirmation and self-repair policy. Defaults keep human approval for
    # every action, while still allowing approved plans to execute immediately.
    # Modes: always, high_risk_only, full_access_high_risk_confirm, full_auto.
    agent_tools_confirmation_mode: str = "always"
    agent_tools_auto_reattempt_enabled: bool = True
    agent_tools_max_reattempts: int = 2
    agent_tools_allow_infinite_reattempts: bool = False
    agent_tools_orchestrator_can_spawn_models: bool = True
    # Tool availability should not force every assistant response to use a tool.
    # The model is told to classify each request as direct answer, in-app GUI
    # action, external/local tool COA, or mixed.
    agent_tools_model_decides_when_to_use_tools: bool = True
    agent_tools_allow_plain_chat_without_tools: bool = True
    agent_tools_app_gui_action_routing: bool = True
    agent_tools_show_tool_decision_badges: bool = True
    assistant_show_live_action_notes: bool = True
    assistant_show_live_chain_of_thought: bool = True
    assistant_show_live_reasoning_trace: bool = True
    # Local voice I/O.  The first implementation is deliberate push-to-record:
    # the browser records audio, the backend transcribes it with the selected STT
    # model, and the user can edit the generated text before sending it to any
    # LLM/VLM assistant.  Wake-word/live capture can be layered on later.
    voice_stt_enabled: bool = True
    voice_tts_enabled: bool = False
    voice_stt_model_name: str = "whisper-large-v3-turbo"
    voice_tts_model_name: str = "kokoro-82m"
    # always = keep model resident when possible; on_demand = load/run/unload when requested.
    voice_stt_load_policy: str = "on_demand"
    voice_tts_load_policy: str = "on_demand"
    voice_stt_device: str = "auto"
    voice_tts_device: str = "auto"
    voice_stt_device_ids: list[int] = field(default_factory=list)
    voice_tts_device_ids: list[int] = field(default_factory=list)
    voice_stt_torch_dtype: str = "auto"
    voice_tts_torch_dtype: str = "auto"
    voice_stt_quantization: str = "none"
    voice_tts_quantization: str = "none"
    voice_stt_language: str | None = None
    voice_tts_language: str | None = None
    voice_tts_voice: str = "af_heart"
    voice_tts_auto_speak: bool = False
    # Long-form TTS protection. Many local TTS models have practical text
    # length limits and may silently truncate long paragraphs.  Keep chunking
    # enabled by default and stitch generated chunks into one WAV.
    voice_tts_chunk_long_text: bool = True
    voice_tts_max_chunk_chars: int = 360
    voice_tts_chunk_pause_ms: int = 180
    voice_browser_input_device_id: str | None = None
    voice_browser_output_device_id: str | None = None
    voice_save_recordings: bool = True
    voice_recording_format: str = "webm"

    # Optional FlexAvatar integration runs in an isolated research environment.
    flexavatar_conda_env: str = "dct-flexavatar"
    flexavatar_conda_executable: str | None = None
    flexavatar_python: str | None = None
    flexavatar_source_dir: str | None = None
    flexavatar_workspace_dir: str | None = None
    flexavatar_default_device: str = "cuda:0"
    flexavatar_job_timeout_seconds: int = 86400
    flexavatar_checkpoint_url: str | None = None
    preferred_external_image_tool: str = "topaz_photo_ai"
    external_image_tools: dict[str, Any] = field(default_factory=lambda: {
        "topaz_gigapixel": {"label": "Topaz Gigapixel", "executable_path": "", "mode": "open", "command_template": '"{exe}" "{input}"'},
        "topaz_photo_ai": {"label": "Topaz Photo AI", "executable_path": "", "mode": "open", "command_template": '"{exe}" "{input}"'},
        "topaz_sharpen": {"label": "Topaz Sharpen", "executable_path": "", "mode": "open", "command_template": '"{exe}" "{input}"'},
        "topaz_denoise": {"label": "Topaz DeNoise", "executable_path": "", "mode": "open", "command_template": '"{exe}" "{input}"'},
        "topaz_mask": {"label": "Topaz Mask", "executable_path": "", "mode": "open", "command_template": '"{exe}" "{input}"'},
        "krita": {"label": "Krita", "executable_path": "", "mode": "open", "command_template": '"{exe}" "{input}"'},
        "comfyui": {"label": "ComfyUI", "executable_path": "", "mode": "open", "command_template": '"{exe}"'}
    })
    # Cloud/provider runtime defaults for API-backed models, including token profile
    # selection, provider routing, and context-shrinking/fallback model hints.
    cloud_model_runtime_defaults: dict[str, Any] = field(default_factory=_default_cloud_model_runtime_defaults)
    # External MCP-capable creative tools. Installed tools are enabled by default;
    # missing tools remain visible with setup instructions.
    external_mcp_tools: dict[str, Any] = field(default_factory=_default_external_mcp_tools)

    # Global original/branch dataset layer. Originals are stored once by SHA-256;
    # model-specific datasets use lightweight branch manifests and editable sidecar copies.
    global_dataset_enabled: bool = True
    global_dataset_root: str | None = None
    global_dataset_originals_dir: str = "originals"
    global_dataset_branches_dir: str = "branches"
    global_dataset_variant_dir: str = "variants"
    global_dataset_ingest_copy_mode: str = "copy"  # copy, hardlink, symlink, reference
    global_dataset_auto_register_downloads: bool = True
    global_dataset_auto_link_downloads_to_branch: bool = False
    global_dataset_default_branch: str = "default"


    @classmethod
    def load(cls, path: Path) -> "AppSettings":
        if not path.exists():
            settings = cls()
            settings.save(path)
            return settings
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        allowed = {field_name for field_name in cls.__dataclass_fields__}
        cleaned = {k: v for k, v in payload.items() if k in allowed}
        # Startup tag DB sync should be fast after first-run setup.  The UI can still disable
        # empty-only mode when the user explicitly wants scheduled freshness checks.
        cleaned.setdefault("tag_db_sync_if_empty_only", False)
        try:
            _tag_cache_hours = int(cleaned.get("tag_db_export_cache_hours") or 168)
            # Older builds wrote 336 as the default.  The new policy is weekly
            # startup refresh gating, so migrate that old default to 168.
            if _tag_cache_hours == 336:
                _tag_cache_hours = 168
            cleaned["tag_db_export_cache_hours"] = max(24, _tag_cache_hours)
        except Exception:
            cleaned["tag_db_export_cache_hours"] = 168
        cleaned.setdefault("migration_parallel_file_transfers", True)
        cleaned.setdefault("migration_fast_same_volume_moves", True)
        try:
            cleaned["migration_file_transfer_workers"] = max(1, min(32, int(cleaned.get("migration_file_transfer_workers") or 4)))
        except Exception:
            cleaned["migration_file_transfer_workers"] = 4
        cleaned.setdefault("tag_db_startup_sync_interval_hours", 168)
        try:
            cleaned["tag_db_startup_sync_interval_hours"] = max(24, int(cleaned.get("tag_db_startup_sync_interval_hours") or 168))
        except Exception:
            cleaned["tag_db_startup_sync_interval_hours"] = 168
        if str(cleaned.get("downloader_user_agent") or "").startswith("DataCurationTool/5."):
            cleaned["downloader_user_agent"] = "DataCurationTool/5.36.0"
        cleaned["backend_worker_count"] = max(1, int(cleaned.get("backend_worker_count") or 4))
        cleaned["max_concurrent_jobs"] = max(1, int(cleaned.get("max_concurrent_jobs") or cleaned.get("backend_worker_count") or 4))
        cleaned.setdefault("download_max_concurrent_items", 4)
        cleaned.setdefault("tag_text_mode", "underscores")
        cleaned.setdefault("tag_text_mode_active", "underscores")
        if cleaned.get("tag_text_mode") not in {"underscores", "spaces"}:
            cleaned["tag_text_mode"] = "underscores"
        if cleaned.get("tag_text_mode_active") not in {"underscores", "spaces"}:
            cleaned["tag_text_mode_active"] = "underscores"
        cleaned["tag_text_mode_restart_required"] = cleaned.get("tag_text_mode") != cleaned.get("tag_text_mode_active")
        cleaned.setdefault("download_default_sort_order", "newest_to_oldest")
        cleaned.setdefault("downloader_parallel_presets", False)
        cleaned.setdefault("downloader_download_all_posts_default", True)
        cleaned.setdefault("downloader_dedupe_across_presets", True)
        cleaned.setdefault("downloader_store_membership_index", True)
        cleaned.setdefault("downloader_allow_duplicate_category_files", False)
        cleaned.setdefault("downloader_parallel_workers", 4)
        cleaned.setdefault("model_download_parallel_workers", 1)
        cleaned.setdefault("model_download_serial_queue", True)
        cleaned.setdefault("api_token_profiles", {"huggingface": [], "openrouter": [], "openai": [], "anthropic": [], "xai": [], "runpod": [], "vastai": [], "lambda_labs": [], "meshy": [], "tripo": [], "rodin": [], "krea": [], "ideogram": []})
        if not isinstance(cleaned.get("api_token_profiles"), dict):
            cleaned["api_token_profiles"] = {"huggingface": [], "openrouter": [], "openai": [], "anthropic": [], "xai": [], "runpod": [], "vastai": [], "lambda_labs": [], "meshy": [], "tripo": [], "rodin": [], "krea": [], "ideogram": []}
        cleaned.setdefault("downloader_category_limit", 100)
        cleaned.setdefault("downloader_per_tag_limit", 10)
        cleaned.setdefault("downloader_api_delay_seconds", 7.0)
        cleaned.setdefault("downloader_file_delay_seconds", 7.0)
        cleaned.setdefault("downloader_request_timeout_seconds", 60)
        cleaned.setdefault("downloader_max_retries", 3)
        cleaned.setdefault("downloader_retry_backoff_seconds", 2.0)
        cleaned.setdefault("previous_install_paths", [])
        cleaned.setdefault("migrate_assets_on_startup", False)
        cleaned.setdefault("migration_include_assets", {"models": True, "tag_exports": True, "tag_database": True, "custom_tags": True, "custom_models": True, "presets": False, "downloads": False, "outputs": False})
        if isinstance(cleaned.get("migration_include_assets"), dict):
            cleaned["migration_include_assets"].setdefault("custom_models", True)
        cleaned.setdefault("migration_mode", "move")
        cleaned.setdefault("migration_conflict_policy", "skip_existing")
        cleaned.setdefault("migration_newest_first", True)
        cleaned.setdefault("migration_delete_source_duplicates", False)
        cleaned.setdefault("migration_local_only_existing_assets", True)
        cleaned.setdefault("migration_skip_post_online_tag_sync", True)
        cleaned.setdefault("custom_models", [])
        cleaned.setdefault("external_model_roots", [])
        cleaned.setdefault("strict_driver_free_memory_checks", False)
        if not isinstance(cleaned.get("external_model_roots"), list):
            cleaned["external_model_roots"] = []
        cleaned.setdefault("default_model_runtime_engine", "transformers")
        cleaned.setdefault("default_model_sharding", False)
        cleaned.setdefault("default_model_sharding_strategy", "auto" if cleaned.get("default_model_sharding") else "none")
        cleaned.setdefault("default_model_device_ids", [0])
        cleaned.setdefault("default_model_dtype", "auto")
        cleaned.setdefault("default_model_quantization", "none")
        cleaned.setdefault("default_tensor_parallel_size", 1)
        cleaned.setdefault("assistant_model_name", "dataset-assistant")
        cleaned.setdefault("orchestrator_model_name", cleaned.get("assistant_model_name") or "dataset-assistant")
        cleaned.setdefault("assistant_model_auto_load", False)
        cleaned.setdefault("assistant_allow_orchestration", True)
        cleaned.setdefault("assistant_thinking_mode", "balanced")
        if cleaned.get("assistant_thinking_mode") not in {"off", "fast", "balanced", "deep"}:
            cleaned["assistant_thinking_mode"] = "balanced"
        cleaned.setdefault("assistant_reasoning_effort", "medium")
        if cleaned.get("assistant_reasoning_effort") not in {"none", "low", "medium", "high", "max"}:
            cleaned["assistant_reasoning_effort"] = "medium"
        cleaned.setdefault("assistant_show_visible_plan", True)
        cleaned.setdefault("assistant_planning_passes", 1)
        cleaned.setdefault("assistant_plan_max_tokens", 768)
        cleaned.setdefault("assistant_min_chat_tokens", 1024)
        cleaned.setdefault("assistant_deep_chat_tokens", 4096)
        cleaned.setdefault("assistant_max_auto_reflection_rounds", 1)
        for _key, _lo, _hi in (("assistant_planning_passes", 0, 3), ("assistant_plan_max_tokens", 128, 4096), ("assistant_min_chat_tokens", 256, 8192), ("assistant_deep_chat_tokens", 1024, 16384), ("assistant_max_auto_reflection_rounds", 0, 3)):
            try:
                cleaned[_key] = max(_lo, min(_hi, int(cleaned.get(_key) or _lo)))
            except Exception:
                cleaned[_key] = _lo
        defaults = AppSettings().external_image_tools
        current_tools = dict(cleaned.get("external_image_tools") or {})
        for key, value in defaults.items():
            current_tools.setdefault(key, dict(value))
        cleaned["external_image_tools"] = current_tools
        default_clouds = _default_cloud_model_runtime_defaults()
        current_clouds = dict(cleaned.get("cloud_model_runtime_defaults") or {})
        for key, value in default_clouds.items():
            row = dict(value)
            row.update(dict(current_clouds.get(key) or {}))
            current_clouds[key] = row
        cleaned["cloud_model_runtime_defaults"] = current_clouds
        default_mcps = _default_external_mcp_tools()
        current_mcps = dict(cleaned.get("external_mcp_tools") or {})
        for key, value in default_mcps.items():
            row = dict(value)
            row.update(dict(current_mcps.get(key) or {}))
            current_mcps[key] = row
        cleaned["external_mcp_tools"] = current_mcps

        cleaned.setdefault("model_vram_use_full_physical_capacity", True)
        cleaned.setdefault("model_vram_cleanup_after_inference", True)
        cleaned.setdefault("model_vram_aggressive_gc_after_inference", True)
        cleaned.setdefault("model_vram_reset_peak_stats_after_inference", True)
        cleaned.setdefault("model_vram_auto_cpu_offload_enabled", False)
        cleaned.setdefault("model_vram_auto_cpu_offload_policy", "on_pressure")
        if cleaned.get("model_vram_auto_cpu_offload_policy") not in {"disabled", "on_pressure", "after_chat", "after_every_inference"}:
            cleaned["model_vram_auto_cpu_offload_policy"] = "on_pressure"
        cleaned.setdefault("model_vram_auto_cpu_offload_threshold", 0.82)
        cleaned.setdefault("model_vram_idle_cpu_offload_seconds", 300)
        cleaned.setdefault("model_vram_disable_generation_cache_on_pressure", True)
        cleaned.setdefault("model_vram_context_pressure_threshold", 0.70)
        cleaned.setdefault("model_vram_skip_cpu_offload_when_system_ram_percent", 82.0)
        cleaned.setdefault("model_system_ram_cleanup_warning_percent", 88.0)
        cleaned.setdefault("model_system_ram_critical_percent", 94.0)
        cleaned.setdefault("model_chat_storage_max_context_chars", 60000)
        cleaned.setdefault("model_chat_storage_max_response_chars", 90000)
        cleaned.setdefault("model_vram_cleanup_debug", False)
        try:
            cleaned["model_vram_auto_cpu_offload_threshold"] = max(0.50, min(0.98, float(cleaned.get("model_vram_auto_cpu_offload_threshold") or 0.82)))
        except Exception:
            cleaned["model_vram_auto_cpu_offload_threshold"] = 0.82
        try:
            cleaned["model_vram_context_pressure_threshold"] = max(0.35, min(0.95, float(cleaned.get("model_vram_context_pressure_threshold") or 0.70)))
        except Exception:
            cleaned["model_vram_context_pressure_threshold"] = 0.70
        try:
            cleaned["model_vram_idle_cpu_offload_seconds"] = max(0, min(86400, int(cleaned.get("model_vram_idle_cpu_offload_seconds") or 300)))
        except Exception:
            cleaned["model_vram_idle_cpu_offload_seconds"] = 300
        for _key, _default, _lo, _hi in (("model_vram_skip_cpu_offload_when_system_ram_percent", 82.0, 40.0, 99.0), ("model_system_ram_cleanup_warning_percent", 88.0, 40.0, 99.5), ("model_system_ram_critical_percent", 94.0, 50.0, 99.9)):
            try:
                cleaned[_key] = max(_lo, min(_hi, float(cleaned.get(_key) or _default)))
            except Exception:
                cleaned[_key] = _default
        for _key, _default, _lo, _hi in (("model_chat_storage_max_context_chars", 60000, 12000, 500000), ("model_chat_storage_max_response_chars", 90000, 20000, 800000)):
            try:
                cleaned[_key] = max(_lo, min(_hi, int(cleaned.get(_key) or _default)))
            except Exception:
                cleaned[_key] = _default
        cleaned.setdefault("agent_tools_enabled", True)
        cleaned.setdefault("agent_tools_require_approval", True)
        cleaned.setdefault("agent_tools_allow_shell", True)
        cleaned.setdefault("agent_tools_allow_python", True)
        cleaned.setdefault("agent_tools_allow_file_write", True)
        cleaned.setdefault("agent_tools_allow_browser", True)
        cleaned.setdefault("agent_tools_allow_existing_browser_profile", True)
        cleaned.setdefault("agent_tools_allow_high_risk", True)
        cleaned.setdefault("agent_tools_allow_any_path", True)
        cleaned.setdefault("agent_tools_enable_approved_coa_execution", True)
        cleaned.setdefault("agent_tools_auto_relay_after_execution", True)
        cleaned.setdefault("agent_tools_workspace", None)
        cleaned.setdefault("agent_tools_allowed_roots", _default_agent_tool_roots())
        cleaned.setdefault("agent_tools_browser_profile_path", None)
        cleaned.setdefault("agent_tools_sandbox_mode", "local")
        cleaned.setdefault("agent_tools_docker_image", "python:3.11-slim")
        cleaned.setdefault("agent_tools_default_timeout_seconds", 120)
        cleaned.setdefault("agent_tools_max_timeout_seconds", 1800)
        cleaned.setdefault("agent_tools_max_output_chars", 120000)
        cleaned.setdefault("agent_tools_smoke_test_on_startup", True)
        cleaned.setdefault("agent_tools_allow_python_venv_install", True)
        cleaned.setdefault("agent_tools_default_python_venv", "agent-tools-default")
        cleaned.setdefault("agent_tools_confirmation_mode", "always")
        if cleaned.get("agent_tools_confirmation_mode") not in {"always", "high_risk_only", "full_access_high_risk_confirm", "full_auto"}:
            cleaned["agent_tools_confirmation_mode"] = "always"
        cleaned.setdefault("agent_tools_auto_reattempt_enabled", True)
        cleaned.setdefault("agent_tools_max_reattempts", 2)
        cleaned.setdefault("agent_tools_allow_infinite_reattempts", False)
        cleaned.setdefault("agent_tools_orchestrator_can_spawn_models", True)
        cleaned.setdefault("agent_tools_model_decides_when_to_use_tools", True)
        cleaned.setdefault("agent_tools_allow_plain_chat_without_tools", True)
        cleaned.setdefault("agent_tools_app_gui_action_routing", True)
        cleaned.setdefault("agent_tools_show_tool_decision_badges", True)
        cleaned.setdefault("assistant_show_live_action_notes", True)
        cleaned.setdefault("assistant_show_live_chain_of_thought", True)
        cleaned.setdefault("assistant_show_live_reasoning_trace", True)
        try:
            cleaned["agent_tools_max_reattempts"] = max(0, min(10, int(cleaned.get("agent_tools_max_reattempts") or 0)))
        except Exception:
            cleaned["agent_tools_max_reattempts"] = 2
        if not isinstance(cleaned.get("agent_tools_allowed_roots"), list):
            cleaned["agent_tools_allowed_roots"] = []
        if cleaned.get("agent_tools_sandbox_mode") not in {"workspace", "local", "docker"}:
            cleaned["agent_tools_sandbox_mode"] = "local"
        cleaned.setdefault("flexavatar_conda_env", "dct-flexavatar")
        cleaned.setdefault("flexavatar_default_device", "cuda:0")
        cleaned.setdefault("flexavatar_job_timeout_seconds", 86400)
        cleaned.setdefault("preferred_external_image_tool", "topaz_photo_ai")
        cleaned.setdefault("global_dataset_enabled", True)
        cleaned.setdefault("global_dataset_root", None)
        cleaned.setdefault("global_dataset_originals_dir", "originals")
        cleaned.setdefault("global_dataset_branches_dir", "branches")
        cleaned.setdefault("global_dataset_variant_dir", "variants")
        cleaned.setdefault("global_dataset_ingest_copy_mode", "copy")
        if cleaned.get("global_dataset_ingest_copy_mode") not in {"copy", "hardlink", "symlink", "reference"}:
            cleaned["global_dataset_ingest_copy_mode"] = "copy"
        cleaned.setdefault("global_dataset_auto_register_downloads", True)
        cleaned.setdefault("global_dataset_auto_link_downloads_to_branch", False)
        cleaned.setdefault("global_dataset_default_branch", "default")
        return cls(**cleaned)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_safe_dict(include_secrets=True), f, indent=2)

    def resolve_api_token(self, provider: str, profile: str | None = None) -> str | None:
        key = str(provider or "").strip().lower().replace("-", "_")
        legacy = {
            "huggingface": self.huggingface_token,
            "hf": self.huggingface_token,
            "openrouter": self.openrouter_token,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "xai": None,
            "x_ai": None,
            "grok": None,
            "runpod": None,
            "vastai": None,
            "vast_ai": None,
            "lambda_labs": None,
            "lambda": None,
            "meshy": None,
            "tripo": None,
            "rodin": None,
            "krea": None,
            "ideogram": None,
        }
        profiles = self.api_token_profiles or {}
        rows = list(profiles.get(key) or profiles.get(key.replace("_", "")) or [])
        normalized_profile = str(profile or "").strip().lower()
        selected: dict[str, Any] | None = None
        if normalized_profile:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                names = [row.get("name"), row.get("label"), row.get("id")]
                if any(str(x or "").strip().lower() == normalized_profile for x in names):
                    selected = row
                    break
        if selected is None:
            for row in rows:
                if isinstance(row, dict) and row.get("default") and row.get("token"):
                    selected = row
                    break
        if selected is None:
            for row in rows:
                if isinstance(row, dict) and row.get("token"):
                    selected = row
                    break
        if selected and selected.get("token") and selected.get("token") != "********":
            return str(selected.get("token"))
        return legacy.get(key) or legacy.get(key.replace("_", ""))

    def to_safe_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        payload = dict(self.__dict__)
        if not include_secrets:
            for secret_key in ["huggingface_token", "openrouter_token", "openai_api_key", "anthropic_api_key"]:
                if payload.get(secret_key):
                    payload[secret_key] = "********"
            masked_profiles: dict[str, list[dict[str, Any]]] = {}
            for provider, rows in (payload.get("api_token_profiles") or {}).items():
                masked_rows: list[dict[str, Any]] = []
                for row in rows or []:
                    if not isinstance(row, dict):
                        continue
                    item = dict(row)
                    if item.get("token"):
                        item["token"] = "********"
                    masked_rows.append(item)
                masked_profiles[provider] = masked_rows
            payload["api_token_profiles"] = masked_profiles
        return payload

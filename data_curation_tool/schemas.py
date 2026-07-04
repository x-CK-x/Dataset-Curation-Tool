from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def _default_if_blank(value: Any, default: str) -> Any:
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return value


class ModelPlacementDefaultsMixin(BaseModel):
    @field_validator("torch_dtype", mode="before", check_fields=False)
    @classmethod
    def _coerce_blank_torch_dtype(cls, value: Any) -> Any:
        return _default_if_blank(value, "auto")

    @field_validator("quantization", mode="before", check_fields=False)
    @classmethod
    def _coerce_blank_quantization(cls, value: Any) -> Any:
        return _default_if_blank(value, "none")

    @field_validator("runtime_engine", mode="before", check_fields=False)
    @classmethod
    def _coerce_blank_runtime_engine(cls, value: Any) -> Any:
        return _default_if_blank(value, "transformers")

    @field_validator("sharding_strategy", mode="before", check_fields=False)
    @classmethod
    def _coerce_blank_sharding_strategy(cls, value: Any) -> Any:
        return _default_if_blank(value, "none")

    @field_validator("device", mode="before", check_fields=False)
    @classmethod
    def _coerce_blank_device(cls, value: Any) -> Any:
        return _default_if_blank(value, "auto")


class MediaType(str, Enum):
    image = "image"
    video = "video"
    animation = "animation"
    audio = "audio"
    model = "model"
    unknown = "unknown"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class DatasetCreate(BaseModel):
    name: str | None = None
    root_path: str
    recursive: bool = True
    read_sidecars: bool = True
    skip_duplicates: bool = True
    tag_profile: str = "e621"
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"
    auto_sync_tag_dictionary: bool = False
    import_workers: int | None = None
    read_embedded_metadata: bool = False
    compute_sha256: bool = True
    compute_phash: bool = False
    probe_dimensions: bool = True
    find_near_duplicates: bool = False
    import_commit_batch_size: int = 256


class DatasetImportMany(BaseModel):
    folders: list[DatasetCreate]


class FolderPickRequest(BaseModel):
    title: str = "Select dataset folder"
    initial_dir: str | None = None


class FilePickRequest(BaseModel):
    title: str = "Select file"
    initial_dir: str | None = None
    filetypes: list[tuple[str, str]] = Field(default_factory=list)


class DatasetInfo(BaseModel):
    id: int
    name: str
    root_path: str
    media_count: int = 0
    created_at: str
    settings: dict[str, Any] = Field(default_factory=dict)


class MediaInfo(BaseModel):
    id: int
    dataset_id: int
    path: str
    relative_path: str
    media_type: MediaType
    ext: str
    width: int | None = None
    height: int | None = None
    size_bytes: int = 0
    sha256: str | None = None
    phash: str | None = None
    tag_string: str = ""
    caption: str = ""
    tags: list[str] = Field(default_factory=list)
    categories: dict[str, str] = Field(default_factory=dict)
    duplicate_of: int | None = None


class MediaPage(BaseModel):
    items: list[MediaInfo]
    total: int
    page: int
    page_size: int


class TagUpdate(BaseModel):
    tag_string: str
    separator: str = ", "
    source: str = "manual"
    save_sidecar: bool = True
    tag_profile: str = "e621"
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"


class CaptionUpdate(BaseModel):
    caption: str
    source: str = "manual"
    save_sidecar: bool = True


class SidecarRefreshRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    tag_profile: str = "e621"


class BulkTagRequest(BaseModel):
    media_ids: list[int]
    operation: Literal["add", "remove", "replace", "set", "copy"]
    tags: list[str] = Field(default_factory=list)
    replace_from: str | None = None
    replace_to: str | None = None
    source_media_id: int | None = None
    separator: str = ", "
    save_sidecars: bool = True
    tag_profile: str = "e621"
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"


class TagPruneRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    implications: dict[str, list[str]] = Field(default_factory=dict)
    dry_run: bool = True


class TagPruneResult(BaseModel):
    media_id: int
    removed: list[str]
    kept: list[str]


class TagMetadataRequest(BaseModel):
    tags: list[str]
    profile_key: str = "e621"


class CustomTagRequest(BaseModel):
    tag: str
    category: str = "custom"
    profile_key: str = "custom"
    note: str | None = None
    color: str | None = None


class TagCategoryRequest(BaseModel):
    profile_key: str = "custom"
    key: str
    label: str | None = None
    css_class: str | None = None
    color: str | None = None


class TagCategoryReapplyRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    profile_key: str = "e621"
    save_sidecars: bool = False


class TagReorderRequest(BaseModel):
    tags: list[str]
    profile_key: str = "e621"
    strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "booru"


class TagDictionaryUrlImportRequest(BaseModel):
    profile_key: str = "e621"
    url: str




class TagProfileUpdateRequest(BaseModel):
    key: str
    label: str | None = None
    categories: list[dict[str, Any]] | None = None
    precedence: list[str] | None = None
    db_export_url: str | None = None


class TagPrecedenceUpdateRequest(BaseModel):
    precedence: list[str]


class TagDictionaryDefaultImportRequest(BaseModel):
    profile_key: str = "e621"
    url: str | None = None




class MetadataFieldInspectRequest(BaseModel):
    media_id: int | None = None
    path: str | None = None
    include_raw: bool = True
    parse_stealth: bool = True


class MetadataFieldComposeRequest(BaseModel):
    media_id: int | None = None
    path: str | None = None
    include_raw: bool = True
    parse_stealth: bool = True
    fields: list[str] = Field(default_factory=list)
    original_delimiter: str = ","
    output_delimiter: str = ", "
    split_strings: bool = True
    keep_parentheses: bool = True
    keep_braces: bool = True
    strip_weight_syntax: bool = False
    normalize_tags: bool = True
    apply_tags: bool = False
    apply_caption: bool = False
    replace_tags: bool = False
    save_sidecars: bool = True
    tag_profile: str = "e621"
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"


class MetadataPathRequest(BaseModel):
    path: str
    include_raw: bool = False
    parse_stealth: bool = True


class MetadataExtractRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    media_id: int | None = None
    dataset_id: int | None = None
    path: str | None = None
    external_paths: list[str] = Field(default_factory=list)
    include_raw: bool = False
    parse_stealth: bool = True
    apply_tags: bool = False
    apply_caption: bool = False
    replace_tags: bool = False
    save_sidecars: bool = True
    tag_source: Literal["positive_prompt", "negative_prompt", "all_prompts", "all_text", "character_prompts", "lora_refs", "lora_triggers", "training_tags", "all"] = "positive_prompt"
    derive_source: str | None = None
    caption_source: Literal["positive_prompt", "negative_prompt", "caption", "summary", "metadata_summary", "character_prompts", "all"] = "positive_prompt"
    tag_profile: str = "e621"
    profile_key: str | None = None
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"


class MetadataApplyRequest(BaseModel):
    media_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    include_raw: bool = False
    apply_tags: bool = True
    apply_caption: bool = False
    replace_tags: bool = False
    save_sidecars: bool = True
    tag_source: Literal["positive_prompt", "negative_prompt", "all_prompts", "all_text", "character_prompts", "lora_refs", "lora_triggers", "training_tags", "all"] = "positive_prompt"
    caption_source: Literal["positive_prompt", "negative_prompt", "caption", "summary", "metadata_summary", "character_prompts", "all"] = "positive_prompt"
    tag_profile: str = "e621"
    profile_key: str | None = None
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"


class MetadataSchemaRequest(BaseModel):
    media_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    path: str | None = None
    external_paths: list[str] = Field(default_factory=list)
    include_raw: bool = True
    parse_stealth: bool = True
    max_items: int = 2000


class MetadataComposeRequest(BaseModel):
    media_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    path: str | None = None
    external_paths: list[str] = Field(default_factory=list)
    selected_paths: list[str] = Field(default_factory=list)
    include_raw: bool = True
    parse_stealth: bool = True
    input_delimiter: str = "auto"
    output_delimiter: str = ", "
    split_to_tags: bool = True
    keep_parentheses: bool = False
    keep_curly_braces: bool = False
    keep_square_brackets: bool = False
    keep_weight_syntax: bool = False
    dedupe: bool = True
    apply_tags: bool = False
    apply_caption: bool = False
    replace_tags: bool = False
    save_sidecars: bool = True
    tag_profile: str = "e621"
    order_strategy: Literal["retain", "booru", "custom_profile", "lora_purpose"] = "retain"


class FrameExtractRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    media_id: int | None = None
    video_path: str | None = None
    output_dir: str | None = None
    target_fps: float | None = 1.0
    fps: float | None = None
    every_n_frames: int | None = None
    start_seconds: float | None = None
    start_time: float | None = None
    end_seconds: float | None = None
    duration: float | None = None
    image_format: Literal["png", "jpg", "webp"] = "png"
    png_compression: int = 0
    attach_to_dataset: bool = False
    attach_as_dataset: bool = False
    dataset_name: str | None = None


class AudioExtractRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    media_id: int | None = None
    video_path: str | None = None
    output_dir: str | None = None
    audio_format: Literal["wav", "flac", "mp3", "m4a", "opus", "copy"] = "wav"
    output_format: Literal["wav", "flac", "mp3", "m4a", "opus", "copy"] | None = None
    format: Literal["wav", "flac", "mp3", "m4a", "opus", "copy"] | None = None
    sample_rate: int | None = None
    channels: int | None = None
    attach_to_dataset: bool = False
    attach_as_dataset: bool = False
    dataset_name: str | None = None


VideoFrameExtractRequest = FrameExtractRequest
VideoAudioExtractRequest = AudioExtractRequest


class KritaOpenRequest(BaseModel):
    media_id: int | None = None
    external_path: str | None = None
    krita_executable: str | None = None
    create_exchange_copy: bool = False


class KritaRefreshRequest(BaseModel):
    media_id: int
    edited_path: str | None = None
    preserve_tags: bool = True
    preserve_caption: bool = True


class KritaExportRequest(BaseModel):
    media_id: int
    output_dir: str | None = None
    include_sidecars: bool = True


class KritaImportRequest(BaseModel):
    source_media_id: int
    edited_path: str
    as_new_media: bool = True
    copy_to_dataset: bool = True
    suffix: str = "_krita_edit"
    preserve_tags: bool = True
    preserve_caption: bool = True


class KritaHandoffRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    output_dir: str | None = None
    copy_sidecars: bool = True
    launch_krita: bool = False
    krita_executable: str | None = None

class GroupRequest(BaseModel):
    dataset_id: int
    name: str
    media_ids: list[int] = Field(default_factory=list)


class GroupInfo(BaseModel):
    id: int
    dataset_id: int
    name: str
    media_count: int
    created_at: str


class ModelRunRequest(ModelPlacementDefaultsMixin):
    dataset_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    model_name: str
    task: Literal["tag", "caption", "classify", "rating", "embed", "segment", "caption_split"] = "tag"
    device: str = "auto"
    batch_size: int = 1
    threshold: float = 0.35
    apply_tags: bool = False
    apply_caption: bool = False
    prompt: str | None = None
    # Multi-GPU placement controls. Default behavior is no sharding: a model is
    # placed on one selected device so other GPUs remain free for other models.
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    device_map: dict[str, Any] | str | None = None
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    tensor_parallel_size: int = 1
    parallel_workers: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class ModelLoadRequest(ModelPlacementDefaultsMixin):
    model_name: str
    device: str = "auto"
    # Mirrors ModelRunRequest placement fields so load-time compatibility
    # problems are surfaced before a user starts a run.
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    device_map: dict[str, Any] | str | None = None
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    tensor_parallel_size: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    name: str
    label: str
    kind: str
    provider: str
    local: bool = True
    optional: bool = False
    description: str = ""
    repo_id: str | None = None
    installed: bool = False
    downloaded: bool = False
    available: bool = True
    capabilities: list[str] = Field(default_factory=list)
    size_gb: float | None = None
    vram_gb: float | None = None
    parameter_count: str | None = None
    precision: str = "auto"
    download_supported: bool = False
    local_path: str | None = None
    context_length: int | None = None
    modality: str = "text"
    recommended_backend: str = "transformers"
    supports_sharding: bool = False
    min_gpus: int = 1
    max_gpus: int | None = None
    cloud: bool = False
    api_model_id: str | None = None




class CustomModelRequest(BaseModel):
    name: str = ""
    label: str = ""
    category: str = ""
    provider: str = "huggingface"
    repo_id: str | None = None
    local_path: str | None = None
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    size_gb: float | None = None
    vram_gb: float | None = None
    parameter_count: str | None = None
    precision: str = "checkpoint-defined"
    modality: str = "image/text"
    recommended_backend: str = "auto"
    download_supported: bool | None = None
    supports_sharding: bool = False
    min_gpus: int = 1
    max_gpus: int | None = None


class ModelDownloadRequest(BaseModel):
    model_name: str | None = None
    repo_id: str | None = None
    revision: str | None = None
    local_dir: str | None = None
    allow_patterns: list[str] = Field(default_factory=list)
    ignore_patterns: list[str] = Field(default_factory=lambda: ["*.msgpack", "*.h5", "*.ot"])
    dry_run: bool = False
    force_download: bool = False
    token: str | None = None
    parallel_downloads: int = 1

class AugmentRequest(BaseModel):
    dataset_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    output_dir: str | None = None
    include_original: bool = True
    augment_only: bool = False
    operations: dict[str, Any] = Field(default_factory=dict)
    attach_to_dataset: bool = False
    output_format: Literal["jpg", "png", "webp"] = "jpg"
    quality: int = 95


class ExternalImageToolRequest(BaseModel):
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    output_dir: str | None = None
    tool_name: str = "topaz_photo_ai"
    mode: Literal["open", "cli"] = "open"
    executable_path: str | None = None
    command_template: str | None = None
    output_suffix: str = "_external_edit"
    attach_to_dataset: bool = False
    wait_for_completion: bool = False
    copy_inputs: bool = True
    auto_discover: bool = True
    save_discovered_path: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class ExternalAppDiscoveryRequest(BaseModel):
    tool_names: list[str] = Field(default_factory=list)
    refresh: bool = True
    deep_scan: bool = False
    save_discovered_paths: bool = True


class OpenLocalPathRequest(BaseModel):
    path: str


class ExportRequest(BaseModel):
    dataset_id: int
    output_dir: str | None = None
    formats: list[Literal["sidecars", "jsonl", "csv", "yolo", "coco"]] = Field(default_factory=lambda: ["jsonl"])
    include_images: bool = False


class DownloadPreset(BaseModel):
    name: str
    source: str
    positive_tags: list[str] = Field(default_factory=list)
    negative_tags: list[str] = Field(default_factory=list)
    logic_query: str = ""
    logic_mode: Literal["boolean_expand", "raw_append", "raw", "append_raw"] = "boolean_expand"
    logic_max_clauses: int = Field(default=64, ge=1, le=512)

    # Output artifact controls.  Defaults preserve existing behavior while letting
    # users opt into post-id filenames and suppress per-file JSON sidecars.
    filename_mode: Literal["hash_original", "post_id", "post_id_original", "original"] = "hash_original"
    write_metadata_json_sidecar: bool = True
    write_tag_txt_sidecar: bool = True

    # Source/content filters. Ratings are source-native short codes where possible
    # (e621/e926: s/q/e). Empty rating list means no rating filter.
    rating_filter: list[str] = Field(default_factory=list)
    allow_animated: bool = True
    allow_video: bool = True
    allow_3d: bool = True
    allow_blender: bool = True
    allow_render: bool = True
    allow_images: bool = True
    allow_audio: bool = True
    allow_other_media: bool = True
    apply_source_blacklists: bool = False
    estimate_total_before_download: bool = False
    options: dict[str, Any] = Field(default_factory=dict)


class DownloadRequest(BaseModel):
    preset_names: list[str] = Field(default_factory=list)
    preset: DownloadPreset | None = None
    # Direct multi-source runs can provide multiple ephemeral presets without
    # requiring users to save each site as a named preset first.
    presets: list[DownloadPreset] = Field(default_factory=list)
    output_dir: str | None = None
    confirmed_authorized: bool = False
    # Top-K/capped mode.  Ignored when download_all_posts=True.
    max_items: int = 100
    # Full-query mode: keep paging until the source returns no more posts or max_pages is reached.
    download_all_posts: bool = False
    # Prevent one post/file from being saved repeatedly when category expansion hits the same post more than once.
    dedupe_across_presets: bool = True
    # Store category/tag membership as JSON index files instead of duplicating media in many tag folders.
    store_membership_index: bool = True
    # Explicit opt-in for legacy category/tag folder copies.  Default is False to avoid duplicate media.
    allow_duplicate_category_files: bool = False

    # Category/profile expansion controls
    tag_profile: str | None = None
    download_all_in_category: bool = False
    download_all_categories: bool = False
    category: str | None = None
    categories: list[str] = Field(default_factory=list)
    category_limit: int = 100
    per_tag_limit: int = 10
    per_category_limit: int | None = None
    category_mode: Literal["preset", "tag_category", "folder"] = "tag_category"
    # Deprecated/legacy: grouping by tag no longer duplicates files unless allow_duplicate_category_files=True.
    group_by_tag: bool = False

    # Date/order controls
    date_from: str | None = None
    date_to: str | None = None
    sort_order: Literal["newest_to_oldest", "oldest_to_newest", "newest", "oldest"] = "newest_to_oldest"

    # Parallelism and pacing controls
    parallel_workers: int = 1
    max_concurrent_downloads: int = 2
    parallel_presets: bool = False
    api_delay_seconds: float | None = None
    file_delay_seconds: float | None = None
    request_timeout_seconds: int | None = None
    max_retries: int | None = None
    retry_backoff_seconds: float | None = None
    max_pages: int | None = None
    start_page: int | None = None
    # Retry/repair mode: redownload media files even when matching output files already exist.
    force_download: bool = False

    # Booru/e621 logic gates. boolean_expand converts OR into multiple deduped API
    # queries using whitespace AND and minus-prefixed NOT. raw_append appends the
    # expression directly to the source's tags parameter for engines that support
    # native logic syntax.
    logic_query: str = ""
    logic_mode: Literal["boolean_expand", "raw_append", "raw", "append_raw"] = "boolean_expand"
    logic_max_clauses: int = Field(default=64, ge=1, le=512)

    # Output artifact controls.  Defaults preserve existing behavior while letting
    # users opt into post-id filenames and suppress per-file JSON sidecars.
    filename_mode: Literal["hash_original", "post_id", "post_id_original", "original"] = "hash_original"
    write_metadata_json_sidecar: bool = True
    write_tag_txt_sidecar: bool = True

    # Source/content filters. Defaults are intentionally permissive: the tool
    # should not silently impose site-like blacklists or hidden exclusions.
    rating_filter: list[str] = Field(default_factory=list)
    allow_animated: bool = True
    allow_video: bool = True
    allow_3d: bool = True
    allow_blender: bool = True
    allow_render: bool = True
    allow_images: bool = True
    allow_audio: bool = True
    allow_other_media: bool = True
    apply_source_blacklists: bool = False
    estimate_total_before_download: bool = False


class ModelChatRequest(ModelPlacementDefaultsMixin):
    model_name: str = "dataset-assistant"
    prompt: str
    dataset_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    external_paths: list[str] = Field(default_factory=list)
    history: list[dict[str, str]] = Field(default_factory=list)
    conversation_id: int | None = None
    conversation_title: str | None = None
    fork_from_message_id: int | None = None
    include_metadata_context: bool = True
    metadata_field_paths: list[str] = Field(default_factory=list)
    metadata_include_raw: bool = False
    use_selected_media: bool = True
    apply_suggested_tags: bool = False
    apply_suggested_caption: bool = False

    # Placement/runtime options. Default is no sharding; select one GPU/device.
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    device_map: dict[str, Any] | str | None = None
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    tensor_parallel_size: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class ModelChatResponse(BaseModel):
    model_name: str
    response: str
    suggested_tags: list[str] = Field(default_factory=list)
    suggested_caption: str | None = None
    applied: dict[str, Any] = Field(default_factory=dict)
    # User-visible planning summary produced by an optional pre-answer planning pass.
    # This is not provider/private hidden chain-of-thought; it is a concise plan/action-notes artifact.
    visible_plan: str | None = None
    action_notes: list[str] = Field(default_factory=list)
    reasoning: dict[str, Any] = Field(default_factory=dict)


class ModelTagSelectionRequest(ModelPlacementDefaultsMixin):
    media_ids: list[int] = Field(default_factory=list)
    dataset_id: int | None = None
    criteria: str = ""
    model_name: str = "dataset-assistant"
    profile_key: str = "e621"
    categories: list[str] = Field(default_factory=list)
    # Global and per-media highlighted/manual candidate tags.
    candidate_tags: list[str] = Field(default_factory=list)
    candidate_tags_by_media: dict[str, list[str]] = Field(default_factory=dict)
    operation: Literal["preview", "remove", "add", "set", "keep_only"] = "preview"
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    device_map: dict[str, Any] | str | None = None
    max_memory: dict[str, str] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    tensor_parallel_size: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class ModelTagSelectionResponse(BaseModel):
    model_name: str
    criteria: str
    selected_tags_by_media: dict[int, list[str]] = Field(default_factory=dict)
    selected_tags: list[str] = Field(default_factory=list)
    applied: dict[str, Any] = Field(default_factory=dict)
    visible_plans_by_media: dict[int, str] = Field(default_factory=dict)
    reasoning: dict[str, Any] = Field(default_factory=dict)


class OrchestrationStep(BaseModel):
    kind: Literal["classify", "tag", "caption", "vlm_check", "llm_review", "tag_select", "apply_tags"]
    model_name: str | None = None
    task: str | None = None
    prompt: str | None = None
    threshold: float = 0.35
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    apply: bool = False
    options: dict[str, Any] = Field(default_factory=dict)


class OrchestrationRequest(BaseModel):
    name: str = "Agentic curation run"
    goal: str = ""
    dataset_id: int | None = None
    media_ids: list[int] = Field(default_factory=list)
    profile_key: str = "e621"
    device_policy: Literal["auto", "cpu", "single_gpu", "multi_gpu", "custom"] = "auto"
    devices: list[str] = Field(default_factory=list)
    max_items: int | None = None
    steps: list[OrchestrationStep] = Field(default_factory=list)
    apply_tags: bool = False
    apply_captions: bool = False
    dry_run: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class OrchestrationTemplate(BaseModel):
    key: str
    label: str
    description: str
    request: OrchestrationRequest


class SqlQuery(BaseModel):
    sql: str
    params: list[Any] = Field(default_factory=list)


class JobInfo(BaseModel):
    id: int
    type: str
    status: JobStatus
    progress: float = 0.0
    message: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    updated_at: str
    finished_at: str | None = None


class SettingsUpdate(BaseModel):
    values: dict[str, Any]


class VoiceCommand(BaseModel):
    text: str
    context: dict[str, Any] = Field(default_factory=dict)




class VoiceTranscriptionRequest(ModelPlacementDefaultsMixin):
    model_name: str | None = None
    language: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    max_memory: dict[str, Any] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    load_policy: Literal["always", "on_demand"] = "on_demand"
    options: dict[str, Any] = Field(default_factory=dict)


class VoiceSynthesisRequest(ModelPlacementDefaultsMixin):
    text: str
    model_name: str | None = None
    voice: str | None = None
    language: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    max_memory: dict[str, Any] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    load_policy: Literal["always", "on_demand"] = "on_demand"
    options: dict[str, Any] = Field(default_factory=dict)


class VoiceModelLoadRequest(ModelPlacementDefaultsMixin):
    kind: Literal["stt", "tts"]
    model_name: str | None = None
    device: str = "auto"
    device_ids: list[int] = Field(default_factory=list)
    sharding_strategy: Literal["none", "auto", "balanced", "balanced_low_0", "sequential", "custom"] = "none"
    max_memory: dict[str, Any] = Field(default_factory=dict)
    torch_dtype: str = "auto"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    runtime_engine: Literal["transformers", "vllm", "sglang", "llama.cpp", "cloud", "auto"] = "transformers"
    options: dict[str, Any] = Field(default_factory=dict)


class DistributedNode(BaseModel):
    name: str
    # Optional HTTP endpoint of a running Data Curation Tool worker, e.g.
    # http://192.168.1.22:7865.  Existing callers that only used base_url still
    # work, while new SSH/SCP-only devices may leave it blank.
    base_url: str = ""
    role: Literal["coordinator", "worker"] = "worker"
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)

    # SSH/SCP connection profile.  The app does not store SSH passwords; use
    # OpenSSH keys, agent forwarding, or OS-level credential handling.
    host: str = ""
    port: int = 22
    username: str = ""
    ssh_executable: str = "ssh"
    scp_executable: str = "scp"
    ssh_key_path: str = ""
    ssh_extra_args: list[str] = Field(default_factory=list)
    scp_extra_args: list[str] = Field(default_factory=list)
    strict_host_key_checking: bool = False
    connect_timeout_seconds: int = 10
    allow_remote_shell: bool = False
    allow_scp: bool = True

    # Remote worker/app layout.  Smaller devices can be marked as lite or
    # downloader-only so future runtime code can avoid loading heavy models.
    platform: Literal["linux", "windows", "macos", "unknown"] = "linux"
    remote_root: str = "~/DataCurationToolRemote"
    remote_project_path: str = ""
    remote_output_dir: str = ""
    conda_env: str = "data-curation-tool"
    python_command: str = "python"
    worker_api_port: int = 7865
    worker_mode: Literal["full", "lite", "downloader-only"] = "full"
    startup_command_template: str = ""
    notes: str = ""


class Health(BaseModel):
    ok: bool = True
    version: str
    time: datetime
    database: str


class AssetMigrationRequest(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
    include: dict[str, bool] = Field(default_factory=dict)
    mode: Literal["move", "copy", "symlink"] = "move"
    conflict: Literal["skip_existing", "replace_if_newer", "replace"] = "skip_existing"
    dry_run: bool = False
    newest_first: bool = True
    delete_source_duplicates: bool = False


class AssetMigrationSettingsRequest(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
    migrate_on_startup: bool = False
    include: dict[str, bool] = Field(default_factory=dict)
    mode: Literal["move", "copy", "symlink"] = "move"
    conflict: Literal["skip_existing", "replace_if_newer", "replace"] = "skip_existing"
    newest_first: bool = True
    delete_source_duplicates: bool = False

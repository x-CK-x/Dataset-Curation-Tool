from __future__ import annotations

from dataclasses import dataclass

from .config import AppSettings
from .database import Database
from .jobs import JobManager
from .models.registry import ModelRegistry
from .paths import AppPaths
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


@dataclass
class AppContext:
    paths: AppPaths
    settings: AppSettings
    db: Database
    jobs: JobManager
    registry: ModelRegistry
    media: MediaService
    metadata: MetadataService
    tags: TagService
    datasets: DatasetService
    models: ModelService
    augment: AugmentationService
    exports: ExportService
    presets: PresetService
    downloads: DownloaderService
    distributed: DistributedService
    voice: VoiceService
    video: VideoService
    krita: KritaService
    orchestration: OrchestrationService
    reference: ReferenceService
    browser: BrowserService
    external_apps: ExternalAppService
    three_d: ThreeDService
    flexavatar: FlexAvatarService
    comfy: ComfyBridgeService
    migration: InstallMigrationService
    code: CodeAssistantService
    cloud: CloudProviderService
    agent_tools: AgentToolsService
    mcp_tools: MCPToolsService
    global_dataset: GlobalDatasetService
    dataset_pipeline: DatasetPipelineService
    pipeline_prep: PipelinePrepService
    character_reference: CharacterReferenceService
    workflows: WorkflowAutomationService
    graph_editor: GraphEditorService
    startup_progress: StartupProgressService
    attention: AttentionVisualizationService
    multimodal: MultimodalDatasetService
    integrity_classifiers: IntegrityClassifierService

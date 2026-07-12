from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5840():
    assert '__version__ = "5.8.48"' in read("data_curation_tool/__init__.py")
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_gallery_thumbnail_prewarm_and_media_performance_path():
    media = read("data_curation_tool/services/media_service.py")
    dataset = read("data_curation_tool/services/dataset_service.py")
    router = read("data_curation_tool/routers/media.py")
    js = read("data_curation_tool/static/app.js")
    assert "ThreadPoolExecutor" in media
    assert "schedule_thumbnail_prewarm" in media
    assert "Image.Resampling.BILINEAR" in media
    assert "self.media_service.schedule_thumbnail_prewarm" in dataset
    assert '@router.post("/thumbnails/prewarm")' in router
    assert "/api/media/thumbnails/prewarm" in js


def test_quick_tag_threshold_device_load_unload_queue_ui():
    js = read("data_curation_tool/static/app.js")
    assert "quickTagThreshold: 0.70" in js
    assert "function stableThresholdValue" in js
    assert "function quickTagThresholdValue" in js
    assert "Queue Load Selected" in js
    assert "Queue Unload Selected" in js
    assert "quick-tag-gpu-controls" in js
    assert "quickTagGpuIds" in js
    assert "quickTagShardingStrategy" in js
    assert "data-preserve-selection" in js
    assert "quickTagMenuInteractionActive" in js


def test_threshold_only_tags_are_applied_and_scores_are_returned():
    service = read("data_curation_tool/services/model_service.py")
    assert "effective_threshold" in service
    assert "quick_tag_surface" in service
    assert "score >= effective_threshold" in service
    assert "candidate_scores_by_media" in service
    assert "applied_tags_by_media" in service
    assert "newly_added" in service


def test_persisted_score_review_card_and_workflow_categories():
    js = read("data_curation_tool/static/app.js")
    css = read("data_curation_tool/static/styles.css")
    graph = read("data_curation_tool/services/graph_editor_service.py")
    assert "Stored Model Prediction Scores for This Media" in js
    assert "advanced_tag_based_multi_model_score_review" in js
    assert "advanced_caption_only_image_dataset_prep" in js
    assert "advanced_ltx_wan_multimodal_caption_export" in js
    assert "advanced_audio_video_sync_caption_review" in js
    assert "workflowCategoryMeta" in js
    assert "workflow-category-chip" in css
    assert "workflow_category" in graph
    assert "advanced_tag_based_multi_model_score_review" in graph
    assert "advanced_caption_only_image_dataset_prep" in graph
    assert "advanced_ltx_wan_multimodal_caption_export" in graph
    assert "advanced_audio_video_sync_caption_review" in graph


def test_workflow_readmes_exist_for_new_advanced_templates():
    for name in [
        "advanced_tag_based_multi_model_score_review",
        "advanced_caption_only_image_dataset_prep",
        "advanced_ltx_wan_multimodal_caption_export",
        "advanced_audio_video_sync_caption_review",
    ]:
        path = ROOT / "docs" / "agentic_workflows" / f"{name}.md"
        assert path.exists(), path
        assert "dry-run" in path.read_text(encoding="utf-8").lower()

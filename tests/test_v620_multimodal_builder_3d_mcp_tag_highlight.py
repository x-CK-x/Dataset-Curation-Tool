from pathlib import Path


def _text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_version_bumped_to_5_8_29():
    import data_curation_tool
    assert data_curation_tool.__version__ == "5.8.48"


def test_multimodal_builder_service_router_and_app_context_are_wired():
    app = _text("data_curation_tool/app.py")
    context = _text("data_curation_tool/context.py")
    router = _text("data_curation_tool/routers/multimodal_dataset_builder.py")
    service = _text("data_curation_tool/services/multimodal_dataset_service.py")
    assert "MultimodalDatasetService" in app
    assert "multimodal_dataset_builder.router" in app
    assert "multimodal: MultimodalDatasetService" in context
    for endpoint in ["/media/probe", "/clips/suggest", "/captions/render", "/datasets/export", "/training/prepare-command", "/pipeline/plan"]:
        assert endpoint in router
    for table in ["media_assets", "clips", "caption_revisions", "audio_annotations", "visual_annotations", "training_samples", "dataset_exports"]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in service


def test_multimodal_export_profiles_cover_ltx_and_wan_targets():
    service = _text("data_curation_tool/services/multimodal_dataset_service.py")
    for token in [
        "ltx_jsonl", "ltx_json", "ltx_csv",
        "wan_musubi_toml", "wan_musubi_jsonl",
        "wan_diffsynth_csv", "wan_simpletuner_json", "ai_toolkit",
        "reference_video", "reference_audio", "video_mask", "audio_mask",
        "frames % 8 == 1", "N*4+1",
    ]:
        assert token in service


def test_requested_3d_provider_rows_are_explicit_and_classified():
    registry = _text("data_curation_tool/models/registry.py")
    three_d = _text("data_curation_tool/services/three_d_service.py")
    for token in ["tripo-p1-smart-mesh-cloud", "hunyuan3d-31-cloud-api", "rodin-hyper3d-production-api"]:
        assert token in registry
    for token in ["tripo_p1_smart_mesh_api", "hunyuan3d_31_cloud_api", "rodin_hyper3d_api"]:
        assert token in three_d
    assert "hosted_saas_api" in three_d
    assert "Use Hunyuan3D 2.x/2.1 rows for local/open-source workflows" in three_d


def test_training_framework_mcps_added_for_multimodal_trainers():
    text = _text("data_curation_tool/services/mcp_tools_service.py")
    for token in ["musubi_tuner", "diffsynth_studio", "simpletuner", "ai_toolkit", "comfyui_training_nodes"]:
        assert token in text
    assert "wan_s2v" in text
    assert "audiovisual_lora" in text
    assert "data_backend_config" in text


def test_frontend_has_multimodal_tab_and_model_tag_highlighter():
    js = _text("data_curation_tool/static/app.js")
    css = _text("data_curation_tool/static/styles.css")
    for token in [
        "Multimodal Dataset Builder",
        "refreshMultimodalBuilder",
        "multimodalDatasetBuilderView",
        "tagScoreHighlightModels",
        "tagScoreModelHighlightControls",
        "model-score-filter-hit",
        "All model rows used on this image",
        "Select Matching Model Tags",
    ]:
        assert token in js
    assert ".tag-chip.model-score-filter-hit" in css
    assert ".model-score-filter-panel" in css

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_version_bumped_to_5837():
    assert '__version__ = "5.8.48"' in read("data_curation_tool/__init__.py")
    assert 'version = "5.8.48"' in read("pyproject.toml")
    assert "v5.8.48" in read("README.md")


def test_quick_tag_model_dropdown_updates_lifecycle_without_tab_switch():
    app = read("data_curation_tool/static/app.js")
    assert "quick-model-lifecycle-mount" in app
    assert "replaceModelLifecycleStrip(lifecycleMount, selectedModel(), true)" in app
    assert "rememberSelect('quickModelSelection', model, preferredQuick?.name || '', false)" in app
    assert "model.addEventListener('change', () => { state.quickModelSelection = model.value || ''; updateQuickLifecycle(true); });" in app
    assert "setTimeout(() => updateQuickLifecycle(false), 0);" in app
    assert "renderNowPreservingState('hard')" in app


def test_completed_model_inference_refreshes_tag_editor_and_predictive_scores():
    app = read("data_curation_tool/static/app.js")
    assert "optimisticallyPatchMediaTagsFromModelJob" in app
    assert "candidate_tags_by_media" in app
    assert "applied_tags_by_media" in app
    assert "candidate_scores_by_media" in app
    assert "completedModelJobScoreTags" in app
    assert "await refreshMediaAfterCompletedModelJobs" in app
    assert "quickModelInferencePreviewPanel" in app
    assert "Prediction values from the last run" in app


def test_backend_returns_candidate_and_applied_tag_maps_and_uses_profile_normalization():
    svc = read("data_curation_tool/services/model_service.py")
    assert "candidate_tags_by_media: dict[int, list[str]]" in svc
    assert "candidate_scores_by_media: dict[int, list[dict[str, Any]]]" in svc
    assert "applied_tags_by_media: dict[int, list[str]]" in svc
    assert "normalize_model_prediction_payload" in svc
    assert "apply_model_tag_aliases" in svc
    assert "apply_model_tag_implications" in svc
    assert "profile_key=profile_key" in svc
    assert "order_strategy=str((request.options or {}).get(\"order_strategy\") or \"retain\")" in svc
    assert '"candidate_tags_by_media": candidate_tags_by_media' in svc
    assert '"candidate_scores_by_media": candidate_scores_by_media' in svc
    assert '"applied_tags_by_media": applied_tags_by_media' in svc


def test_quick_tag_request_sends_selected_profile_alias_implication_and_order_options():
    app = read("data_curation_tool/static/app.js")
    assert "tag_profile: state.tagProfile" in app
    assert "tag_text_mode: activeTagTextMode()" in app
    assert "order_strategy: state.orderingStrategy || 'booru'" in app
    assert "apply_model_tag_aliases: true" in app
    assert "apply_model_tag_implications: true" in app


def test_docs_added_for_v5837():
    assert (ROOT / "docs/V5_8_37_QUICK_TAG_REFRESH_AND_ALIAS_SCORE_SYNC.md").exists()
    assert (ROOT / "docs/wiki/67-Quick-Tag-Refresh-and-Alias-Score-Sync.md").exists()
    assert "67-Quick-Tag-Refresh-and-Alias-Score-Sync.md" in read("docs/wiki/_Sidebar.md")

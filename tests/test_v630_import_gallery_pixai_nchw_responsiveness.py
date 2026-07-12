from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_version_bumped_to_5836():
    assert '__version__ = "5.8.48"' in read("data_curation_tool/__init__.py")
    assert 'version = "5.8.48"' in read("pyproject.toml")
    assert "v5.8.48" in read("README.md")


def test_pixai_onnx_detects_nchw_and_preserves_wd_nhwc_path():
    adapters = read("data_curation_tool/models/adapters.py")
    assert "self.onnx_input_layout" in adapters
    assert 'self.onnx_input_layout = "nchw"' in adapters
    assert 'self.onnx_input_layout = "nhwc"' in adapters
    assert 'self.onnx_input_range = "0_1_normalized" if self.name == "pixai-tagger-v09" else "0_255"' in adapters
    assert 'arr.transpose(2, 0, 1)' in adapters
    assert 'arr[:, :, ::-1]' in adapters  # WD RGB -> BGR path still exists.
    assert 'self.name == "pixai-tagger-v09"' in adapters
    assert 'getattr(resampling, "BILINEAR")' in adapters
    assert 'getattr(resampling, "BICUBIC")' in adapters
    assert 'PixAI\'s DeepGHS ONNX export exposes a channel-first input' in adapters


def test_import_duplicate_skip_seeds_from_all_active_media():
    service = read("data_curation_tool/services/dataset_service.py")
    assert "seeded this map only from the just-created dataset" in service
    assert "SELECT id, sha256 FROM media WHERE active=1 AND sha256 IS NOT NULL" in service
    assert "continue" in service


def test_gallery_page_batches_tags_and_hides_exact_duplicate_rows_by_default():
    service = read("data_curation_tool/services/media_service.py")
    assert "def _rows_to_media" in service
    assert "SELECT media_id, tag, category FROM tags WHERE media_id IN" in service
    assert "SELECT media_id, caption FROM captions WHERE media_id IN" in service
    assert "GROUP BY sha256" in service
    assert "Default Gallery view should not show exact duplicates" in service


def test_native_dialog_runs_in_short_lived_subprocess_with_fallback():
    dialog = read("data_curation_tool/services/dialog_service.py")
    assert "def _subprocess_tk_dialog" in dialog
    assert "subprocess.run" in dialog
    assert "PYTHONIOENCODING" in dialog
    assert "Heavy model load/inference/import jobs can temporarily starve" in dialog
    assert "_inprocess_folder" in dialog


def test_frontend_reduces_passive_media_tab_rerenders_and_shows_picker_feedback():
    app = read("data_curation_tool/static/app.js")
    assert "recentUserInteraction(850)" in app
    assert "completedImportLike" in app
    assert "startupFingerprint" in app
    assert "let shouldRender = false" in app
    assert "state.importPickerBusy = true" in app
    assert "Opening native folder picker" in app
    assert "Waiting on native folder dialog" in app
    assert "state.lastImportJobId" in app
    assert "Import queued as job" in app
    assert "await refreshAll();\n        setTab('Jobs')" not in app
    assert "let shouldRender = renderTabs.includes(state.tab);" not in app


def test_quick_model_dropdown_availability_cues_present():
    app = read("data_curation_tool/static/app.js")
    css = read("data_curation_tool/static/styles.css")
    assert "function modelAvailabilityOptionStyle" in app
    assert "quick-model-status-select" in app
    assert "Loaded models have a green highlight" in app
    assert "model-option-loaded" in css
    assert "legend-dot.loaded" in css
    assert "legend-dot.downloaded" in css


def test_docs_added_for_v5836():
    assert (ROOT / "docs/V5_8_36_IMPORT_GALLERY_RESPONSIVENESS_PIXAI_NCHW.md").exists()
    assert (ROOT / "docs/wiki/66-Import-Gallery-Responsiveness-PixAI-NCHW.md").exists()
    assert "v5.8.48" in read("docs/wiki/Home.md")
    assert "v5.8.48" in read("docs/wiki/README.md")
    assert "66-Import-Gallery-Responsiveness-PixAI-NCHW.md" in read("docs/wiki/_Sidebar.md")

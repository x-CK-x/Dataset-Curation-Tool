from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5842():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')
    assert 'v5.8.48 Update' in read('README.md')


def test_quick_tag_multiselect_queue_uses_persisted_selection_for_actions():
    js = read('data_curation_tool/static/app.js')
    assert 'function quickModelQueueStateValues' in js
    assert 'function persistQuickModelQueueSelection' in js
    assert 'function quickQueueSelectedNames' in js
    assert 'const selectedQueueNames = () => quickQueueSelectedNames(queueSelect, model.value);' in js
    assert 'Queue Download/Update Selected' in js
    assert 'Queue Load Selected' in js
    assert 'Queue Unload Selected' in js
    assert 'Queue Selected Models' in js
    assert 'await queueModelInferenceJobs(names, buildQuickRunBody' in js


def test_quick_tag_loaded_placement_and_cpu_cuda_controls():
    js = read('data_curation_tool/static/app.js')
    service = read('data_curation_tool/services/model_service.py')
    assert 'quickTagUseLoadedPlacement' in js
    assert 'quickTagDeviceMode' in js
    assert "'cpu'" in js and "'cuda'" in js
    assert 'loadedPlacementForQuickModel' in js
    assert 'use_loaded_model_placement' in js
    assert 'def _assert_loaded_placement_compatible' in service
    assert 'opts.get("use_loaded_model_placement")' in service
    assert 'prefer_loaded' in service


def test_quick_tag_queue_scroll_and_menu_selection_are_preserved_live():
    js = read('data_curation_tool/static/app.js')
    assert 'const priorScrollTop = select.scrollTop || 0;' in js
    assert 'select.dataset.selectedValues = JSON.stringify(next)' in js
    assert 'option.dataset.queueSelected' in js
    assert 'const priorScrollTop = list ? list.scrollTop : 0;' in js
    assert 'nextList.scrollTop = priorScrollTop' in js


def test_string_tag_outputs_are_applied_and_scores_are_persisted():
    service = read('data_curation_tool/services/model_service.py')
    media = read('data_curation_tool/services/media_service.py')
    assert 'elif isinstance(item, str):' in service
    assert 'normalization paths emit tags as bare strings' in service
    assert 'score_lookup.get(_score_key(item), 1.0)' in service
    assert 'elif isinstance(item, str):' in media
    assert 'add_pair(item, 1.0, source_key)' in media


def test_booru_reset_endpoint_and_ui_exist():
    router = read('data_curation_tool/routers/media.py')
    js = read('data_curation_tool/static/app.js')
    assert '@router.post("/reset-tags-from-booru")' in router
    assert 'booru_tag_resets' in router
    assert '_fetch_booru_post_by_id' in router
    assert 'booruResetCard' in js
    assert 'Reset This Image Tags From Booru' in js
    assert 'Batch Reset Tags From Booru' in js
    assert '/api/media/reset-tags-from-booru' in js


def test_gallery_thumbnail_concurrency_and_docs():
    media = read('data_curation_tool/services/media_service.py')
    assert 'min(64, (os.cpu_count() or 4) * 2)' in media
    assert 'max_side: int = 160' in media
    assert (ROOT / 'docs' / 'V5_8_42_QUICK_TAG_SELECTION_LOADED_PLACEMENT_BOORU_RESET.md').exists()
    assert (ROOT / 'docs' / 'wiki' / '72-Quick-Tag-Selection-Loaded-Placement-Booru-Reset.md').exists()

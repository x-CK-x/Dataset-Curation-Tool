from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5843():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')
    assert 'v5.8.48 Update' in read('README.md')


def test_nonblocking_thumbnail_hydration_and_gpu_attempt():
    media = read('data_curation_tool/services/media_service.py')
    router = read('data_curation_tool/routers/media.py')
    js = read('data_curation_tool/static/app.js')
    assert '_try_gpu_thumbnail_for_path' in media
    assert 'cv2.cuda' in media
    assert 'def thumbnail_status' in router
    assert 'fast: bool = Query(False)' in router
    assert '_thumbnail_placeholder_svg' in router
    assert 'scheduleThumbnailHydration' in js
    assert 'data-thumbnail-media-id' in js
    assert '/api/media/thumbnails/status' in js
    assert 'thumbnail?fast=1' in js


def test_quick_tag_multiselect_can_deselect_and_queue_all_selected():
    js = read('data_curation_tool/static/app.js')
    assert 'function quickModelQueueDomSelectedValues' in js
    assert 'persistQuickModelQueueSelection(select, quickModelQueueDomSelectedValues(select))' in js
    assert 'Let the browser own native multiple-select behavior' in js
    assert 'Ctrl/Cmd-click toggles models' in js
    assert 'const selectedQueueNames = () => quickQueueSelectedNames(queueSelect, model.value);' in js


def test_booru_reset_is_job_backed_and_visible():
    router = read('data_curation_tool/routers/media.py')
    js = read('data_curation_tool/static/app.js')
    assert '@router.post("/reset-tags-from-booru/job")' in router
    assert 'booru_tag_reset' in router
    assert 'watchBooruResetJob' in js
    assert "/api/media/reset-tags-from-booru/job" in js
    assert 'Queued booru tag reset' in js


def test_integrity_classifier_service_router_and_ui():
    service = read('data_curation_tool/services/integrity_classifier_service.py')
    router = read('data_curation_tool/routers/integrity_classifiers.py')
    app = read('data_curation_tool/app.py')
    js = read('data_curation_tool/static/app.js')
    assert 'class IntegrityClassifierService' in service
    assert 'efficientnet_v2_m' in service
    assert 'onnxruntime' in service
    assert '@router.post("/run")' in router
    assert 'integrity_classifiers.router' in app
    assert 'integrityClassifierModelCard' in js
    assert 'integrityRunCard' in js
    assert 'Nightshade / Glaze' in js


def test_docs_exist():
    assert (ROOT / 'docs' / 'V5_8_43_THUMBNAILS_MULTISELECT_BOORU_RESET_INTEGRITY.md').exists()
    assert (ROOT / 'docs' / 'wiki' / '73-Thumbnails-Multiselect-Booru-Reset-Integrity.md').exists()

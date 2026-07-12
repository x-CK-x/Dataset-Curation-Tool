from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_5839():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')
    assert 'v5.8.48 Update' in read('README.md')


def test_models_tab_live_card_patchers_present():
    js = read('data_curation_tool/static/app.js')
    assert 'function syncCatalogLoadedStatusFromStatuses' in js
    assert 'function patchModelsTabLive' in js
    assert 'function modelRuntimeSignature' in js
    assert 'data-model-card-name' in js
    assert 'data-model-catalog-scroll' in js
    assert 'patchModelsTabLive({ reorder: true })' in js
    assert 'patchModelsTabLive({ reorder: false })' in js


def test_resource_status_merges_actual_driver_and_torch_memory():
    service = read('data_curation_tool/services/model_service.py')
    assert 'torch_snapshot = self._cuda_memory_snapshot()' in service
    assert 'torch_by_index' in service
    assert '"actual_used_memory_gb"' in service
    assert '"actual_free_memory_gb"' in service
    assert '"actual_memory_source"' in service
    assert '"torch_allocated_gb"' in service
    assert '"torch_reserved_gb"' in service
    assert '"resource_after"] = self.model_resource_status()' in service


def test_frontend_resource_panel_shows_actual_vram_and_gallery_is_resilient():
    js = read('data_curation_tool/static/app.js')
    css = read('data_curation_tool/static/styles.css')
    assert 'actual used' in js
    assert 'torch allocated' in js
    assert 'state.mediaLoadError' in js
    assert 'media load failed; preserving existing gallery state' in js
    assert 'background status/media/model poll failed; UI state preserved' in js
    assert '.model-resource-actual' in css
    assert '.notice.bad-text' in css


def test_runtime_planning_context_endpoint_for_orchestrators():
    service = read('data_curation_tool/services/model_service.py')
    routers = read('data_curation_tool/routers/models.py')
    assert 'def model_runtime_planning_context' in service
    assert 'strict_gpu_assignment' in service
    assert 'assistant_can_request_sharding' in service
    assert '@router.get("/runtime-planning-context")' in routers
    assert 'runtime_planning_context' in routers
    assert 'runtime_resources' in routers


def test_docs_present():
    assert 'Live Model Cards, VRAM Visibility, and Gallery Resilience' in read('docs/V5_8_39_LIVE_MODEL_CARD_VRAM_GALLERY_RESILIENCE.md')
    assert 'Live Model Card, VRAM, and Gallery Resilience Fix' in read('docs/wiki/69-Live-Model-Card-VRAM-Gallery-Resilience.md')
    assert '69-Live-Model-Card-VRAM-Gallery-Resilience.md' in read('docs/wiki/_Sidebar.md')

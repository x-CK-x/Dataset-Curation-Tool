from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_5838():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')
    assert 'v5.8.48 Update' in read('README.md')


def test_backend_resource_status_includes_system_ram_and_batch_queue_endpoint():
    service = read('data_curation_tool/services/model_service.py')
    routers = read('data_curation_tool/routers/models.py')
    assert 'def _system_memory_snapshot' in service
    assert '"system_ram": self._system_memory_snapshot()' in service
    assert 'class ModelQueueRunsRequest' in routers
    assert '@router.post("/queue-runs")' in routers
    assert 'c.jobs.submit_with_job_id("model_inference"' in routers


def test_frontend_live_runtime_poll_and_dom_patchers_present():
    js = read('data_curation_tool/static/app.js')
    assert 'pollModelRuntimeLive' in js
    assert "api('/api/models/resource-status'" in js
    assert 'updateModelResourceDom' in js
    assert 'refreshModelOptionsInPlace' in js
    assert 'setInterval(() => { pollModelRuntimeLive()' in js
    assert 'data-model-resource-panel' in js
    assert 'data-model-live-options' in js


def test_quick_tag_queue_and_agent_queue_ui_present():
    js = read('data_curation_tool/static/app.js')
    assert 'Queue multiple quick tag/rating models' in js
    assert 'Quick Tag Inference Queue' in js
    assert 'queueModelInferenceJobs' in js
    assert "api('/api/models/queue-runs'" in js
    assert 'Live Model Queue / Agent-Orchestrated Model Jobs' in js
    assert 'All Model/Agent Job Queue' in js
    assert 'Agent Tools' in js and 'queued_surface' in js


def test_queue_css_and_docs_present():
    css = read('data_curation_tool/static/styles.css')
    assert '.model-job-queue-panel' in css
    assert '.model-queue-row' in css
    assert '.progress-ring.queue-ring' in css
    assert 'Live Model Runtime Queues' in read('docs/wiki/68-Live-Model-Runtime-Queues.md')
    assert 'V5_8_38_LIVE_MODEL_RUNTIME_QUEUES' in '\n'.join(p.name for p in (ROOT / 'docs').glob('V5_8_38*'))

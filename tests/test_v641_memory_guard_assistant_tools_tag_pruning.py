from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_version_bumped_to_5848():
    assert '__version__ = "5.8.48"' in read('data_curation_tool/__init__.py')
    assert 'version = "5.8.48"' in read('pyproject.toml')


def test_system_ram_guard_and_cpu_offload_default_are_present():
    cfg = read('data_curation_tool/config.py')
    svc = read('data_curation_tool/services/model_service.py')
    assert 'model_vram_auto_cpu_offload_enabled: bool = False' in cfg
    assert 'model_vram_skip_cpu_offload_when_system_ram_percent' in cfg
    assert 'model_system_ram_cleanup_warning_percent' in cfg
    assert 'model_chat_storage_max_context_chars' in cfg
    assert 'def _system_ram_guard' in svc
    assert 'CPU offload was skipped because moving model weights/KV state into system RAM could exhaust RAM' in svc
    assert 'auto_cpu_offload_enabled": self._settings_bool("model_vram_auto_cpu_offload_enabled", False)' in svc


def test_chat_payload_storage_is_bounded():
    svc = read('data_curation_tool/services/model_service.py')
    assert 'def _compact_json_for_storage' in svc
    assert 'Structured chat payload was compacted to prevent long-running assistant memory growth' in svc
    assert 'substr(context_json, 1, ?)' in svc
    assert 'def _prune_conversation_payloads' in svc
    assert 'fetches rows one at a time' in svc
    assert 'conversation_payload_prune' in svc
    assert 'system_ram_guard' in svc


def test_assistant_lora_rules_and_tag_edit_application_are_wired():
    svc = read('data_curation_tool/services/model_service.py')
    app = read('data_curation_tool/app.py')
    js = read('data_curation_tool/static/app.js')
    assert 'model_service.pipeline_prep = pipeline_prep_service' in app
    assert 'def _lora_rule_context_from_options' in svc
    assert 'DATASET / LORA RULE CONTEXT FROM THIS TOOL' in svc
    assert 'def _apply_assistant_tag_edit_directives' in svc
    assert 'assistant_apply_tag_edits' in js
    assert 'apply assistant tag edits/pruning' in js
    assert 'lora_target_model' in js
    assert 'dataset_pipeline_rules' in js


def test_agent_model_queue_tools_are_available_and_visible():
    tools = read('data_curation_tool/services/agent_tools_service.py')
    app = read('data_curation_tool/app.py')
    js = read('data_curation_tool/static/app.js')
    assert 'AgentToolsService(paths, app_settings, model_service, browser=browser_service, jobs=job_manager)' in app
    for marker in ['queue_model_load', 'queue_model_inference', 'queue_model_unload', 'wait_for_jobs']:
        assert marker in tools
    assert 'agent_model_' in js
    assert 'agent_model_inference' in tools
    assert 'Approved assistant tool/model queue plan started' in js


def test_condensed_memory_is_not_truncated_in_ui():
    js = read('data_curation_tool/static/app.js')
    css = read('data_curation_tool/static/styles.css')
    assert 'memory-summary-log' in js
    assert 'Copy Memory' in js
    assert 'Download Memory' in js
    assert '.memory-summary-log' in css
    assert 'max-height: min(70vh, 920px)' in css

from __future__ import annotations

from pathlib import Path

from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.services.model_service import _extract_tags


def test_florence_and_instructblip_rows_have_concrete_adapters():
    registry = ModelRegistry(Path('/tmp/dct-v553-models'))
    expected = {
        'florence-2-base': 'HFFlorence2Adapter',
        'florence2-curation-base': 'HFFlorence2Adapter',
        'florence2-curation-large': 'HFFlorence2Adapter',
        'florence-2-large-multitask': 'HFFlorence2Adapter',
        'instructblip-vicuna-7b': 'HFInstructBLIPAdapter',
    }
    for name, adapter_cls in expected.items():
        record = registry.get_record(name)
        assert record.adapter.__class__.__name__ == adapter_cls
        assert 'vlm' in record.capabilities or 'caption' in record.capabilities


def test_tag_extractor_accepts_json_structured_vlm_responses():
    assert _extract_tags('{"tags": ["blue eyes", "rating:safe"]}') == ['blue_eyes', 'rating:safe']
    assert _extract_tags('```json\n{"selected_tags": ["cat", "smile"]}\n```') == ['cat', 'smile']
    assert _extract_tags('tags: long_hair, solo') == ['long_hair', 'solo']


def test_unload_lifecycle_state_is_purple_and_active():
    lifecycle = Path('data_curation_tool/services/model_lifecycle.py').read_text(encoding='utf-8')
    styles = Path('data_curation_tool/static/styles.css').read_text(encoding='utf-8')
    app_js = Path('data_curation_tool/static/app.js').read_text(encoding='utf-8')
    service = Path('data_curation_tool/services/model_service.py').read_text(encoding='utf-8')
    assert '"unloading"' in lifecycle
    assert '.stage-pill.unloading' in styles
    assert '#a855f7' in styles
    assert "'unloading'" in app_js
    assert 'reset(name, "load"' in service
    assert 'reset(name, "inference"' in service


def test_select_all_and_existing_tag_fallbacks_are_in_service():
    source = Path('data_curation_tool/services/model_service.py').read_text(encoding='utf-8')
    assert 'criteria_requests_select_all' in source
    assert 'match_existing_from_text' in source
    assert 'structured extraction' in source

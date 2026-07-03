from __future__ import annotations

import json
from pathlib import Path

from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.models.adapters import _context_to_text
from data_curation_tool.services.model_service import _extract_tags


def _touch_nonzero(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_florence_local_snapshot_with_weights_is_downloaded_with_support_warning(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    record = registry.get_record("florence-2-large-multitask")
    local = tmp_path / "models" / "hf" / "microsoft--Florence-2-large"
    _touch_nonzero(local / "config.json", "{}")
    _touch_nonzero(local / "model.safetensors", "not empty")

    assert record.is_downloaded(registry.model_root, registry.external_model_roots) is True
    row = record.to_dict(registry.model_root, registry.external_model_roots)
    issues = " ".join(row["download_integrity"]["issues"])
    warnings = " ".join(row["download_integrity"].get("warnings") or [])
    assert issues == ""
    assert "processing_florence2.py" in warnings
    assert row["downloaded"] is True



def test_resolve_model_path_prefers_repairable_partial_snapshot(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    local = tmp_path / "models" / "hf" / "microsoft--Florence-2-large"
    _touch_nonzero(local / "config.json", "{}")
    _touch_nonzero(local / "model.safetensors", "not empty")
    record = registry.get_record("florence-2-large-multitask")

    # The folder is downloaded because weights are present, and load_model should
    # still hand it to the adapter so the adapter can repair missing support files.
    assert record.is_downloaded(registry.model_root, registry.external_model_roots) is True
    assert registry.resolve_model_path(record) == str(local)

def test_florence_complete_local_snapshot_is_downloaded(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    record = registry.get_record("florence-2-large-multitask")
    local = tmp_path / "models" / "hf" / "microsoft--Florence-2-large"
    for name in ["config.json", "model.safetensors", "processing_florence2.py", "configuration_florence2.py", "modeling_florence2.py"]:
        _touch_nonzero(local / name, "content")

    assert record.complete_local_dir(registry.model_root, registry.external_model_roots) == local
    row = record.to_dict(registry.model_root, registry.external_model_roots)
    assert row["downloaded"] is True
    assert row["download_integrity"]["issues"] == []


def test_lfm_and_gemma_snapshots_without_chat_template_are_downloaded_with_warning(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    record = registry.get_record("lfm25-vl-16b")
    local = tmp_path / "models" / "hf" / "LiquidAI--LFM2.5-VL-1.6B-Extract"
    _touch_nonzero(local / "config.json", "{}")
    _touch_nonzero(local / "model.safetensors", "weights")

    assert record.is_downloaded(registry.model_root, registry.external_model_roots) is True
    assert record.local_integrity_issues(local) == []
    assert any("chat template" in warning for warning in record.local_support_warnings(local))

    _touch_nonzero(local / "chat_template.jinja", "{{ messages }}")
    assert record.is_downloaded(registry.model_root, registry.external_model_roots) is True
    assert record.local_support_warnings(local) == []


def test_default_hf_download_allow_patterns_keep_remote_code_and_templates():
    registry = ModelRegistry(Path("/tmp/dct-v554-models"))
    for name in ["florence-2-large-multitask", "florence2-curation-large", "lfm25-vl-16b", "gemma-4-e2b-it"]:
        record = registry.get_record(name)
        assert "*.py" in record.allow_patterns
        assert "chat_template*" in record.allow_patterns
        assert "*.jinja" in record.allow_patterns


def test_chat_context_includes_history_metadata_and_predictions():
    text = _context_to_text({
        "dataset": {"name": "demo", "root_path": "C:/data"},
        "media": [{"id": 7, "relative_path": "a.png", "tags": ["solo", "smile"], "caption": "a caption", "model_predictions": [{"model_name": "jtp3"}], "annotations": [{"label": "face"}]}],
        "generation_metadata": [{"prompt": "example", "steps": 20}],
        "history": [{"role": "user", "content": "previous question"}, {"role": "assistant", "content": "previous answer"}],
    })
    assert "Dataset: demo" in text
    assert "tags=solo, smile" in text
    assert "recent model predictions" in text
    assert "Metadata #1" in text
    assert "Conversation history" in text
    assert "previous question" in text


def test_extended_tag_extraction_keys_for_conversation_and_tag_ops():
    assert _extract_tags('{"selected_existing_tags": ["blue eyes", "solo"]}') == ["blue_eyes", "solo"]
    assert _extract_tags('{"present_tags": ["smile"], "caption": "ignored"}') == ["smile"]
    assert _extract_tags('selected existing tags: cat, tail') == ["cat", "tail"]


def test_frontend_exposes_conversational_assistant_controls():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Chat About Current Target" in app_js
    assert "/api/models/chat" in app_js
    assert "apply tags from response" in app_js
    assert "Conversation mode uses the same selected image/data" in app_js

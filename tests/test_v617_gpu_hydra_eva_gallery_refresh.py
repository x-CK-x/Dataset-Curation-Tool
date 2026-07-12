from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__
from data_curation_tool.models.registry import ModelRegistry

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_5_8_25():
    assert __version__ == "5.8.48"


def test_hydra_is_local_tagger_not_default_mcp_catalog_row(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    row = registry.get_record("redrocket-hydra-3-5")
    caps = set(row.capabilities)
    assert row.kind == "tagger"
    assert "mcp" not in caps
    assert "model_offload" not in caps
    assert "local_inference" in caps
    assert row.recommended_backend == "native_hydra_3_5_local"


def test_legacy_eva_attention_qk_norm_compatibility_defaults_present():
    source = read("data_curation_tool/models/adapters.py")
    assert '"q_norm": "__identity__"' in source
    assert '"k_norm": "__identity__"' in source
    assert '"qk_norm": False' in source
    assert "attempts <= 32" in source


def test_legacy_tagger_cuda_assignment_is_strict_and_onnx_device_id_is_used():
    source = read("data_curation_tool/models/adapters.py")
    assert "CUDAExecutionProvider is not available" in source
    assert 'provider_options.append({"device_id": cuda_idx})' in source
    assert "could not be moved there" in source
    assert "self.load(device=requested_device" in source


def test_runtime_device_prefers_explicit_device_ids_over_stale_cpu_loaded_placement():
    source = read("data_curation_tool/services/model_service.py")
    assert "Do not let a previously CPU-offloaded or stale placement override" in source
    assert "return f\"cuda:{ids[0]}\"" in source


def test_model_catalog_uses_short_cache_for_ui_interactions():
    source = read("data_curation_tool/services/model_service.py")
    assert "_catalog_cache_rows" in source
    assert "_static_model_catalog_rows" in source
    assert "cache the static" in source.lower()


def test_frontend_refreshes_active_gallery_and_uses_distinct_model_score_palette():
    js = read("data_curation_tool/static/app.js")
    assert "refreshTabDataOnEnter" in js
    assert "const MODEL_SCORE_HUE_PALETTE" in js
    assert "Gallery', 'Tag Editor', 'Batch Tags'" in js or "'Gallery', 'Tag Editor'" in js
    assert "await loadMedia({ force: true }).catch(() => null);" in js


def test_models_endpoint_supports_force_refresh():
    source = read("data_curation_tool/routers/models.py")
    assert "def list_models(request: Request, force: bool = False)" in source
    assert "list_models(force=force)" in source

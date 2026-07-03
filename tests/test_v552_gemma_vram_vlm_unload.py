from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths


def _gpu_payload(total=24.0, free=16.8):
    return {
        "torch_available": True,
        "cuda_available": True,
        "devices": [
            {
                "id": "cuda:0",
                "index": 0,
                "name": "RTX 3090",
                "total_memory_gb": total,
                "free_memory_gb": free,
                "used_memory_gb": max(0.0, total - free),
                "torch_ready": True,
            }
        ],
        "warnings": [],
    }


def test_gemma_runtime_vram_profiles_are_used_for_estimates_and_dropdown_metadata(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DCT_SKIP_STARTUP_TAG_SYNC", "1")
    import data_curation_tool.services.model_service as model_service_module

    monkeypatch.setattr(model_service_module, "detect_devices", lambda: _gpu_payload(total=24.0, free=16.8))
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    app = create_app(paths)
    client = TestClient(app)

    # Driver free is intentionally lower than the app reservation budget. The
    # default should warn, not hard-fail, because Windows/WDDM driver-free values
    # can be stale/conservative compared with user-observed idle GPUs.
    e4 = client.post("/api/models/placement/plan", json={
        "model_name": "gemma-4-e4b-it",
        "device": "cuda:0",
        "device_ids": [0],
        "sharding_strategy": "none",
        "torch_dtype": "auto",
        "quantization": "none",
    }).json()
    assert e4["estimated_vram_gb"] == 17.9
    assert e4["can_load"] is True
    assert e4["devices"][0]["driver_free_memory_warning"] is True

    twelve = client.post("/api/models/placement/plan", json={
        "model_name": "gemma-4-12b-it",
        "device": "cuda:0",
        "device_ids": [0],
        "sharding_strategy": "none",
        "torch_dtype": "auto",
        "quantization": "none",
    }).json()
    assert twelve["can_load"] is False
    assert twelve["estimated_vram_gb"] == 26.7
    assert twelve["runtime_vram_profiles"]["8bit"] == 13.4
    assert "8bit" in " ".join(twelve["errors"])

    twelve_8 = client.post("/api/models/placement/plan", json={
        "model_name": "gemma-4-12b-it",
        "device": "cuda:0",
        "device_ids": [0],
        "sharding_strategy": "none",
        "torch_dtype": "auto",
        "quantization": "8bit",
    }).json()
    assert twelve_8["can_load"] is True
    assert twelve_8["estimated_vram_gb"] == 13.4

    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "function modelMemorySummary" in app_js
    assert "runtime_vram_profiles" in app_js
    assert "Memory estimate" in app_js


def test_gemma_download_patterns_include_chat_template_jinja():
    registry = ModelRegistry(Path("/tmp/dct-v552-models"))
    row = registry.get_record("gemma-4-e2b-it")
    assert "chat_template*" in row.allow_patterns
    assert "*.jinja" in row.allow_patterns


def test_hf_vlm_adapter_has_gemma4_any_to_any_and_multimodal_loader_paths():
    source = Path("data_curation_tool/models/adapters.py").read_text(encoding="utf-8")
    assert "any-to-any" in source
    assert "AutoModelForMultimodalLM" in source
    assert "chat_template.jinja" in source
    assert "<|image|>" in source


def test_unload_clears_long_lived_adapter_gpu_references():
    registry = ModelRegistry(Path("/tmp/dct-v552-models"))
    adapter = registry.get_record("gemma-4-e2b-it").adapter

    class DummyModel:
        def __init__(self):
            self.moved_to = None
        def to(self, device):
            self.moved_to = device
            return self

    class DummyPipeline:
        def __init__(self):
            self.model = DummyModel()

    adapter.model = DummyModel()
    adapter.processor = object()
    adapter.pipeline = DummyPipeline()
    registry._loaded["gemma-4-e2b-it"] = adapter
    registry._loaded_meta["gemma-4-e2b-it"] = {"model_name": "gemma-4-e2b-it", "device": "cuda:0"}

    result = registry.unload("gemma-4-e2b-it")
    assert result["unloaded"] == ["gemma-4-e2b-it"]
    assert adapter.model is None
    assert adapter.pipeline is None
    assert adapter.processor is None
    assert not registry.is_loaded("gemma-4-e2b-it")

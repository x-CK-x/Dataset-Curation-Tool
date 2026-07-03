from __future__ import annotations

from pathlib import Path

from data_curation_tool.config import AppSettings
from data_curation_tool.models.registry import ModelRegistry


class DummyAdapter:
    def __init__(self):
        self.model = self
        self.device = "cuda:0"
        self.moves: list[str] = []

    def to(self, device: str):
        self.device = str(device)
        self.moves.append(str(device))
        return self

    def is_available(self) -> bool:
        return True

    def chat(self, prompt: str, context=None, device="auto", **kwargs):
        return {"response": "ok", "kwargs": kwargs}


def test_vram_memory_settings_defaults_exist():
    settings = AppSettings()
    assert settings.model_vram_cleanup_after_inference is True
    assert settings.model_vram_auto_cpu_offload_enabled is True
    assert settings.model_vram_auto_cpu_offload_policy == "on_pressure"
    assert 0.5 <= settings.model_vram_auto_cpu_offload_threshold <= 0.98
    assert settings.model_vram_disable_generation_cache_on_pressure is True


def test_registry_cpu_offload_and_reactivation_metadata(tmp_path: Path):
    reg = ModelRegistry(tmp_path / "models")
    adapter = DummyAdapter()
    reg._loaded["dummy"] = adapter
    reg._loaded_meta["dummy"] = {"model_name": "dummy", "device": "cuda:0", "per_gpu_reserved_gb": {"0": 1.0}, "loaded": True}

    off = reg.offload_to_cpu("dummy", reason="test pressure")
    assert off["count"] == 1
    assert adapter.device == "cpu"
    assert reg.loaded_placement("dummy")["offloaded_to_cpu"] is True

    react = reg.reactivate_from_cpu("dummy", device="cuda:0")
    assert react["reactivated"] is True
    assert adapter.device == "cuda:0"
    assert reg.loaded_placement("dummy")["offloaded_to_cpu"] is False


def test_v571_frontend_and_backend_hooks_present():
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    router = Path("data_curation_tool/routers/models.py").read_text(encoding="utf-8")
    service = Path("data_curation_tool/services/model_service.py").read_text(encoding="utf-8")
    registry = Path("data_curation_tool/models/registry.py").read_text(encoding="utf-8")

    assert "Model VRAM / Long Chat Memory Management" in app_js
    assert "/memory/cleanup" in router
    assert "offload-cpu" in router
    assert "_registry_chat_with_vram_guard" in service
    assert "model_vram_disable_generation_cache_on_pressure" in service
    assert "def offload_to_cpu" in registry
    assert "def reactivate_from_cpu" in registry

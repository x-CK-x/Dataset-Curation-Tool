from __future__ import annotations

from pathlib import Path

from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DownloadRequest, ModelChatRequest, ModelRunRequest
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.services.downloader_service import DownloaderService, source_definitions
from data_curation_tool.services.preset_service import PresetService


def test_v59_download_request_and_source_capabilities():
    req = DownloadRequest(
        confirmed_authorized=True,
        download_all_categories=True,
        categories=["character", "artist"],
        date_from="2026-01-01",
        date_to="2026-01-31",
        sort_order="oldest_to_newest",
        max_concurrent_downloads=4,
        parallel_presets=True,
    )
    assert req.download_all_categories is True
    assert req.categories == ["character", "artist"]
    assert req.sort_order == "oldest_to_newest"
    assert req.max_concurrent_downloads == 4
    assert all(s["supports_date_range"] and s["supports_sort_order"] for s in source_definitions())


def test_v59_downloader_expands_category_presets(tmp_path: Path):
    db = Database(tmp_path / "app.sqlite3")
    presets = PresetService(db, tmp_path / "presets")
    svc = DownloaderService(db, presets)
    expanded = svc._expand_category_presets(
        [{"name": "base", "source": "e621", "positive_tags": ["solo"], "negative_tags": [], "options": {}}],
        DownloadRequest(confirmed_authorized=True, download_all_categories=True, categories=["character", "artist"], category_mode="folder"),
    )
    assert [p["options"]["category"] for p in expanded] == ["character", "artist"]
    assert "character" in expanded[0]["name"]


def test_v59_model_registry_has_large_local_and_cloud_rows(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    models = {m["name"]: m for m in registry.list()}
    for name in ["gemma-4-12b-it", "gemma-4-31b-it", "qwen3-vl-30b-a3b", "qwen2.5-72b-instruct"]:
        assert models[name]["download_supported"] is True
        assert models[name]["supports_sharding"] is True
        assert models[name]["max_gpus"] == 6
    assert models["openai-gpt-5.5"]["cloud"] is True
    assert models["openrouter-kimi-k27-code"]["cloud"] is True


def test_v59_model_run_and_chat_accept_gpu_placement():
    run = ModelRunRequest(model_name="dataset-assistant", device="cuda:0", device_ids=[0, 1, 2], sharding_strategy="auto", torch_dtype="float16", quantization="4bit", parallel_workers=3)
    chat = ModelChatRequest(prompt="help", model_name="dataset-assistant", device_ids=[3, 4], sharding_strategy="balanced", max_memory={"3": "23GiB"})
    assert run.device_ids == [0, 1, 2]
    assert run.sharding_strategy == "auto"
    assert chat.sharding_strategy == "balanced"
    assert chat.max_memory == {"3": "23GiB"}

from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.schemas import DownloadRequest, ModelChatRequest, ModelRunRequest


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_v59_download_schema_supports_category_date_order_parallel():
    req = DownloadRequest(
        preset_names=["sample"],
        confirmed_authorized=True,
        download_all_in_category=True,
        categories=["character", "artist"],
        date_from="2026-01-01",
        date_to="2026-06-01",
        sort_order="oldest_to_newest",
        parallel_workers=6,
        parallel_presets=True,
        per_tag_limit=3,
    )
    assert req.categories == ["character", "artist"]
    assert req.sort_order == "oldest_to_newest"
    assert req.parallel_workers == 6


def test_v59_models_endpoint_exposes_new_local_cloud_and_sharding_rows(tmp_path: Path):
    client = _client(tmp_path)
    models = {m["name"]: m for m in client.get("/api/models").json()}
    for key in ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "qwen3.6-35b-a3b", "openai-gpt-5.5", "anthropic-claude-fable-5", "openrouter-auto"]:
        assert key in models
    assert models["gemma-4-31b-it"]["supports_sharding"] is True
    assert models["gemma-4-31b-it"]["max_gpus"] == 6
    assert models["openai-gpt-5.5"]["cloud"] is True
    assert models["anthropic-claude-fable-5"]["provider"] == "anthropic"


def test_v59_model_request_schemas_accept_device_placement():
    run = ModelRunRequest(
        model_name="gemma-4-31b-it",
        media_ids=[1, 2],
        device="cuda:0,cuda:1,cuda:2",
        device_ids=[0, 1, 2],
        sharding_strategy="balanced",
        max_memory={"0": "23GiB", "1": "23GiB", "2": "23GiB"},
        torch_dtype="bfloat16",
        quantization="4bit",
        parallel_workers=3,
    )
    assert run.sharding_strategy == "balanced"
    assert run.device_ids == [0, 1, 2]
    chat = ModelChatRequest(
        model_name="openai-gpt-5.5",
        prompt="suggest tags",
        device_ids=[0],
        sharding_strategy="none",
        runtime_engine="cloud",
    )
    assert chat.runtime_engine == "cloud"


def test_v59_hud_contains_download_and_runtime_controls(tmp_path: Path):
    client = _client(tmp_path)
    js = client.get("/static/app.js").text
    assert "Download all tags in selected category/categories" in js
    assert "Date from" in js and "Oldest → Newest" in js
    assert "Parallelize presets/category jobs" in js
    assert "shard" in js.lower()
    assert "GPU ids" in js
    assert "cloud model override" in js

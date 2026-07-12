from __future__ import annotations

from pathlib import Path

from data_curation_tool import __version__


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_version_bumped_to_v5835() -> None:
    assert __version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_onnxruntime_gpu_is_pinned_to_cuda12_runtime_extras() -> None:
    for rel in [
        "requirements.txt",
        "requirements-models.txt",
        "requirements-annotation-models.txt",
        "environment.yml",
    ]:
        text = read(rel)
        assert "onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23" in text
        assert "onnxruntime-gpu>=1.18,<2" not in text

    repair = read("scripts/repair_onnxruntime_runtime.py")
    assert 'GPU_SPEC = "onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23"' in repair
    assert "cublasLt64_13" in repair
    assert "preload_dlls(cuda=True, cudnn=True, msvc=True)" in repair
    assert "fresh_process_report" in repair


def test_wd_pixai_onnx_adapter_preloads_cuda_dlls_and_keeps_strict_cuda() -> None:
    adapters = read("data_curation_tool/models/adapters.py")
    start = adapters.index("class WDOnnxTaggerAdapter")
    end = adapters.index("class LegacyVisionTaggerAdapter", start)
    section = adapters[start:end]

    assert "import torch" in section
    assert "preload_dlls(cuda=True, cudnn=True, msvc=True)" in section
    assert "CUDAExecutionProvider" in section
    assert "device_id" in section
    assert "CPU fallback is disabled" in section
    assert "CUDA-12 ONNX Runtime GPU stack" in section


def test_download_completion_uses_single_model_reconcile_instead_of_full_catalog_scan() -> None:
    app = read("data_curation_tool/static/app.js")
    watcher_start = app.index("function watchModelDownloadJob")
    watcher_end = app.index("state.modelDownloadJobWatchers[String(id)] = setInterval", watcher_start)
    watcher = app[watcher_start:watcher_end]
    queue_start = app.index("async function queueModelDownload")
    queue_end = app.index("async function queueModelLoad", queue_start)
    queue = app[queue_start:queue_end]

    assert "function patchModelCatalogRow" in app
    assert "async function reconcileDownloadedModelNow" in app
    assert "/api/models/reconcile/" in app
    assert "await reconcileDownloadedModelNow(name, id)" in watcher
    assert "refreshModelsPanel({ force: true" not in watcher
    # Queueing should not block on a full force-refresh before the user sees the job status.
    assert "await refreshModelsPanel({ force: true" not in queue
    assert "await refreshModelStatuses(false)" in queue


def test_backend_has_single_model_reconcile_endpoint_and_no_slow_full_scan_on_completion() -> None:
    router = read("data_curation_tool/routers/models.py")
    service = read("data_curation_tool/services/model_service.py")

    assert '@router.post("/reconcile/{model_name}")' in router
    assert "def reconcile_model_local_asset" in service
    section = service[service.index("def reconcile_model_local_asset"):service.index("def _complete_active_download_if_local_payload_ready")]
    assert "record.to_dict" in section
    assert "Local model payload verified; download status refreshed" in section
    assert "INCOMPLETE/CORRUPT" in section
    assert "self.invalidate_model_catalog_cache()" in section


def test_huggingface_downloads_have_timeout_defaults_and_stall_heartbeat() -> None:
    registry = read("data_curation_tool/models/registry.py")
    assert 'HF_HUB_DOWNLOAD_TIMEOUT' in registry
    assert 'HF_HUB_ETAG_TIMEOUT' in registry
    assert 'DCT_HF_DOWNLOAD_TIMEOUT' in registry
    assert 'DCT_MODEL_DOWNLOAD_STALL_NOTICE_SEC' in registry
    assert 'no new local bytes for' in registry
    assert 'still waiting on Hugging Face/network transfer' in registry


def test_documentation_added_for_v5835() -> None:
    assert Path(ROOT / "docs/V5_8_35_DOWNLOAD_FINALIZE_CUDA12_ONNX_REFRESH.md").exists()
    assert Path(ROOT / "docs/wiki/65-Download-Finalize-CUDA12-ONNX-Refresh.md").exists()
    assert "65-Download-Finalize-CUDA12-ONNX-Refresh.md" in read("docs/wiki/_Sidebar.md")
    assert "65-Download-Finalize-CUDA12-ONNX-Refresh.md" in read("docs/wiki/Home.md")

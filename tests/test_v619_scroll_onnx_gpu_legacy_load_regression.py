from pathlib import Path


def test_version_bumped_to_5_8_29():
    import data_curation_tool
    assert data_curation_tool.__version__ == "5.8.48"


def test_effnet_prefers_pytorch_before_onnx_for_cuda_fallback():
    from data_curation_tool.models.legacy_tagger_configs import legacy_tagger_config

    cfg = legacy_tagger_config("thouph-experimental-efficientnetv2-m-8035")
    candidates = list(cfg["model_candidates"])
    assert candidates.index("model_balanced.pth") < candidates.index("model_balanced.onnx")
    assert candidates.index("model.pth") < candidates.index("model.onnx")


def test_onnxruntime_gpu_replaces_cpu_runtime_in_requirements():
    for filename in ["requirements.txt", "requirements-models.txt", "requirements-annotation-models.txt", "environment.yml"]:
        text = Path(filename).read_text(encoding="utf-8")
        assert "onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23" in text
        assert "onnxruntime>=1.18" not in text.replace("onnxruntime-gpu>=1.18", "")


def test_scroll_restore_does_not_force_window_scroll_on_poll_renders():
    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "if (opts.restoreWindow === true)" in text
    assert "hardRefreshCurrentTab(forceNow = false)" in text
    assert "Automatic refreshes must not replace the shell while the user is scrolling" in text


def test_legacy_adapter_has_cpu_fallback_warning_and_pytorch_fallback():
    text = Path("data_curation_tool/models/adapters.py").read_text(encoding="utf-8")
    assert "def _find_pytorch_fallback" in text
    assert "using PyTorch fallback" in text
    assert "loaded the ONNX model on CPU so the model remains usable" in text

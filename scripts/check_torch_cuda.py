from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys


def nvidia_smi_count() -> int | None:
    exe = shutil.which("nvidia-smi")
    if not exe and os.name == "nt":
        candidate = os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32", "nvidia-smi.exe")
        if os.path.exists(candidate):
            exe = candidate
    if not exe:
        return None
    try:
        proc = subprocess.run([exe, "--query-gpu=index", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=8, check=False)
        if proc.returncode != 0:
            return None
        return len([line for line in proc.stdout.splitlines() if line.strip() != ""])
    except Exception:
        return None


def expected_visible_count(physical: int | None) -> int | None:
    override = os.environ.get("DCT_CUDA_VISIBLE_DEVICES")
    if override:
        return len([x for x in override.split(",") if x.strip()])
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible:
        return len([x for x in visible.split(",") if x.strip() and x.strip() != "-1"])
    return physical

try:
    import torch
except Exception as exc:
    print(json.dumps({"ok": False, "error": f"torch import failed: {exc}"}, indent=2))
    sys.exit(1)

version = getattr(torch, "__version__", "unknown")
cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
ready = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
torch_count = int(torch.cuda.device_count()) if ready else 0
physical_count = nvidia_smi_count()
expected_count = expected_visible_count(physical_count)
result = {
    "ok": bool(ready and cuda_version),
    "torch_version": version,
    "torch_cuda_version": cuda_version,
    "cuda_available": ready,
    "torch_device_count": torch_count,
    "nvidia_smi_device_count": physical_count,
    "expected_visible_count": expected_count,
    "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
    "DCT_CUDA_VISIBLE_DEVICES": os.environ.get("DCT_CUDA_VISIBLE_DEVICES"),
}
if result["ok"] and expected_count is not None and torch_count < expected_count and os.environ.get("DCT_ALLOW_TORCH_GPU_SUBSET") != "1":
    result["ok"] = False
    result["error"] = (
        f"torch sees {torch_count} CUDA GPU(s), but NVIDIA tools report/expect {expected_count}. "
        "The app clears CUDA_VISIBLE_DEVICES by default; set DCT_CUDA_VISIBLE_DEVICES intentionally, "
        "or reinstall CUDA-enabled torch in this Conda environment."
    )
print(json.dumps(result, indent=2))
sys.exit(0 if result["ok"] else 1)

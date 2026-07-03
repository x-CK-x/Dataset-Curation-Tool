from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Any


def _float_or_none(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _run_nvidia_smi() -> tuple[list[dict[str, Any]], str | None]:
    exe = shutil.which("nvidia-smi")
    if not exe and os.name == "nt":
        candidate = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "nvidia-smi.exe")
        if os.path.exists(candidate):
            exe = candidate
    if not exe:
        return [], "nvidia-smi was not found on PATH"
    try:
        # memory.used/free is required by the model-placement planner.  Some
        # older drivers do not expose cuda_version through --query-gpu, so keep
        # a lower-fidelity fallback below.
        cmd = [
            exe,
            "--query-gpu=index,name,uuid,pci.bus_id,memory.total,memory.used,memory.free,driver_version,cuda_version",
            "--format=csv,noheader,nounits",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
        has_memory_usage = proc.returncode == 0
        if proc.returncode != 0:
            cmd = [
                exe,
                "--query-gpu=index,name,uuid,pci.bus_id,memory.total,memory.used,memory.free,driver_version",
                "--format=csv,noheader,nounits",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
            has_memory_usage = proc.returncode == 0
        if proc.returncode != 0:
            cmd = [exe, "--query-gpu=index,name,uuid,pci.bus_id,memory.total,driver_version", "--format=csv,noheader,nounits"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
            has_memory_usage = False
        if proc.returncode != 0:
            return [], (proc.stderr or proc.stdout or "nvidia-smi failed").strip()
        devices: list[dict[str, Any]] = []
        for line in proc.stdout.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 5:
                continue
            idx = parts[0]
            name = parts[1]
            uuid = parts[2] if len(parts) > 2 else None
            pci_bus_id = parts[3] if len(parts) > 3 else None
            total_mb = _float_or_none(parts[4] if len(parts) > 4 else None)
            used_mb: float | None = None
            free_mb: float | None = None
            driver = parts[5] if len(parts) > 5 else None
            cuda_version = None
            if has_memory_usage and len(parts) >= 8:
                used_mb = _float_or_none(parts[5])
                free_mb = _float_or_none(parts[6])
                driver = parts[7]
                cuda_version = parts[8] if len(parts) > 8 else None
            elif len(parts) > 6:
                cuda_version = parts[6]
            total_memory_gb = round(total_mb / 1024, 2) if total_mb is not None else None
            used_memory_gb = round(used_mb / 1024, 2) if used_mb is not None else None
            free_memory_gb = round(free_mb / 1024, 2) if free_mb is not None else None
            devices.append(
                {
                    "id": f"cuda:{idx}",
                    "index": int(idx) if str(idx).isdigit() else idx,
                    "name": name,
                    "uuid": uuid,
                    "pci_bus_id": pci_bus_id,
                    "nvidia_smi_index": int(idx) if str(idx).isdigit() else idx,
                    "cuda_index_note": "CUDA ids follow PyTorch/nvidia-smi ordering; Windows Task Manager GPU numbers can differ.",
                    "type": "cuda-detected",
                    "total_memory_gb": total_memory_gb,
                    "used_memory_gb": used_memory_gb,
                    "free_memory_gb": free_memory_gb,
                    "driver_version": driver,
                    "cuda_version_reported_by_driver": cuda_version,
                    "torch_ready": False,
                }
            )
        return devices, None
    except Exception as exc:  # pragma: no cover - depends on host GPU tooling
        return [], str(exc)


def detect_devices() -> dict[str, Any]:
    """Detect CPU, NVIDIA GPUs, and whether PyTorch can use CUDA.

    The UI should not require torch just to see that NVIDIA GPUs exist. Torch is
    still the source of truth for whether model inference can actually use CUDA.
    """
    payload: dict[str, Any] = {
        "python": sys.executable,
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "torch_available": False,
        "cuda_available": False,
        "nvidia_smi_available": False,
        "devices": [{"id": "cpu", "name": "CPU", "type": "cpu", "torch_ready": True}],
        "torch_version": None,
        "torch_cuda_version": None,
        "error": None,
        "warnings": [],
        "install_hint": (
            "Run install.bat/install.sh again, or run the CUDA helper script. "
            "Set DCT_INSTALL_TORCH=cu128 for NVIDIA CUDA 12.8 wheels, cpu for CPU wheels, or skip to skip torch."
        ),
    }

    smi_devices, smi_error = _run_nvidia_smi()
    if smi_devices:
        payload["nvidia_smi_available"] = True
        payload["devices"].extend(smi_devices)
    elif smi_error:
        payload["warnings"].append(smi_error)

    try:
        import torch

        payload["torch_available"] = True
        payload["torch_version"] = getattr(torch, "__version__", None)
        payload["torch_cuda_version"] = getattr(getattr(torch, "version", None), "cuda", None)
        payload["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            # Merge torch-verified CUDA entries with nvidia-smi entries.  Some
            # Windows/Conda setups expose only a subset of GPUs to torch because
            # of CUDA_VISIBLE_DEVICES or runtime initialization issues, while
            # nvidia-smi still sees every physical card.  The UI should show all
            # physical GPUs and mark which are actually torch-ready.
            smi_by_id = {str(d.get("id")): d for d in smi_devices}
            payload["devices"] = [d for d in payload["devices"] if d.get("type") != "cuda-detected"]
            seen_cuda_ids: set[str] = set()
            for idx in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(idx)
                smi = smi_by_id.get(f"cuda:{idx}", {})
                used_gb = smi.get("used_memory_gb")
                free_gb = smi.get("free_memory_gb")
                if used_gb is None or free_gb is None:
                    try:
                        free_bytes, total_bytes = torch.cuda.mem_get_info(idx)
                        total_gb = total_bytes / (1024**3)
                        free_gb = round(free_bytes / (1024**3), 2)
                        used_gb = round(max(0.0, total_gb - free_bytes / (1024**3)), 2)
                    except Exception:
                        pass
                payload["devices"].append(
                    {
                        "id": f"cuda:{idx}",
                        "index": idx,
                        "name": props.name,
                        "uuid": smi.get("uuid"),
                        "pci_bus_id": smi.get("pci_bus_id"),
                        "nvidia_smi_index": smi.get("nvidia_smi_index", idx),
                        "cuda_index_note": "CUDA ids follow PyTorch/nvidia-smi ordering; Windows Task Manager GPU numbers can differ.",
                        "type": "cuda",
                        "total_memory_gb": round(props.total_memory / (1024**3), 2),
                        "physical_total_memory_gb": round(props.total_memory / (1024**3), 2),
                        "used_memory_gb": used_gb,
                        "free_memory_gb": free_gb,
                        "compute_capability": f"{props.major}.{props.minor}",
                        "torch_ready": True,
                    }
                )
                seen_cuda_ids.add(f"cuda:{idx}")
            for smi in smi_devices:
                sid = str(smi.get("id") or "")
                if sid and sid not in seen_cuda_ids:
                    row = dict(smi)
                    row["type"] = "cuda-detected-not-torch-visible"
                    row["torch_ready"] = False
                    row["physical_total_memory_gb"] = row.get("total_memory_gb")
                    row["warning"] = "GPU is visible to nvidia-smi but not to torch in this Conda/runtime process. Check CUDA_VISIBLE_DEVICES and CUDA-enabled torch installation."
                    payload["devices"].append(row)
            if smi_devices and len(seen_cuda_ids) < len(smi_devices):
                payload["warnings"].append("nvidia-smi reports more physical NVIDIA GPUs than torch.cuda.device_count(); non-torch-visible GPUs are shown but cannot run local torch models until the environment exposes them.")
        elif smi_devices:
            payload["warnings"].append(
                "NVIDIA GPUs were detected by nvidia-smi, but torch.cuda.is_available() is false. "
                "Install a CUDA-enabled torch build inside this Conda environment."
            )
    except Exception as exc:
        payload["error"] = str(exc)
        if smi_devices:
            payload["warnings"].append(
                "NVIDIA GPUs were detected, but torch could not be imported in this environment."
            )
    return payload

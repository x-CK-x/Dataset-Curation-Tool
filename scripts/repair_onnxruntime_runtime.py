#!/usr/bin/env python3
"""Validate and repair the ONNX Runtime Python namespace used by DCT.

The CPU and CUDA wheels expose the same ``onnxruntime`` import package.  A
partial uninstall/reinstall can therefore leave distribution metadata behind
while removing package files, producing an importable namespace that lacks
``InferenceSession``.  This helper validates the actual API, removes conflicting
CPU/GPU distributions when needed, installs the CUDA wheel cleanly, and then
validates the repaired runtime in a fresh interpreter.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

GPU_SPEC = "onnxruntime-gpu[cuda,cudnn]>=1.21,<1.23"
# Keep ORT below 1.23 for now: this tool targets CUDA 12.x desktop installs;
# unbounded installs can pull newer CUDA-13 wheels and fail with cublasLt64_13.dll.
DIST_NAMES = ("onnxruntime", "onnxruntime-gpu")


def _version_tuple(value: str | None) -> tuple[int, int, int]:
    if not value or value.startswith("error:"):
        return (0, 0, 0)
    parts: list[int] = []
    for chunk in str(value).replace("-", ".").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        if digits:
            parts.append(int(digits))
        if len(parts) >= 3:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def distribution_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in DIST_NAMES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
        except Exception as exc:  # pragma: no cover - unusual broken metadata
            out[name] = f"error: {exc}"
    return out


def inspect_runtime() -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": False,
        "python": sys.executable,
        "distributions": distribution_versions(),
        "module_file": None,
        "module_version": None,
        "providers": [],
        "preload_dlls_available": False,
        "preload_dlls_ok": None,
        "preload_dlls_error": None,
        "errors": [],
    }
    try:
        ort = importlib.import_module("onnxruntime")
    except Exception as exc:
        report["errors"].append(f"import onnxruntime failed: {exc}")
        return report

    report["module_file"] = str(getattr(ort, "__file__", None) or "")
    report["module_version"] = str(getattr(ort, "__version__", "") or "")
    report["preload_dlls_available"] = callable(getattr(ort, "preload_dlls", None))
    if report["preload_dlls_available"]:
        try:
            ort.preload_dlls(cuda=True, cudnn=True, msvc=True)
            report["preload_dlls_ok"] = True
        except Exception as exc:
            report["preload_dlls_ok"] = False
            report["preload_dlls_error"] = str(exc)
    if not callable(getattr(ort, "InferenceSession", None)):
        report["errors"].append("onnxruntime.InferenceSession is missing or not callable")
    if not callable(getattr(ort, "get_available_providers", None)):
        report["errors"].append("onnxruntime.get_available_providers is missing or not callable")
    else:
        try:
            report["providers"] = list(ort.get_available_providers() or [])
        except Exception as exc:
            report["errors"].append(f"get_available_providers() failed: {exc}")

    module_file = str(report["module_file"] or "")
    if not module_file or module_file in {"None", ""}:
        report["errors"].append("onnxruntime resolved to a namespace without a concrete __file__")
    report["ok"] = not report["errors"]
    return report


def gpu_install_is_clean(report: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    dists = report.get("distributions") or {}
    if not report.get("ok"):
        reasons.extend(str(x) for x in report.get("errors") or [])
    gpu_version = dists.get("onnxruntime-gpu")
    if not gpu_version:
        reasons.append("onnxruntime-gpu distribution is not installed")
    elif _version_tuple(str(gpu_version)) >= (1, 23, 0):
        reasons.append(
            f"onnxruntime-gpu {gpu_version} is outside the pinned CUDA-12 range {GPU_SPEC}; "
            "newer wheels can require CUDA 13 DLLs such as cublasLt64_13.dll"
        )
    if dists.get("onnxruntime"):
        reasons.append("CPU onnxruntime distribution is installed alongside onnxruntime-gpu")
    if report.get("preload_dlls_available") and report.get("preload_dlls_ok") is False:
        reasons.append(
            "onnxruntime.preload_dlls failed; CUDA/cuDNN/MSVC runtime extras may be missing or incompatible: "
            + str(report.get("preload_dlls_error") or "unknown preload error")
        )
    return not reasons, reasons


def run_command(args: list[str]) -> None:
    print("[onnxruntime-repair] $", " ".join(args), flush=True)
    subprocess.run(args, check=True)


def repair() -> None:
    pip = [sys.executable, "-m", "pip"]
    # Both distributions own the same import namespace.  Remove both before a
    # force reinstall so stale files/dist-info cannot survive the repair.
    run_command([*pip, "uninstall", "-y", "onnxruntime", "onnxruntime-gpu"])
    run_command([
        *pip,
        "install",
        "--upgrade",
        "--force-reinstall",
        "--no-cache-dir",
        GPU_SPEC,
    ])


def fresh_process_report() -> dict[str, Any]:
    snippet = r'''
import importlib, importlib.metadata as metadata, json, sys
out = {"ok": False, "python": sys.executable, "distributions": {}, "errors": [], "providers": []}
for name in ("onnxruntime", "onnxruntime-gpu"):
    try: out["distributions"][name] = metadata.version(name)
    except metadata.PackageNotFoundError: out["distributions"][name] = None
    except Exception as exc: out["distributions"][name] = "error: " + str(exc)
try:
    ort = importlib.import_module("onnxruntime")
    out["module_file"] = str(getattr(ort, "__file__", None) or "")
    out["module_version"] = str(getattr(ort, "__version__", "") or "")
    if callable(getattr(ort, "preload_dlls", None)):
        try: ort.preload_dlls(cuda=True, cudnn=True, msvc=True); out["preload_dlls_ok"] = True
        except Exception as exc: out["preload_dlls_ok"] = False; out["preload_dlls_error"] = str(exc)
    else:
        out["preload_dlls_ok"] = None
    if not callable(getattr(ort, "InferenceSession", None)): out["errors"].append("InferenceSession missing")
    if not callable(getattr(ort, "get_available_providers", None)): out["errors"].append("get_available_providers missing")
    else:
        try: out["providers"] = list(ort.get_available_providers() or [])
        except Exception as exc: out["errors"].append("provider query failed: " + str(exc))
except Exception as exc:
    out["errors"].append("import failed: " + str(exc))
out["ok"] = not out["errors"]
print(json.dumps(out))
'''
    proc = subprocess.run([sys.executable, "-c", snippet], text=True, capture_output=True)
    if proc.returncode != 0:
        return {"ok": False, "errors": [proc.stderr.strip() or f"fresh interpreter exited {proc.returncode}"]}
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        return {"ok": False, "errors": [f"could not parse fresh validation output: {exc}", proc.stdout, proc.stderr]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Validate without installing or uninstalling packages.")
    parser.add_argument("--force", action="store_true", help="Always remove both CPU/GPU wheels and reinstall the CUDA wheel.")
    parser.add_argument("--ensure-gpu", action="store_true", help="Require a clean onnxruntime-gpu-only installation (default for DCT installers).")
    args = parser.parse_args()

    before = inspect_runtime()
    clean_gpu, reasons = gpu_install_is_clean(before)
    print("[onnxruntime-repair] before:")
    print(json.dumps(before, indent=2, sort_keys=True))

    needs_repair = bool(args.force or not before.get("ok") or ((args.ensure_gpu or not args.check_only) and not clean_gpu))
    if args.check_only:
        if before.get("ok") and (not args.ensure_gpu or clean_gpu):
            return 0
        if reasons:
            print("[onnxruntime-repair] validation reasons:")
            for reason in reasons:
                print(f"  - {reason}")
        return 2

    if needs_repair:
        print("[onnxruntime-repair] repairing because:")
        for reason in reasons or ["--force was requested"]:
            print(f"  - {reason}")
        try:
            repair()
        except subprocess.CalledProcessError as exc:
            print(f"[onnxruntime-repair] repair command failed with exit code {exc.returncode}", file=sys.stderr)
            return int(exc.returncode or 1)
    else:
        print("[onnxruntime-repair] runtime is already healthy; no package changes required.")

    after = fresh_process_report()
    print("[onnxruntime-repair] after:")
    print(json.dumps(after, indent=2, sort_keys=True))
    clean_after, after_reasons = gpu_install_is_clean(after)
    if not after.get("ok") or not clean_after:
        for reason in after_reasons:
            print(f"[onnxruntime-repair] ERROR: {reason}", file=sys.stderr)
        return 3
    if "CUDAExecutionProvider" not in set(after.get("providers") or []):
        print(
            "[onnxruntime-repair] WARNING: the GPU wheel is healthy, but CUDAExecutionProvider is not currently available. "
            "Check the ONNX Runtime/CUDA/cuDNN compatibility matrix and PATH/DLL visibility.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

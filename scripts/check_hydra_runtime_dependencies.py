from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _check_imports() -> list[str]:
    required = [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("timm", "timm"),
        ("einops", "einops"),
        ("safetensors", "safetensors"),
        ("numpy", "numpy"),
        ("PIL", "pillow"),
    ]
    missing: list[str] = []
    for module, package in required:
        try:
            __import__(module)
        except Exception as exc:
            missing.append(f"{package} ({exc})")
    return missing


def main() -> int:
    missing = _check_imports()
    repair_script = Path(__file__).with_name("repair_hydra_runtime_dependencies.py")
    proc = subprocess.run([sys.executable, str(repair_script), "--check-only"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pyvips_output = proc.stdout or ""
    if proc.returncode != 0:
        missing.append("pyvips/libvips")
    if missing:
        print("Hydra runtime dependency check failed:")
        for item in missing:
            print(f"  - {item}")
        print("\npyvips/libvips diagnostic:")
        print(pyvips_output.strip())
        print("\nRecommended automatic repair:")
        print("  python scripts/repair_hydra_runtime_dependencies.py")
        print("or run:")
        print("  install_hydra_runtime_deps.bat")
        print("\nManual fallback:")
        print('  python -m pip install "pyvips[binary]>=3.0.0" pyvips-binary>=8.16.0 cffi>=1.17.1')
        print("  conda install -n data-curation-tool -c conda-forge pyvips libvips cffi")
        return 1
    print("Hydra runtime dependencies OK.")
    print(pyvips_output.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

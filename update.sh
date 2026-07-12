#!/usr/bin/env bash
export CUDA_DEVICE_ORDER="${CUDA_DEVICE_ORDER:-PCI_BUS_ID}"
set -euo pipefail

if [ -n "${DCT_CUDA_VISIBLE_DEVICES:-}" ]; then
  export CUDA_VISIBLE_DEVICES="$DCT_CUDA_VISIBLE_DEVICES"
else
  unset CUDA_VISIBLE_DEVICES
fi
cd "$(dirname "$0")"
export DCT_ENV_NAME="${DCT_ENV_NAME:-data-curation-tool}"
export DCT_ENV_FILE="${DCT_ENV_FILE:-environment.yml}"

# Initialize Conda even when the target env was deleted.
# shellcheck source=/dev/null
source scripts/activate_data_curation_env.sh || true
if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] Conda could not be initialized. Set DCT_CONDA_BASE to your Conda root."
  exit 1
fi

ensure_conda_env() {
  if [ ! -f "$DCT_ENV_FILE" ]; then
    echo "[ERROR] Missing $DCT_ENV_FILE in $(pwd)."
    return 1
  fi
  if conda env list | awk '{print $1}' | grep -Fxq "$DCT_ENV_NAME"; then
    echo "Updating Conda environment from $DCT_ENV_FILE..."
    conda env update -n "$DCT_ENV_NAME" -f "$DCT_ENV_FILE" --prune
  else
    echo "Creating Conda environment from $DCT_ENV_FILE..."
    conda env create -f "$DCT_ENV_FILE"
  fi
}

if ! ensure_conda_env; then
  cat <<'TXT'

[ERROR] Conda failed to create/update the data-curation-tool environment.
Check the dependency name above, then run: conda clean --all
Note: soundfile uses conda package pysoundfile; Hydra local inference uses conda-forge pyvips/libvips plus pip pyvips[binary] fallback.
TXT
  exit 1
fi

conda activate "$DCT_ENV_NAME"
python -m pip install --upgrade pip
python scripts/repair_onnxruntime_runtime.py --ensure-gpu
python -m pip install -r requirements.txt --upgrade-strategy only-if-needed
python scripts/repair_onnxruntime_runtime.py --ensure-gpu
python -m pip install 'pyvips[binary]>=3.0.0' --upgrade-strategy only-if-needed
python -m pip install -e . --no-deps
# Hydra repair fallback uses pyvips[binary]>=3.0.0 pyvips-binary>=8.16.0 cffi>=1.17.1
python scripts/check_core_dependencies.py
if ! python scripts/repair_hydra_runtime_dependencies.py; then
  echo "[WARN] Hydra pyvips/libvips auto-repair did not complete. Run ./install_hydra_runtime_deps.sh before using RedRocket Hydra 3.5 locally."
fi
MODE="${DCT_INSTALL_TORCH:-auto}"
if [ "$MODE" = "auto" ]; then
  if command -v nvidia-smi >/dev/null 2>&1; then MODE="cu128"; else MODE="skip"; fi
fi
case "$MODE" in
  cu128)
    if ! python scripts/check_torch_cuda.py >/dev/null 2>&1; then
      echo "Installing/replacing CPU PyTorch with CUDA 12.8 PyTorch wheels..."
      python -m pip uninstall -y torch torchvision torchaudio || true
      python -m pip install --force-reinstall -r requirements-torch-cu128.txt
    else
      echo "CUDA PyTorch already available."
    fi
    ;;
  cpu)
    echo "Installing CPU PyTorch wheels..."
    python -m pip install --force-reinstall -r requirements-torch-cpu.txt
    ;;
  skip)
    echo "Skipping PyTorch install. Set DCT_INSTALL_TORCH=cu128 or cpu to install it."
    ;;
  *)
    echo "Unknown DCT_INSTALL_TORCH mode: $MODE. Use auto, cu128, cpu, or skip."
    exit 1
    ;;
esac
python -m compileall data_curation_tool
python - <<'PY'
from data_curation_tool.services.gpu_service import detect_devices
import json
print(json.dumps(detect_devices(), indent=2))
PY
echo "Update complete. Run ./run.sh to start the HUD."

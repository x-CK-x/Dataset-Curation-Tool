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
# shellcheck source=/dev/null
source scripts/activate_data_curation_env.sh || true
if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] Conda could not be initialized. Set DCT_CONDA_BASE to your Conda root."
  exit 1
fi
conda env update -f environment.yml --prune
conda activate "$DCT_ENV_NAME"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --upgrade
python -m pip install -e .
python scripts/check_core_dependencies.py
MODE="${DCT_INSTALL_TORCH:-auto}"
if [ "$MODE" = "auto" ]; then
  if command -v nvidia-smi >/dev/null 2>&1; then MODE="cu128"; else MODE="skip"; fi
fi
case "$MODE" in
  cu128)
    if ! python scripts/check_torch_cuda.py >/dev/null 2>&1; then
      echo "Installing CUDA 12.8 PyTorch wheels for NVIDIA GPUs..."
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

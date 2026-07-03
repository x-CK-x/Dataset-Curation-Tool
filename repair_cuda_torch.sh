#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source scripts/activate_data_curation_env.sh
python -m pip uninstall -y torch torchvision torchaudio || true
python -m pip install --force-reinstall -r requirements-torch-cu128.txt
python scripts/check_torch_cuda.py

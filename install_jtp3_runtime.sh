#!/usr/bin/env bash
set -euo pipefail
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  source scripts/activate_data_curation_env.sh
fi
echo 'Installing RedRocket JTP-3 runtime dependencies into data-curation-tool...'
python -m pip install --upgrade --timeout 120 --retries 3 pip
python -m pip install --upgrade --timeout 120 --retries 3 'timm>=1.0.16' torch numpy pillow einops safetensors requests
echo 'Done. If torch is CPU-only, run install_torch_cuda128.bat afterwards.'

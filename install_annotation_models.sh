#!/usr/bin/env bash
set -euo pipefail
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  source scripts/activate_data_curation_env.sh
fi
python -m pip install --upgrade pip
python -m pip install -r requirements-annotation-models.txt
echo "SAM/SAM-HQ/YOLO dependencies were requested. Optional SAM2 can be installed from the Annotation Editor with include_sam2=true; WSL/Linux is often safer if Windows CUDA extension builds fail."

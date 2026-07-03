#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
family="${1:-sam}"
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  source scripts/activate_data_curation_env.sh
fi
python -m pip install --upgrade pip
case "$family" in
  sam)
    python -m pip install --upgrade git+https://github.com/facebookresearch/segment-anything.git
    ;;
  sam_hq|sam-hq)
    python -m pip install --upgrade segment-anything-hq
    ;;
  sam2)
    python -m pip install --upgrade git+https://github.com/facebookresearch/sam2.git
    ;;
  *)
    echo "Unknown family: $family" >&2
    echo "Usage: ./install_sam_runtime.sh sam|sam_hq|sam2" >&2
    exit 2
    ;;
esac
echo "[OK] $family runtime installed. Download/load the exact checkpoint from Segmentation & Masks."

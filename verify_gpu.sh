#!/usr/bin/env bash
set -euo pipefail
export CUDA_DEVICE_ORDER="${CUDA_DEVICE_ORDER:-PCI_BUS_ID}"
if [ -n "${DCT_CUDA_VISIBLE_DEVICES:-}" ]; then
  export CUDA_VISIBLE_DEVICES="$DCT_CUDA_VISIBLE_DEVICES"
else
  unset CUDA_VISIBLE_DEVICES
fi
cd "$(dirname "$0")"
source scripts/activate_data_curation_env.sh
python - <<'PY'
from data_curation_tool.services.gpu_service import detect_devices
import json
print(json.dumps(detect_devices(), indent=2))
PY

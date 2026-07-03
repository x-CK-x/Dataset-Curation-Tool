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
source scripts/activate_data_curation_env.sh || { echo "Could not activate data-curation-tool. Running install.sh..."; ./install.sh; source scripts/activate_data_curation_env.sh; }
if ! python scripts/check_core_dependencies.py >/dev/null 2>&1; then
  echo "Required Python dependencies are missing. Running update.sh now..."
  ./update.sh
  source scripts/activate_data_curation_env.sh
fi
export DCT_BROWSER_MODE="${DCT_BROWSER_MODE:-firefox_selenium}"
python run.py --host 127.0.0.1 --port 7865 --open-browser "$@"

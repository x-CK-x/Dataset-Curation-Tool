#!/usr/bin/env bash
# Exact fallback dependency: pyvips[binary]>=3.0.0 plus pyvips-binary>=8.16.0 and cffi>=1.17.1
set -euo pipefail
cd "$(dirname "$0")"
DCT_ENV_NAME="${DCT_ENV_NAME:-data-curation-tool}"
source scripts/activate_data_curation_env.sh

echo "Repairing RedRocket Hydra 3.5 pyvips/libvips runtime dependencies in ${DCT_ENV_NAME}..."
echo "This uses the pip pyvips-binary fallback first, then conda-forge pyvips/libvips if needed."
python scripts/repair_hydra_runtime_dependencies.py
python scripts/check_hydra_runtime_dependencies.py

echo
echo "Hydra runtime dependencies are installed. Restart the app, then re-run Hydra load/inference."

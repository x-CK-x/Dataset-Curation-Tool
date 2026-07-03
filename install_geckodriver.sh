#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DCT_ENV_NAME="${DCT_CONDA_ENV:-data-curation-tool}"
source scripts/activate_data_curation_env.sh
python scripts/install_geckodriver.py

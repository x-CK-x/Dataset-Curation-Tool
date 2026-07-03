#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source scripts/activate_data_curation_env.sh
python -m pip install -r requirements-torch-cpu.txt
python - <<'PY'
import torch
print('torch', torch.__version__)
print('cuda available', torch.cuda.is_available())
PY

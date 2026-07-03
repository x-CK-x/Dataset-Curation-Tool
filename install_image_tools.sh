#!/usr/bin/env bash
set -euo pipefail
source "$(conda info --base)/etc/profile.d/conda.sh"
source scripts/activate_data_curation_env.sh
python -m pip install -r requirements-image-tools.txt
echo "Image enhancement dependencies installed. Commercial Topaz tools must be installed/licensed separately and configured in the Augment tab."

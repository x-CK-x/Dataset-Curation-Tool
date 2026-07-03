#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source "$(conda info --base)/etc/profile.d/conda.sh"
source scripts/activate_data_curation_env.sh
python scripts/test_geckodriver_firefox.py --url https://example.com --hold-seconds 8

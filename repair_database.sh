#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source scripts/activate_data_curation_env.sh
python scripts/repair_database.py "$@"

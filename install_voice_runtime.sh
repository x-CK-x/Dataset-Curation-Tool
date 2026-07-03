#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export DCT_ENV_NAME="${DCT_ENV_NAME:-data-curation-tool}"
source scripts/activate_data_curation_env.sh
python -m pip install --upgrade pip
python -m pip install -r requirements-voice.txt --upgrade
echo "Optional voice STT/TTS runtime packages installed."

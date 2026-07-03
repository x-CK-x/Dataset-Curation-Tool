#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-quick}"
case "$MODE" in
  quick|full|update) ;;
  *) echo "Usage: ./install_flexavatar.sh [quick|full|update]"; exit 2 ;;
esac
ENV_NAME="dct-flexavatar"
source scripts/activate_data_curation_env.sh || true
if ! command -v conda >/dev/null 2>&1; then
  echo "Conda could not be initialized. Set DCT_CONDA_BASE to your Conda root."
  exit 1
fi
KEEP_FULL=0
[[ "$MODE" == "full" ]] && KEEP_FULL=1
[[ -f runtime/flexavatar/.full_setup_complete ]] && KEEP_FULL=1
if conda env list --json | python -c 'import json,sys,os; n="dct-flexavatar"; d=json.load(sys.stdin); raise SystemExit(0 if any(os.path.basename(x)==n for x in d.get("envs",[])) else 1)'; then
  conda env update -n "$ENV_NAME" -f integrations/flexavatar/environment-dct.yml --prune
else
  conda env create -n "$ENV_NAME" -f integrations/flexavatar/environment-dct.yml
fi
conda run --no-capture-output -n "$ENV_NAME" python -m pip install -e "$PWD/integrations/flexavatar/source"
mkdir -p runtime/flexavatar
date -u +%FT%TZ > runtime/flexavatar/.quick_setup_complete
if [[ "$KEEP_FULL" == "1" ]]; then
  conda run --no-capture-output -n "$ENV_NAME" python -m pip install git+https://github.com/tobias-kirschstein/easy-pixel3dmm.git
  conda run --no-capture-output -n "$ENV_NAME" python -m pip install --extra-index-url https://miropsota.github.io/torch_packages_builder pytorch3d==0.7.9+pt2.7.1cu118
  conda run --no-capture-output -n "$ENV_NAME" python -m pip install --no-build-isolation git+https://github.com/NVlabs/nvdiffrast.git
  conda run --no-capture-output -n "$ENV_NAME" python -m pixel3dmm.scripts.install_preprocessing_pipeline
  date -u +%FT%TZ > runtime/flexavatar/.full_setup_complete
fi
echo "FlexAvatar $MODE setup complete."

#!/usr/bin/env bash
# Source this file: source scripts/activate_data_curation_env.sh
DCT_ENV_NAME="${DCT_ENV_NAME:-data-curation-tool}"
_dct_conda_base="${DCT_CONDA_BASE:-}"
if [ -z "$_dct_conda_base" ] && command -v conda >/dev/null 2>&1; then
  _dct_conda_base="$(conda info --base 2>/dev/null || true)"
fi
if [ -z "$_dct_conda_base" ]; then
  for candidate in "$HOME/miniconda3" "$HOME/anaconda3" "$HOME/mambaforge" "$HOME/miniforge3" "$HOME/.conda" "/opt/conda"; do
    if [ -f "$candidate/etc/profile.d/conda.sh" ]; then
      _dct_conda_base="$candidate"
      break
    fi
  done
fi
if [ -z "$_dct_conda_base" ] || [ ! -f "$_dct_conda_base/etc/profile.d/conda.sh" ]; then
  echo "[ERROR] Conda was not found. Set DCT_CONDA_BASE to your Conda root, e.g. $HOME/miniconda3."
  return 1 2>/dev/null || exit 1
fi
# shellcheck source=/dev/null
source "$_dct_conda_base/etc/profile.d/conda.sh"
conda activate "$DCT_ENV_NAME"

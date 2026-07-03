#!/usr/bin/env bash
set -euo pipefail
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  source scripts/activate_data_curation_env.sh
fi
family="${1:-basic}"
python -m pip install --upgrade pip
install_mediapipe() { python -m pip install --upgrade --timeout 120 --retries 3 'mediapipe>=0.10.14'; }
install_ultralytics() { python -m pip install --upgrade --timeout 120 --retries 3 ultralytics; }
install_mmpose() {
  echo 'Installing OpenMMLab pose runtime. This optional step can be large and version-sensitive.'
  python -m pip install --upgrade --timeout 120 --retries 3 'openmim>=0.3.9'
  python -m mim install 'mmengine>=0.10.0' 'mmcv>=2.0.1' 'mmdet>=3.0.0' 'mmpose>=1.3.0'
}
case "$family" in
  basic|all) install_ultralytics; install_mediapipe ;;
  ultralytics) install_ultralytics ;;
  mediapipe) install_mediapipe ;;
  mmpose|mmpose-full) install_mmpose ;;
  all-full) install_ultralytics; install_mediapipe; install_mmpose ;;
  *) echo 'Usage: install_pose_models.sh [basic|ultralytics|mediapipe|mmpose|all-full]' >&2; exit 2 ;;
esac
echo 'Pose runtime installation finished. Use Pose & 3D > Check Status / Download / Load.'

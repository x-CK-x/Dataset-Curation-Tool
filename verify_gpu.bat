@echo off
setlocal
if defined DCT_CUDA_VISIBLE_DEVICES (
  set "CUDA_VISIBLE_DEVICES=%DCT_CUDA_VISIBLE_DEVICES%"
) else (
  set "CUDA_VISIBLE_DEVICES="
)
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat || exit /b 1
python -c "from data_curation_tool.services.gpu_service import detect_devices; import json; print(json.dumps(detect_devices(), indent=2))"
pause

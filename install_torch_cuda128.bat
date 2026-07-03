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
python -m pip install -r requirements-torch-cu128.txt
python -c "import torch; print('torch', torch.__version__); print('cuda available', torch.cuda.is_available()); print('device count', torch.cuda.device_count())"
pause

@echo off
setlocal
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat || exit /b 1
python -m pip uninstall -y torch torchvision torchaudio
python -m pip install --force-reinstall -r requirements-torch-cu128.txt || exit /b 1
python scripts\check_torch_cuda.py
pause

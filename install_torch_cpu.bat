@echo off
setlocal
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat || exit /b 1
python -m pip install -r requirements-torch-cpu.txt
python -c "import torch; print('torch', torch.__version__); print('cuda available', torch.cuda.is_available())"
pause

@echo off
setlocal EnableExtensions
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat
if errorlevel 1 (
  echo Could not activate conda environment data-curation-tool.
  pause
  exit /b 1
)
echo Installing RedRocket JTP-3 runtime dependencies into data-curation-tool...
python -m pip install --upgrade --timeout 120 --retries 3 pip
python -m pip install --upgrade --timeout 120 --retries 3 "timm>=1.0.16" torch numpy pillow einops safetensors requests
if errorlevel 1 (
  echo JTP-3 runtime dependency install failed.
  pause
  exit /b 1
)
echo Done. If torch is CPU-only, run install_torch_cuda128.bat afterwards.
pause

@echo off
set "CUDA_DEVICE_ORDER=PCI_BUS_ID"
setlocal EnableExtensions
if defined DCT_CUDA_VISIBLE_DEVICES (
  set "CUDA_VISIBLE_DEVICES=%DCT_CUDA_VISIBLE_DEVICES%"
) else (
  rem Clear accidental global CUDA masking so both RTX cards are visible by default.
  set "CUDA_VISIBLE_DEVICES="
)
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\find_conda.bat || (pause & exit /b 1)
echo Updating Conda environment: %DCT_ENV_NAME%
call "%DCT_CONDA_BAT%" env update -f environment.yml --prune || exit /b 1
call scripts\activate_data_curation_env.bat || exit /b 1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --upgrade || exit /b 1
python -m pip install -e . || exit /b 1
python scripts\check_core_dependencies.py || exit /b 1
if "%DCT_INSTALL_TORCH%"=="" set "DCT_INSTALL_TORCH=auto"
set "TORCH_MODE=%DCT_INSTALL_TORCH%"
if /I "%TORCH_MODE%"=="auto" (
  where nvidia-smi >nul 2>nul
  if errorlevel 1 (set "TORCH_MODE=skip") else (set "TORCH_MODE=cu128")
)
if /I "%TORCH_MODE%"=="cu128" (
  python scripts\check_torch_cuda.py >nul 2>nul
  if errorlevel 1 (
    echo Installing CUDA 12.8 PyTorch wheels for NVIDIA GPUs...
    python -m pip uninstall -y torch torchvision torchaudio
    python -m pip install --force-reinstall -r requirements-torch-cu128.txt || exit /b 1
  ) else (
    echo CUDA PyTorch already available.
  )
) else if /I "%TORCH_MODE%"=="cpu" (
  echo Installing CPU PyTorch wheels...
  python -m pip install --force-reinstall -r requirements-torch-cpu.txt || exit /b 1
) else (
  echo Skipping PyTorch install. Set DCT_INSTALL_TORCH=cu128 or cpu to install it.
)
python -m compileall data_curation_tool || exit /b 1
python -c "from data_curation_tool.services.gpu_service import detect_devices; import json; print(json.dumps(detect_devices(), indent=2))"
echo.
echo Install complete. Run run.bat to start the HUD.
pause

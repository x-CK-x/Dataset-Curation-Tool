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
set "DCT_ENV_FILE=environment.yml"
call scripts\find_conda.bat || (pause & exit /b 1)
echo Updating Conda environment: %DCT_ENV_NAME%
call :ensure_conda_env || (pause & exit /b 1)
call scripts\activate_data_curation_env.bat || exit /b 1
python -m pip install --upgrade pip
python scripts\repair_onnxruntime_runtime.py --ensure-gpu || exit /b 1
python -m pip install -r requirements.txt --upgrade-strategy only-if-needed || exit /b 1
python scripts\repair_onnxruntime_runtime.py --ensure-gpu || exit /b 1
python -m pip install "pyvips[binary]>=3.0.0" --upgrade-strategy only-if-needed || exit /b 1
python -m pip install -e . --no-deps || exit /b 1
rem Hydra repair fallback uses pyvips[binary]>=3.0.0 pyvips-binary>=8.16.0 cffi>=1.17.1
python scripts\check_core_dependencies.py || exit /b 1
python scripts\repair_hydra_runtime_dependencies.py
if errorlevel 1 (
  echo [WARN] Hydra pyvips/libvips auto-repair did not complete. Run install_hydra_runtime_deps.bat before using RedRocket Hydra 3.5 locally.
)
if "%DCT_INSTALL_TORCH%"=="" set "DCT_INSTALL_TORCH=auto"
set "TORCH_MODE=%DCT_INSTALL_TORCH%"
if /I "%TORCH_MODE%"=="auto" (
  where nvidia-smi >nul 2>nul
  if errorlevel 1 (set "TORCH_MODE=skip") else (set "TORCH_MODE=cu128")
)
if /I "%TORCH_MODE%"=="cu128" (
  python scripts\check_torch_cuda.py >nul 2>nul
  if errorlevel 1 (
    echo Installing/replacing CPU PyTorch with CUDA 12.8 PyTorch wheels...
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
echo Update complete. Run run.bat to start the HUD.
pause
exit /b 0

:ensure_conda_env
if not exist "%DCT_ENV_FILE%" (
  echo [ERROR] Missing %DCT_ENV_FILE% in %CD%.
  exit /b 1
)
call "%DCT_CONDA_BAT%" env list | findstr /R /I /C:"^%DCT_ENV_NAME%[ ]" >nul 2>nul
if errorlevel 1 (
  echo Creating Conda environment from %DCT_ENV_FILE%...
  call "%DCT_CONDA_BAT%" env create -f "%DCT_ENV_FILE%"
) else (
  echo Updating Conda environment from %DCT_ENV_FILE%...
  call "%DCT_CONDA_BAT%" env update -n "%DCT_ENV_NAME%" -f "%DCT_ENV_FILE%" --prune
)
if errorlevel 1 (
  echo.
  echo [ERROR] Conda failed to create/update %DCT_ENV_NAME%.
  echo Check the dependency name above, then run: conda clean --all
  echo Note: soundfile uses conda package pysoundfile; Hydra local inference uses conda-forge pyvips/libvips plus pip pyvips[binary] fallback.
  exit /b 1
)
exit /b 0

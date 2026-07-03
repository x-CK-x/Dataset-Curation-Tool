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
call scripts\activate_data_curation_env.bat
if errorlevel 1 (
  echo Conda environment data-curation-tool was not found or could not activate.
  echo Running install.bat first...
  call install.bat || exit /b 1
  call scripts\activate_data_curation_env.bat || exit /b 1
)
python scripts\check_core_dependencies.py >nul 2>nul
if errorlevel 1 (
  echo Required Python dependencies are missing. Running update.bat now...
  call update.bat || exit /b 1
  call scripts\activate_data_curation_env.bat || exit /b 1
)
if "%DCT_BROWSER_MODE%"=="" set "DCT_BROWSER_MODE=firefox_selenium"
python run.py --host 127.0.0.1 --port 7865 --open-browser %*

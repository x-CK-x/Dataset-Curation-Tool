@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=quick"
if /I not "%MODE%"=="quick" if /I not "%MODE%"=="full" if /I not "%MODE%"=="update" (
  echo Usage: install_flexavatar.bat [quick^|full^|update]
  pause
  exit /b 2
)
call scripts\find_conda.bat || (pause & exit /b 1)
set "ENV_NAME=dct-flexavatar"
set "KEEP_FULL=0"
if /I "%MODE%"=="full" set "KEEP_FULL=1"
if exist "runtime\flexavatar\.full_setup_complete" set "KEEP_FULL=1"

call "%DCT_CONDA_BAT%" env list | findstr /I /R "[\\/]%ENV_NAME%$" >nul 2>nul
if errorlevel 1 (
  echo Creating isolated FlexAvatar environment %ENV_NAME%...
  call "%DCT_CONDA_BAT%" env create -n "%ENV_NAME%" -f "integrations\flexavatar\environment-dct.yml"
) else (
  echo Updating isolated FlexAvatar environment %ENV_NAME%...
  call "%DCT_CONDA_BAT%" env update -n "%ENV_NAME%" -f "integrations\flexavatar\environment-dct.yml" --prune
)
if errorlevel 1 goto :failed

call "%DCT_CONDA_BAT%" run --no-capture-output -n "%ENV_NAME%" python -m pip install -e "%CD%\integrations\flexavatar\source"
if errorlevel 1 goto :failed
if not exist "runtime\flexavatar" mkdir "runtime\flexavatar"
>"runtime\flexavatar\.quick_setup_complete" echo installed

if "%KEEP_FULL%"=="1" (
  echo Installing or refreshing Pixel3DMM full custom-input tracking stack...
  call "%DCT_CONDA_BAT%" run --no-capture-output -n "%ENV_NAME%" python -m pip install git+https://github.com/tobias-kirschstein/easy-pixel3dmm.git
  if errorlevel 1 goto :failed
  call "%DCT_CONDA_BAT%" run --no-capture-output -n "%ENV_NAME%" python -m pip install --extra-index-url https://miropsota.github.io/torch_packages_builder pytorch3d==0.7.9+pt2.7.1cu118
  if errorlevel 1 goto :failed
  call "%DCT_CONDA_BAT%" run --no-capture-output -n "%ENV_NAME%" python -m pip install --no-build-isolation git+https://github.com/NVlabs/nvdiffrast.git
  if errorlevel 1 goto :failed
  call "%DCT_CONDA_BAT%" run --no-capture-output -n "%ENV_NAME%" python -m pixel3dmm.scripts.install_preprocessing_pipeline
  if errorlevel 1 goto :failed
  >"runtime\flexavatar\.full_setup_complete" echo installed
  echo Full tracking and official-viewer runtime installed.
)

echo FlexAvatar %MODE% setup complete.
echo Open the FlexAvatar tab to download/install FLEX-1, seed examples, and run validation.
pause
exit /b 0

:failed
echo.
echo FlexAvatar setup failed. Review the error above. The main Data Curation Tool environment was not modified.
pause
exit /b 1

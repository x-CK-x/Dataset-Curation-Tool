@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "FAMILY=%~1"
if "%FAMILY%"=="" set "FAMILY=sam"

set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat
if errorlevel 1 (
  echo [ERROR] Could not activate Conda environment data-curation-tool.
  echo Run install.bat first, or activate the environment manually.
  pause
  exit /b 1
)

python -m pip install --upgrade pip
if /I "%FAMILY%"=="sam" goto install_sam
if /I "%FAMILY%"=="sam_hq" goto install_sam_hq
if /I "%FAMILY%"=="sam-hq" goto install_sam_hq
if /I "%FAMILY%"=="sam2" goto install_sam2

echo [ERROR] Unknown family "%FAMILY%".
echo Usage: install_sam_runtime.bat sam ^| sam_hq ^| sam2
pause
exit /b 2

:install_sam
python -m pip install --upgrade git+https://github.com/facebookresearch/segment-anything.git
if errorlevel 1 goto failed
echo [OK] SAM runtime installed. Choose a SAM model in Segmentation ^& Masks and use Download Weights / Load.
goto done

:install_sam_hq
python -m pip install --upgrade segment-anything-hq
if errorlevel 1 goto failed
echo [OK] SAM-HQ runtime installed. Choose a SAM-HQ model in Segmentation ^& Masks and use Download Weights / Load.
goto done

:install_sam2
python -m pip install --upgrade git+https://github.com/facebookresearch/sam2.git
if errorlevel 1 goto failed
echo [OK] SAM2 runtime installed.
echo [NOTE] The official project recommends WSL/Ubuntu for Windows installations if CUDA extension compilation fails.
goto done

:failed
echo [ERROR] %FAMILY% runtime installation failed. Review the command output above.
pause
exit /b 1

:done
pause
exit /b 0

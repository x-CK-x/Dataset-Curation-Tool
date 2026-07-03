@echo off
setlocal
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat
if errorlevel 1 (
  echo Could not activate conda environment data-curation-tool.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
python -m pip install -r requirements-annotation-models.txt
echo.
echo SAM/SAM-HQ/YOLO dependencies were requested. Optional SAM2 can be installed from the Annotation Editor with include_sam2=true; WSL/Linux is often safer if Windows CUDA extension builds fail.
pause

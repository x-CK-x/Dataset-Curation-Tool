@echo off
setlocal
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat
if errorlevel 1 (
  echo Conda environment not found. Running install.bat first.
  call install.bat || exit /b 1
  call scripts\activate_data_curation_env.bat || exit /b 1
)
python scripts\repair_database.py %*
pause

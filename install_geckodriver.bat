@echo off
setlocal
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat || (echo Conda env not found. Run install.bat first.& pause& exit /b 1)
python scripts\install_geckodriver.py
pause

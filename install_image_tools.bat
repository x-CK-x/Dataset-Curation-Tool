@echo off
setlocal
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat
if errorlevel 1 goto :conda_fail
python -m pip install -r requirements-image-tools.txt
goto :done
:conda_fail
echo Failed to activate conda environment data-curation-tool.
exit /b 1
:done
echo Image enhancement dependencies installed. Commercial Topaz tools must be installed/licensed separately and configured in the Augment tab.
pause

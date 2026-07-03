@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\find_conda.bat || (pause & exit /b 1)
call scripts\activate_data_curation_env.bat || exit /b 1
python -m pip install --upgrade pip
python -m pip install -r requirements-voice.txt --upgrade || exit /b 1
echo.
echo Optional voice STT/TTS runtime packages installed.
pause

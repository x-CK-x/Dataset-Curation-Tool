@echo off
rem Activates the application Conda env from a normal Command Prompt.
if not defined DCT_ENV_NAME set "DCT_ENV_NAME=data-curation-tool"
call "%~dp0find_conda.bat" || exit /b 1
call "%DCT_CONDA_BAT%" activate "%DCT_ENV_NAME%"
exit /b %ERRORLEVEL%

@echo off
set PORT=7865
if not "%~1"=="" set PORT=%~1
powershell -ExecutionPolicy Bypass -File "%~dp0stop.ps1" -Port %PORT%
pause

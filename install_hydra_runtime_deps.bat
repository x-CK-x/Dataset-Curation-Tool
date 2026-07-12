@echo off
rem Exact fallback dependency: pyvips[binary]>=3.0.0 plus pyvips-binary>=8.16.0 and cffi>=1.17.1
setlocal EnableExtensions
cd /d "%~dp0"
set "DCT_ENV_NAME=data-curation-tool"
call scripts\find_conda.bat || (pause & exit /b 1)
call scripts\activate_data_curation_env.bat || exit /b 1

echo Repairing RedRocket Hydra 3.5 pyvips/libvips runtime dependencies in %DCT_ENV_NAME%...
echo This uses the pip pyvips-binary fallback first, then conda-forge pyvips/libvips if needed.
python scripts\repair_hydra_runtime_dependencies.py || exit /b 1
python scripts\check_hydra_runtime_dependencies.py || exit /b 1

echo.
echo Hydra runtime dependencies are installed. Restart the app, then re-run Hydra load/inference.
pause

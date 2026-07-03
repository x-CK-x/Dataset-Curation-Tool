@echo off
setlocal EnableExtensions
set "DCT_ENV_NAME=data-curation-tool"
call scripts\activate_data_curation_env.bat
if errorlevel 1 (
  echo Could not activate conda environment data-curation-tool.
  pause
  exit /b 1
)
set "FAMILY=%~1"
if "%FAMILY%"=="" set "FAMILY=basic"
python -m pip install --upgrade pip
if /I "%FAMILY%"=="basic" goto basic
if /I "%FAMILY%"=="mediapipe" goto mediapipe
if /I "%FAMILY%"=="ultralytics" goto ultralytics
if /I "%FAMILY%"=="mmpose" goto mmpose
if /I "%FAMILY%"=="mmpose-full" goto mmpose
if /I "%FAMILY%"=="all" goto basic
if /I "%FAMILY%"=="all-full" goto allfull

echo Usage: install_pose_models.bat [basic^|ultralytics^|mediapipe^|mmpose^|all-full]
echo basic/all install only the fast, reliable runtimes. mmpose/all-full are optional and can take much longer.
pause
exit /b 2

:basic
call :install_ultralytics || exit /b 1
call :install_mediapipe || exit /b 1
goto done

:allfull
call :install_ultralytics || exit /b 1
call :install_mediapipe || exit /b 1
call :install_mmpose || exit /b 1
goto done

:ultralytics
call :install_ultralytics || exit /b 1
goto done

:mediapipe
call :install_mediapipe || exit /b 1
goto done

:mmpose
call :install_mmpose || exit /b 1
goto done

:install_mediapipe
echo Installing MediaPipe Pose Landmarker runtime...
python -m pip install --upgrade --timeout 120 --retries 3 "mediapipe>=0.10.14"
exit /b %errorlevel%

:install_ultralytics
echo Installing Ultralytics YOLO pose runtime...
python -m pip install --upgrade --timeout 120 --retries 3 ultralytics
exit /b %errorlevel%

:install_mmpose
echo Installing OpenMMLab pose runtime. This optional step can be large and version-sensitive.
echo If it stalls, press Ctrl+C and use basic runtimes first; MMPose can be installed later.
python -m pip install --upgrade --timeout 120 --retries 3 "openmim>=0.3.9"
if errorlevel 1 exit /b 1
python -m mim install "mmengine>=0.10.0" "mmcv>=2.0.1" "mmdet>=3.0.0" "mmpose>=1.3.0"
exit /b %errorlevel%

:done
echo.
echo Pose runtime installation finished. Use Pose ^& 3D ^> Check Status / Download / Load.
pause

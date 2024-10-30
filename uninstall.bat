@echo off
SETLOCAL

SET ENV_NAME=data-curation
SET PATHFILE=dataset_curation_path.txt

echo Starting uninstallation of the '%ENV_NAME%' environment.

REM Check if conda is installed
IF EXIST "%UserProfile%\Miniconda3\Scripts\conda.exe" (
    echo Conda is installed.
) ELSE (
    echo Conda is not installed. Nothing to uninstall.
    GOTO :EOF
)

REM Deactivate any active conda environment
call conda deactivate

REM Check if the environment exists
call conda env list | findstr /C:"%ENV_NAME%" >nul
IF %ERRORLEVEL% EQU 0 (
    echo Removing conda environment '%ENV_NAME%'...
    call conda env remove -n "%ENV_NAME%"
) ELSE (
    echo Conda environment '%ENV_NAME%' does not exist.
)

REM Remove the Dataset-Curation-Tool directory if it exists
IF EXIST "%PATHFILE%" (
    set /p STORED_PATH=<"%PATHFILE%"
    IF EXIST "%STORED_PATH%" (
        echo Removing 'Dataset-Curation-Tool' directory at '%STORED_PATH%'...
        rmdir /S /Q "%STORED_PATH%"
    ) ELSE (
        echo Directory '%STORED_PATH%' does not exist.
    )
    del "%PATHFILE%"
)

echo Uninstallation complete.

ENDLOCAL

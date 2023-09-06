@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

SET PATHFILE=dataset_curation_path.txt

echo Check if conda command is available
IF EXIST "%UserProfile%\Miniconda3\Scripts\conda.exe" (
    echo Miniconda is already installed.
) ELSE (
    echo Miniconda is not installed. Installing now...
    REM Downloading Miniconda3 for Windows
    curl -o miniconda.exe https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    miniconda.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\Miniconda3
    DEL miniconda.exe
    SET PATH=!UserProfile!\Miniconda3;!UserProfile!\Miniconda3\Scripts;!PATH!
)

echo Check if we have a stored path
if exist "%PATHFILE%" (
    set /p STORED_PATH=<"%PATHFILE%"
    cd /d "%STORED_PATH%"
) else (
    echo Check if the current directory is "Dataset-Curation-Tool"
    IF "%cd%" NEQ "%cd:\Dataset-Curation-Tool=%" (
		echo Already in 'Dataset-Curation-Tool' directory.
	) ELSE (
        echo Check and clone the GitHub repository if not already cloned
        IF NOT EXIST Dataset-Curation-Tool (
            git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
            cd Dataset-Curation-Tool
        ) ELSE (
            echo Repository already exists. Please move to a different directory to clone again.
            timeout /t 10 /nobreak  REM Pauses the script for 10 seconds without any key interruption
            exit /b 1
        )
    )
    echo Store the current path for future use
    echo %cd% > "%PATHFILE%"
)

echo Delete the specified files
DEL /Q /F linux_run.sh mac_run.sh run.bat

echo Fetch the latest changes and tags
git fetch

echo Stash any user changes
git stash

echo Check the current tag
for /f "delims=" %%i in ('git describe --tags --exact-match 2^>nul') do set CURRENT_TAG=%%i
if NOT "%CURRENT_TAG%"=="v4.3.0" (
    git checkout tags/v4.3.0
) else (
    echo Already on tag v4.3.0.
)

echo Apply stashed user changes
git stash apply

echo Check if the conda environment already exists
call conda info --envs | findstr /C:"data-curation" >nul
if %errorlevel% neq 0 (
    call conda env create -f environment.yml
) else (
    echo Conda environment 'data-curation' already exists. Checking for updates...
    call conda env update -n data-curation -f environment.yml
)

echo Activate the conda environment
call activate data-curation

echo Run the python program with the passed arguments
python webui.py %*

ENDLOCAL

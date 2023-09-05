@echo off
SETLOCAL

SET PATHFILE=dataset_curation_path.txt

REM Check if conda command is available
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Miniconda is not installed. Installing now...
    REM Downloading Miniconda3 for Windows
    curl -o miniconda.exe https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    miniconda.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\Miniconda3
    DEL miniconda.exe
    SET PATH=%UserProfile%\Miniconda3;%UserProfile%\Miniconda3\Scripts;%PATH%
) else (
    echo Miniconda is already installed.
)

REM Check if we have a stored path
if exist "%PATHFILE%" (
    set /p STORED_PATH=<"%PATHFILE%"
    cd /d "%STORED_PATH%"
) else (
    REM Check if the current directory is "Dataset-Curation-Tool"
    IF "%cd%"=="%cd:\Dataset-Curation-Tool=%" (
        echo Already in 'Dataset-Curation-Tool' directory.
    ) ELSE (
        REM Check and clone the GitHub repository if not already cloned
        IF NOT EXIST Dataset-Curation-Tool (
            git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
            cd Dataset-Curation-Tool
        ) ELSE (
            echo Repository already exists. Please move to a different directory to clone again.
            exit /b 1
        )
    )
    REM Store the current path for future use
    echo %cd% > "%PATHFILE%"
)

REM Delete the specified files
DEL /Q /F linux_run.sh mac_run.sh run.bat

REM Fetch the latest changes and tags
git fetch

REM Stash any user changes
git stash

REM Check the current tag
for /f "delims=" %%i in ('git describe --tags --exact-match 2^>nul') do set CURRENT_TAG=%%i
if NOT "%CURRENT_TAG%"=="v4.2.7" (
    git checkout tags/v4.2.7
) else (
    echo Already on tag v4.2.7.
)

REM Apply stashed user changes
git stash apply

REM Check if the conda environment already exists
call conda info --envs | findstr /C:"data-curation" >nul
if %errorlevel% neq 0 (
    call conda env create -f environment.yml
) else (
    echo Conda environment 'data-curation' already exists. Checking for updates...
    call conda env update -n data-curation -f environment.yml
)

REM Activate the conda environment
call activate data-curation

REM Run the python program with the passed arguments
python webui.py %*

ENDLOCAL

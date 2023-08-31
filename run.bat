@echo off
setlocal

REM File to store path
set PATHFILE=dataset_curation_path.txt

REM Check if conda command is available
where conda >nul 2>nul
if %errorlevel% equ 0 (
    echo Miniconda is already installed.
) else (
    echo Miniconda is not installed. Installing now...
    REM Downloading Miniconda3 for 64-bit Windows. Adjust if needed.
    curl -o miniconda.exe https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    miniconda.exe /InstallationType=JustMe /AddToPath=1 /RegisterPython=0
    del miniconda.exe
)

REM Check if we have a stored path
if exist %PATHFILE% (
    set /p STORED_PATH=<%PATHFILE%
    cd /d %STORED_PATH%
) else (
    REM Check if current directory is "Dataset-Curation-Tool"
    if "%~n1" NEQ "Dataset-Curation-Tool" (
        REM Check and clone the GitHub repository if not already cloned
        if not exist Dataset-Curation-Tool (
            git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
        ) else (
            echo Repository already exists. Skipping clone.
        )
        cd Dataset-Curation-Tool
    ) else (
        echo Already in 'Dataset-Curation-Tool' directory.
    )
    REM Store the current path for future use
    echo %CD% > %PATHFILE%
)

REM Fetch latest changes and tags from remote
git fetch

REM Stash any user changes
git stash

REM Check the current tag
for /f "delims=" %%i in ('git describe --tags --exact-match 2^>nul') do set CURRENT_TAG=%%i
if "%CURRENT_TAG%" NEQ "v4.2.3" (
    git checkout tags/v4.2.3
) else (
    echo Already on tag v4.2.3.
)

REM Apply stashed user changes
git stash apply

REM Check if the conda environment already exists
call conda info --envs | findstr /C:"data-curation" >nul
if %errorlevel% neq 0 (
    call conda env create -f environment.yml
) else (
    echo Conda environment 'data-curation' already exists. Skipping environment creation.
)

REM Activate the conda environment
call activate data-curation

REM Run the python program with the passed arguments
python webui.py %*

endlocal

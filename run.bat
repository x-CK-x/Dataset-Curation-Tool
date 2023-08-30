@echo off

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

REM Check and clone the GitHub repository if not already cloned
if not exist Dataset-Curation-Tool (
    git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git
)

cd Dataset-Curation-Tool
call conda env create -f environment.yml

REM Activate the conda environment
call activate data-curation

REM Run the python program with the passed arguments
python webui.py %*
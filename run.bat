@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

SET PATHFILE=dataset_curation_path.txt
SET UPDATE_ENV=0

echo Check if conda command is available

IF EXIST "%UserProfile%\Miniconda3\Scripts\conda.exe" (
    echo Miniconda is already installed.
	REM Add Miniconda to the current session's PATH
	SET PATH=!UserProfile!\Miniconda3;!UserProfile!\Miniconda3\Scripts;!PATH!
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

			SET UPDATE_ENV=1
        ) ELSE (
            echo Repository already exists. Please move to a different directory to clone again.
			cd Dataset-Curation-Tool
        )
    )
    echo Store the current path for future use
    echo %cd% > "%PATHFILE%"
)

echo Delete the specified files
DEL /Q /F linux_run.sh mac_run.sh run.bat

echo Fetch the latest changes and tags
git fetch

echo Check the current tag
FOR /F "delims=" %%i IN ('git for-each-ref refs/tags --sort=-creatordate --format "%%(refname:short)" --count=1') DO SET LATEST_TAG=%%i
FOR /F "delims=" %%i IN ('git describe --tags --exact-match 2^>nul') DO SET CURRENT_TAG=%%i
IF NOT "%CURRENT_TAG%"=="%LATEST_TAG%" (
	echo Currently on %CURRENT_TAG%.

    git reset HEAD linux_run.sh mac_run.sh run.bat
	git checkout -- linux_run.sh mac_run.sh run.bat

	echo Stash any user changes
	git stash

    FOR /R . %%i IN (__pycache__) DO IF EXIST "%%i" RD /S /Q "%%i"
    FOR /R . %%i IN (*.pyc) DO IF EXIST "%%i" DEL /Q "%%i"

	echo checking out to %LATEST_TAG%.
    git checkout tags/%LATEST_TAG%

	echo Apply stashed user changes
	git stash apply

	SET UPDATE_ENV=1
) ELSE (
    echo Already on tag %LATEST_TAG%.
)

echo Check if the conda environment already exists
call conda info --envs | findstr /C:"data-curation" >nul
if %errorlevel% neq 0 (
    call conda env create -f environment.yml
) else (
	IF "%UPDATE_ENV%"=="1" (
		echo Conda environment 'data-curation' already exists. Checking for updates...
		call conda env update -n data-curation -f environment.yml
	)
)

echo Activate the conda environment
call activate data-curation

echo Run the python program with the passed arguments
python webui.py %*

IF ERRORLEVEL 1 (
    echo Error encountered. Press any key to exit.
    pause >nul
)

ENDLOCAL

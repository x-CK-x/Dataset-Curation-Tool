@echo off
SETLOCAL DISABLEDELAYEDEXPANSION

REM Ensure you run this script from a directory without special characters like '=' in its path.

echo Checking if git is available...
echo Checking if git is available... >> debug.log

where git >nul 2>nul
if errorlevel 1 (
    echo Git not found. Installing Git...
    echo Git not found. Installing Git... >> debug.log

    curl -Lo git-installer.exe "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe" --ssl-no-revoke -k >> debug.log 2>&1

    if not exist "git-installer.exe" (
        echo Failed to download Git installer - file not found
        echo Failed to download Git installer - file not found >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )

    set "Size="
    REM Using a separate code block to set Size
    for %%F in ("git-installer.exe") do (
        set "Size=%%~zF"
    )

    REM Check if Size variable is zero
    setlocal
    if "%Size%"=="0" (
        echo Git installer file is empty
        echo Git installer file is empty >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )

    echo Git installer downloaded successfully
    echo Git installer downloaded successfully >> debug.log

    echo Installing Git silently...
    echo Installing Git silently... >> debug.log
    git-installer.exe /VERYSILENT /NORESTART /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS >> debug.log 2>&1

    if errorlevel 1 (
        echo Git installation failed
        echo Git installation failed >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )

    if exist "%ProgramFiles%\Git\cmd\git.exe" (
        set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
    ) else (
        if exist "%ProgramFiles(x86)%\Git\cmd\git.exe" (
            set "PATH=%ProgramFiles(x86)%\Git\cmd;%PATH%"
        ) else (
            echo Git executable not found after installation
            echo Git executable not found after installation >> debug.log
            echo Press any key to exit.
            pause >nul
            exit /b 1
        )
    )

    where git >nul 2>nul
    if errorlevel 1 (
        echo Git still not found after installation
        echo Git still not found after installation >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )

    echo Git installed successfully
    echo Git installed successfully >> debug.log
) else (
    echo Git is already installed
    echo Git is already installed >> debug.log
)

ENDLOCAL
SETLOCAL DISABLEDELAYEDEXPANSION

set "PATHFILE=dataset_curation_path.txt"
set "UPDATE_ENV=0"

echo Use --update on the command line with the run file to update the program!
echo Use --update on the command line with the run file to update the program! >> debug.log

set "OTHER_ARGS="
for %%a in (%*) do (
    if "%%a"=="--update" (
        set "UPDATE_ENV=1"
    ) else (
        set "OTHER_ARGS=%OTHER_ARGS% %%a"
    )
)

echo Checking conda availability...
echo Checking conda availability... >> debug.log

set "CONDA_EXE=%UserProfile%\Miniconda3\Scripts\conda.exe"
if exist "%CONDA_EXE%" (
    echo Miniconda is already installed
    echo Miniconda is already installed >> debug.log
    set "PATH=%UserProfile%\Miniconda3;%UserProfile%\Miniconda3\Scripts;%PATH%"
) else (
    echo Miniconda not found. Installing Miniconda...
    echo Miniconda not found. Installing Miniconda... >> debug.log
    curl -o miniconda.exe "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" >> debug.log 2>&1
    if errorlevel 1 (
        echo Failed to download Miniconda. Check internet connection.
        echo Failed to download Miniconda. Check internet connection. >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )
    miniconda.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\Miniconda3 >> debug.log 2>&1
    if errorlevel 1 (
        echo Miniconda installation failed
        echo Miniconda installation failed >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )
    del miniconda.exe
    set "PATH=%UserProfile%\Miniconda3;%UserProfile%\Miniconda3\Scripts;%PATH%"
)

echo Checking repository path...
echo Checking repository path... >> debug.log

if exist "%PATHFILE%" (
	echo Checking the content of %PATHFILE%:
	type "%PATHFILE%" >> debug.log

	@echo off
	SETLOCAL ENABLEDELAYEDEXPANSION

	echo Checking the content of %PATHFILE%
	type "%PATHFILE%" >> debug.log

	set "PARENT_PATH="

	for /f "usebackq tokens=* delims=" %%i in ("%PATHFILE%") do (
		echo Line read: "%%i"
		set "PARENT_PATH=%%i"
	)

	echo After loop, PARENT_PATH="!PARENT_PATH!"

	if "!PARENT_PATH!"=="" (
		echo Stored path is empty. Please delete %PATHFILE% and run again.
		echo Stored path is empty. Please delete %PATHFILE% and run again. >> debug.log
		echo Press any key to exit.
		pause >nul
		exit /b 1
	)

	cd /d "!PARENT_PATH!" >> debug.log 2>&1
	if errorlevel 1 (
		echo Failed to change directory to stored path: "!PARENT_PATH!"
		echo Failed to change directory to stored path: "!PARENT_PATH!" >> debug.log
		echo Press any key to exit.
		pause >nul
		exit /b 1
	)

	echo Changed directory to stored path: %cd%
	echo Changed directory to stored path: %cd% >> debug.log
) else (
    echo No %PATHFILE% found, using current directory as parent
    echo No %PATHFILE% found, using current directory as parent >> debug.log

    REM We are already in the current directory where run.bat is located, so no need to cd again
    set "PARENT_PATH=%cd%"
    echo Using current directory as parent: %cd%
    echo Using current directory as parent: %cd% >> debug.log
)

if exist "Dataset-Curation-Tool\environment.yml" (
    echo Dataset-Curation-Tool already present
    echo Dataset-Curation-Tool already present >> debug.log
) else (
    echo Dataset-Curation-Tool not found in %cd%. Attempting to clone...
    echo Dataset-Curation-Tool not found in %cd%. Attempting to clone... >> debug.log
    git clone https://github.com/x-CK-x/Dataset-Curation-Tool.git Dataset-Curation-Tool >> debug.log 2>&1

    if errorlevel 1 (
        echo Git clone failed
        echo Git clone failed >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )
    set "UPDATE_ENV=1"
)

cd /d Dataset-Curation-Tool >> debug.log 2>&1

if not exist "environment.yml" (
    echo environment.yml not found inside Dataset-Curation-Tool
    echo environment.yml not found inside Dataset-Curation-Tool >> debug.log
    echo Press any key to exit.
    pause >nul
    exit /b 1
)

echo Verified we are inside Dataset-Curation-Tool directory: %cd%
echo Verified we are inside Dataset-Curation-Tool directory: %cd% >> debug.log

cd ..
if errorlevel 1 (
    echo Failed to go one directory up to store parent path
    echo Failed to go one directory up to store parent path >> debug.log
    echo Press any key to exit.
    pause >nul
    exit /b 1
)

echo %cd% > "%PATHFILE%"
echo Stored current path %cd% into %PATHFILE%.
echo Stored current path %cd% into %PATHFILE%. >> debug.log

cd "Dataset-Curation-Tool"
if errorlevel 1 (
    echo Failed to re-enter Dataset-Curation-Tool directory
    echo Failed to re-enter Dataset-Curation-Tool directory >> debug.log
    echo Press any key to exit.
    pause >nul
    exit /b 1
)

echo Deleting old run scripts...
echo Deleting old run scripts... >> debug.log
if exist linux_run.sh del /q /f linux_run.sh
if exist mac_run.sh del /q /f mac_run.sh
if exist run.bat del /q /f run.bat

echo Fetching latest changes and tags...
echo Fetching latest changes and tags... >> debug.log
git fetch >> debug.log 2>&1
if errorlevel 1 (
    echo Failed to fetch from git repository
    echo Failed to fetch from git repository >> debug.log
    echo Press any key to exit.
    pause >nul
    exit /b 1
)

echo Determining latest tag...
echo Determining latest tag... >> debug.log
for /f "delims=" %%i in ('git for-each-ref refs/tags --sort=-creatordate --format "%%(refname:short)" --count=1') do set "LATEST_TAG=%%i"
for /f "delims=" %%i in ('git describe --tags --exact-match 2^>nul') do set "CURRENT_TAG=%%i"

if "%CURRENT_TAG%"=="" (
    echo No current tag found - possibly a detached HEAD
    echo No current tag found - possibly a detached HEAD >> debug.log
) else (
    echo Currently on tag: %CURRENT_TAG%. Latest tag: %LATEST_TAG%.
    echo Currently on tag: %CURRENT_TAG%. Latest tag: %LATEST_TAG%. >> debug.log
)

if not "%CURRENT_TAG%"=="%LATEST_TAG%" (
    echo Not on the latest tag. Checking out to %LATEST_TAG%.
    echo Not on the latest tag. Checking out to %LATEST_TAG%. >> debug.log

    git reset HEAD linux_run.sh mac_run.sh run.bat >> debug.log 2>&1
    git checkout -- linux_run.sh mac_run.sh run.bat >> debug.log 2>&1

    echo Stashing any user changes...
    echo Stashing any user changes... >> debug.log
    git stash >> debug.log 2>&1

    echo Removing __pycache__ and pyc files
    echo Removing __pycache__ and pyc files >> debug.log
    for /r %%i in (__pycache__) do if exist "%%i" rd /s /q "%%i"
    for /r %%i in (*.pyc) do if exist "%%i" del /q "%%i"

    echo Checking out to %LATEST_TAG%...
    echo Checking out to %LATEST_TAG%... >> debug.log
    git checkout tags/%LATEST_TAG% >> debug.log 2>&1
    if errorlevel 1 (
        echo Failed to checkout to %LATEST_TAG%.
        echo Failed to checkout to %LATEST_TAG%. >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )

    echo Applying stashed user changes...
    echo Applying stashed user changes... >> debug.log
    git stash apply >> debug.log 2>&1

    set "UPDATE_ENV=1"
) else (
    echo Already on the latest tag %LATEST_TAG%
    echo Already on the latest tag %LATEST_TAG% >> debug.log
)

echo Checking if the conda environment data-curation exists...
echo Checking if the conda environment data-curation exists... >> debug.log
call conda info --envs | findstr /c:"data-curation" >nul
if errorlevel 1 (
    echo Environment data-curation not found. Creating environment...
    echo Environment data-curation not found. Creating environment... >> debug.log
    call conda env create -f environment.yml >> debug.log 2>&1
    if errorlevel 1 (
        echo Failed to create conda environment
        echo Failed to create conda environment >> debug.log
        echo Press any key to exit.
        pause >nul
        exit /b 1
    )
) else (
    if "%UPDATE_ENV%"=="1" (
        echo Environment data-curation exists. Updating environment...
        echo Environment data-curation exists. Updating environment... >> debug.log
        call conda env update -n data-curation -f environment.yml >> debug.log 2>&1
    ) else (
        echo Environment data-curation already exists and up to date
        echo Environment data-curation already exists and up to date >> debug.log
    )
)

echo Activating data-curation environment...
echo Activating data-curation environment... >> debug.log
call activate data-curation >> debug.log 2>&1
if errorlevel 1 (
    echo Failed to activate environment
    echo Failed to activate environment >> debug.log
    echo Press any key to exit.
    pause >nul
    exit /b 1
)

echo Running the python program...
echo Running the python program... >> debug.log
python webui.py%OTHER_ARGS%

echo Starting UI at http://localhost:7860
echo Starting UI at http://localhost:7860 >> debug.log
start http://localhost:7860

ENDLOCAL

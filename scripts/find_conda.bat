@echo off
rem Finds the user's PC-level Conda batch launcher and sets DCT_CONDA_BAT.
rem This works from normal Command Prompt, not only Anaconda Prompt.
if defined DCT_CONDA_BAT if exist "%DCT_CONDA_BAT%" exit /b 0
set "DCT_CONDA_BAT="
for %%C in (
  "%USERPROFILE%\miniconda3\condabin\conda.bat"
  "%USERPROFILE%\anaconda3\condabin\conda.bat"
  "%USERPROFILE%\mambaforge\condabin\conda.bat"
  "%USERPROFILE%\miniforge3\condabin\conda.bat"
  "%LOCALAPPDATA%\miniconda3\condabin\conda.bat"
  "%LOCALAPPDATA%\anaconda3\condabin\conda.bat"
  "%LOCALAPPDATA%\mambaforge\condabin\conda.bat"
  "%LOCALAPPDATA%\miniforge3\condabin\conda.bat"
  "%LOCALAPPDATA%\Programs\miniconda3\condabin\conda.bat"
  "%LOCALAPPDATA%\Programs\anaconda3\condabin\conda.bat"
  "%ProgramData%\miniconda3\condabin\conda.bat"
  "%ProgramData%\anaconda3\condabin\conda.bat"
) do (
  if not defined DCT_CONDA_BAT if exist "%%~C" set "DCT_CONDA_BAT=%%~C"
)
if not defined DCT_CONDA_BAT (
  for /f "delims=" %%C in ('where conda.bat 2^>nul') do if not defined DCT_CONDA_BAT set "DCT_CONDA_BAT=%%~C"
)
if not defined DCT_CONDA_BAT (
  for /f "delims=" %%C in ('where conda 2^>nul') do if not defined DCT_CONDA_BAT set "DCT_CONDA_BAT=%%~C"
)
if not defined DCT_CONDA_BAT (
  echo [ERROR] Conda was not found.
  echo Set DCT_CONDA_BAT to your conda.bat path, for example:
  echo   set DCT_CONDA_BAT=%%USERPROFILE%%\miniconda3\condabin\conda.bat
  exit /b 1
)
exit /b 0

@echo off
rem Nightshift setup for Windows: a private Python environment in .venv (ComfyUI's own Python is never touched),
rem the face models, the speech model for lyric timing, and ffmpeg if it is missing. Safe to run again.
setlocal
cd /d "%~dp0"
echo.
echo  NIGHTSHIFT setup
echo  ----------------

set "UV="
where uv >nul 2>nul && set "UV=uv"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"

if defined UV (
  echo  [1/4] Python environment with uv
  if not exist .venv\Scripts\python.exe "%UV%" venv .venv --python 3.12 || goto :fail
  "%UV%" pip install --python .venv\Scripts\python.exe -e . || goto :fail
) else (
  echo  [1/4] Python environment with the Python on your PATH
  if not exist .venv\Scripts\python.exe (
    py -3 -m venv .venv 2>nul || python -m venv .venv || goto :nopython
  )
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -e . || goto :fail
)

echo  [2/4] Face detection and recognition models (~40 MB)
.venv\Scripts\python.exe scripts\get_models.py || goto :fail

echo  [3/4] Speech model for lyric timing (faster-whisper small.en, ~480 MB, once)
.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8'); print('       ok')" || goto :fail

echo  [4/4] ffmpeg
where ffmpeg >nul 2>nul && (echo        ok) || (
  echo        not found: installing it with winget
  winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
  echo        close this window and open a new one so ffmpeg is on the PATH
)

echo.
echo  Done. Start the app with studio.bat
echo.
pause
exit /b 0

:nopython
echo.
echo  No Python found. Install uv (https://docs.astral.sh/uv/) or Python 3.10+ and run this again.
pause
exit /b 1

:fail
echo.
echo  Setup stopped on an error (see above).
pause
exit /b 1

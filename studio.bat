@echo off
rem Nightshift Studio: opens the app in your browser (http://127.0.0.1:8189).
rem Your own settings go in studio.local.bat next to this file (not in git), for example:
rem   set "COMFY_DIR=C:\ComfyUI_windows_portable\ComfyUI"      (renders land straight in the projects)
rem   set "COMFY_URL=http://127.0.0.1:8188"
rem   set "NIGHTSHIFT_ARGS=--host 0.0.0.0 --mcp-port 8765"       (reachable on your network; an agent can drive it over MCP)
setlocal
cd /d "%~dp0"
set "COMFY_URL=http://127.0.0.1:8188"
set "COMFY_DIR="
set "NIGHTSHIFT_ARGS="
if exist studio.local.bat call studio.local.bat
if not exist .venv\Scripts\python.exe (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
set "DIRARG="
if defined COMFY_DIR set DIRARG=--comfy-dir "%COMFY_DIR%"
.venv\Scripts\python.exe -m nightshift app --comfy-url %COMFY_URL% %DIRARG% %NIGHTSHIFT_ARGS%
pause

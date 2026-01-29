@echo off

setlocal

REM If Python is available, launch the GUI viewer; otherwise fall back to tree.
python --version >nul 2>&1
if %errorlevel%==0 (
  python "%~dp0app.py"
) else (
  echo Python not found. Falling back to tree output...
  echo.
  tree "%cd%" /f /a
  pause
)
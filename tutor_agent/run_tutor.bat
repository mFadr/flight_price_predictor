@echo off
rem Personal AI Tutor - Windows launcher. Creates the virtual environment on first run.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo Python 3.12+ was not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
        pause
        exit /b 1
    )
    echo [setup] Installing dependencies - this takes a few minutes the first time...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed. See the messages above.
        pause
        exit /b 1
    )
)

start "" ".venv\Scripts\pythonw.exe" -m tutor
endlocal

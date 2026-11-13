@echo off
title JARVIS MARK 59 - Master Setup & Environment Installer
cd /d "%~dp0"

echo ======================================================================
echo              JARVIS MARK 59 - Automated System Setup
echo ======================================================================
echo.
echo This script will automatically create virtual environments and install
echo all dependencies for both:
echo   1. Analysis Pro (OrderFlow Dashboard & Market Data Engine)
echo   2. Mark-LVI (JARVIS Voice Assistant & Multi-Agent Engine)
echo.

REM Verify Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10, 3.11, or 3.12 from https://www.python.org/
    echo CRITICAL: Ensure you check "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Python detected:
python --version
echo.

REM ---------------------------------------------------------
REM 1. Setup Analysis Pro
REM ---------------------------------------------------------
echo ======================================================================
echo [1/2] Setting up Analysis Pro (OrderFlow System)...
echo ======================================================================
cd /d "%~dp0Analysis Pro"

if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

echo [*] Upgrading pip...
.\.venv\Scripts\python.exe -m pip install --upgrade pip

echo [*] Installing Analysis Pro requirements...
.\.venv\Scripts\pip.exe install -r requirements.txt

if not exist ".env" (
    if exist ".env.example" (
        echo [*] Initializing .env configuration...
        copy ".env.example" ".env" >nul
    )
)
echo [OK] Analysis Pro setup completed!
echo.

REM ---------------------------------------------------------
REM 2. Setup Mark-LVI
REM ---------------------------------------------------------
echo ======================================================================
echo [2/2] Setting up Mark-LVI (JARVIS Assistant)...
echo ======================================================================
cd /d "%~dp0Mark-LVI"

if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

echo [*] Upgrading pip...
.\.venv\Scripts\python.exe -m pip install --upgrade pip

echo [*] Running Mark-LVI setup.py...
.\.venv\Scripts\python.exe setup.py
if errorlevel 1 (
    echo [!] setup.py had a warning/error. Running pip install -r requirements.txt...
    .\.venv\Scripts\pip.exe install -r requirements.txt
)

if not exist "config\api_keys.json" (
    if exist "config\api_keys.json.example" (
        echo [*] Initializing config\api_keys.json...
        copy "config\api_keys.json.example" "config\api_keys.json" >nul
    )
)
echo [OK] Mark-LVI setup completed!
echo.

cd /d "%~dp0"
echo ======================================================================
echo                      SETUP COMPLETED SUCCESSFULLY!
echo ======================================================================
echo.
echo Next steps:
echo   1. (Optional) Put your GEXDash API key in "Analysis Pro\.env"
echo   2. (Optional) Put your Gemini API key in "Mark-LVI\config\api_keys.json"
echo   3. Launch the system using "START_JARVIS.bat"
echo.
pause

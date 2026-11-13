@echo off
title JARVIS - Mark LVI
cd /d "%~dp0"

echo ========================================================
echo                 JARVIS MARK-LVI ASSISTANT
echo ========================================================

REM Check if Python virtual environment exists
if not exist ".\.venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Setting up environment...
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in PATH!
        echo Please install Python 3.10, 3.11, or 3.12 from python.org
        echo Make sure to check "Add python.exe to PATH" during installation.
        pause
        exit /b 1
    )
    echo [*] Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [*] Upgrading pip...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    echo [*] Running setup.py for Mark-LVI dependencies and setup...
    .\.venv\Scripts\python.exe setup.py
    if errorlevel 1 (
        echo [WARNING] setup.py encountered an issue. Falling back to requirements.txt...
        .\.venv\Scripts\pip.exe install -r requirements.txt
    )
    echo [*] Mark-LVI environment setup completed!
)

REM Setup config/api_keys.json if missing
if not exist "config\api_keys.json" (
    if exist "config\api_keys.json.example" (
        echo [*] Initializing config\api_keys.json from example...
        copy "config\api_keys.json.example" "config\api_keys.json" >nul
        echo [*] NOTE: Please edit config\api_keys.json to provide your GEMINI_API_KEY.
    )
)

echo.
echo [*] Starting JARVIS Mark LVI...
echo.
.\.venv\Scripts\python.exe main.py
pause

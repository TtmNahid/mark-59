@echo off
title OrderFlow Analysis Pro - Full System
cd /d "%~dp0"

echo ========================================================
echo       JARVIS MARK 59 - OrderFlow Analysis Pro
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
    echo [*] Installing dependencies from requirements.txt ...
    .\.venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation encountered an issue.
        pause
        exit /b 1
    )
    echo [*] Environment setup completed successfully!
)

REM Setup .env if missing
if not exist ".env" (
    if exist ".env.example" (
        echo [*] Initializing .env from .env.example ...
        copy ".env.example" ".env" >nul
        echo [*] Please configure your GEXDASH_API_KEY in .env if you have one.
    )
)

REM Kill any stale process holding port 8080
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    echo [*] Releasing port 8080 (killing PID %%a)...
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo [*] Starting OrderFlow Analysis Pro Dashboard...
echo [*] Web interface will be available at: http://localhost:8080
echo.
.\.venv\Scripts\python.exe -m orderflow_system.main
pause

@echo off
title JARVIS MARK 59 - Master Launcher
cd /d "%~dp0"

:MENU
cls
echo ======================================================================
echo                       JARVIS MARK 59 - MASTER LAUNCHER
echo ======================================================================
echo.
echo   [1] Start OrderFlow Analysis Pro Dashboard (Port 8080)
echo   [2] Start JARVIS Mark-LVI Voice AI Assistant
echo   [3] Start BOTH (OrderFlow Dashboard + JARVIS Assistant)
echo   [4] One-Click Setup / Reinstall Dependencies (SETUP_ALL.bat)
echo   [5] Exit
echo.
echo ======================================================================
set /p choice="Select an option (1-5) [Default: 3]: "

if "%choice%"=="" set choice=3
if "%choice%"=="1" goto LAUNCH_DASHBOARD
if "%choice%"=="2" goto LAUNCH_JARVIS
if "%choice%"=="3" goto LAUNCH_BOTH
if "%choice%"=="4" goto RUN_SETUP
if "%choice%"=="5" goto EXIT_SCRIPT

echo Invalid option selected.
pause
goto MENU

:LAUNCH_DASHBOARD
echo Starting OrderFlow Analysis Pro Dashboard...
start "OrderFlow Analysis Pro" cmd /c "call \"%~dp0Analysis Pro\run_orderflow.bat\""
goto MENU

:LAUNCH_JARVIS
echo Starting JARVIS Mark-LVI Assistant...
start "JARVIS Mark LVI" cmd /c "call \"%~dp0Mark-LVI\run_jarvis.bat\""
goto MENU

:LAUNCH_BOTH
echo Starting OrderFlow Analysis Pro Dashboard...
start "OrderFlow Analysis Pro" cmd /c "call \"%~dp0Analysis Pro\run_orderflow.bat\""
timeout /t 3 /nobreak >nul
echo Starting JARVIS Mark-LVI Assistant...
start "JARVIS Mark LVI" cmd /c "call \"%~dp0Mark-LVI\run_jarvis.bat\""
goto MENU

:RUN_SETUP
call "%~dp0SETUP_ALL.bat"
goto MENU

:EXIT_SCRIPT
exit /b 0

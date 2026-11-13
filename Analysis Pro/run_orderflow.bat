@echo off
title OrderFlow Analysis Pro - Full System
cd /d "%~dp0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
echo Starting OrderFlow Analysis Pro...
.\.venv\Scripts\python.exe -m orderflow_system.main
pause


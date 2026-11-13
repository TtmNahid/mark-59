@echo off
title OrderFlow Analysis Pro - Demo Mode
cd /d "%~dp0"
echo Starting OrderFlow Dashboard in Demo Mode on http://localhost:8080 ...
.\.venv\Scripts\python.exe -m orderflow_system.dashboard
pause


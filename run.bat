@echo off
title Weather Context AI Server
echo ========================================================
echo   Starting Weather Context AI...
echo ========================================================
echo.
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

:: Start Uvicorn server
echo Server starting at http://localhost:8000
echo Press Ctrl+C in this window anytime to stop the server.
echo.
python -m uvicorn main:app --reload --port 8000
pause

@echo off
REM Set code page to UTF-8
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Quick startup script for Windows

echo Draw ^& Guess Game Startup Script
echo ================================

REM Check virtual environment
if not exist "venv" (
    echo Virtual environment not found, creating...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)

REM Set paths
set "PYTHON=venv\Scripts\python.exe"
set "PIP=venv\Scripts\pip.exe"

REM Check dependencies
echo Checking dependencies...
"%PIP%" install -q -r requirements.txt

REM Default: start client directly (no mode selection)
echo.
echo Starting client...
"%PYTHON%" src\client\main.py

endlocal

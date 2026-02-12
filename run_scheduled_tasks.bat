@echo off
REM Silver Tier AI Employee Scheduled Tasks Runner
REM This script starts the scheduler service for the Silver Tier AI Employee

echo Starting Silver Tier AI Employee Scheduler...
echo ==============================================

REM Change to the project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install required packages if not already installed
echo Installing required packages...
pip install schedule psutil

REM Start the scheduler
echo Starting scheduler...
python scheduler.py

echo Scheduler stopped.
pause
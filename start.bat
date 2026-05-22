@echo off
REM Real Time USB Activity Logger - Quick Start Script
REM This batch file automates the setup and launch process

echo ========================================
echo Real Time USB Activity Logger - QUICK START
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.x from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detected
echo.

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import wmi" >nul 2>&1
if errorlevel 1 (
    echo [!] Dependencies not found. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependencies already installed
)

echo.
echo ========================================
echo LAUNCHING Real Time USB Activity Logger...
echo ========================================
echo.

REM Launch the application
python main.py

REM If application exits with error
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error!
    pause
)

@echo off
REM Audio Dump Monitor Startup Script for Windows
REM This script checks prerequisites and starts the monitor

echo ========================================
echo   Audio Dump Monitor
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7 or later from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Check if adb is available
adb version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ADB is not installed or not in PATH
    echo Please install Android SDK Platform Tools
    echo Download from: https://developer.android.com/studio/releases/platform-tools
    pause
    exit /b 1
)

echo [OK] ADB found

REM Check for connected devices
echo.
echo Checking for connected devices...
adb devices

adb get-state >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] No device connected!
    echo Please connect an Android device and enable USB debugging.
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b 1
)

echo [OK] Device connected
echo.

REM Create output directory if not exists
if not exist "audio_dumps" mkdir audio_dumps

REM Start the monitor
echo Starting Audio Dump Monitor...
echo Press Ctrl+C to stop
echo.

python audio_dump_monitor.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Monitor exited with error
    pause
)

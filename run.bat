@echo off
REM Quick start script for Web Application Honeypot (Windows)
REM This script sets up and runs the honeypot with proper warnings

echo ==================================================================
echo 🍯 WEB APPLICATION HONEYPOT - QUICK START
echo ==================================================================
echo.
echo ⚠️  SECURITY WARNING:
echo    This honeypot is for LAB/EDUCATIONAL USE ONLY!
echo    Do not expose to public internet without proper isolation.
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

echo ✅ Python found

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -q -r requirements.txt

REM Create data directory if it doesn't exist
if not exist "honeypot\data" (
    echo 📁 Creating data directory...
    mkdir honeypot\data
)

echo.
echo 🚀 Starting honeypot...
echo    - Access at: http://127.0.0.1:8080/login
echo    - Logs will be written to: honeypot\data\web_honeypot.jsonl
echo    - Press Ctrl+C to stop
echo.
echo ==================================================================

REM Start the honeypot
python -m honeypot.webapp

echo.
echo 🛑 Honeypot stopped
pause
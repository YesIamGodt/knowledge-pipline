@echo off
REM LLM Wiki Agent - Demo Launcher (Windows)

echo ========================================
echo LLM Wiki Agent - Demo Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Launch the demo
echo.
echo Starting demo server...
echo URL: http://localhost:5000
echo Press Ctrl+C to stop
echo.
python demo\app.py

pause

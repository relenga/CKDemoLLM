@echo off
REM Backend Startup Script for CK LangGraph
REM This script ensures we're in the correct directory and starts the FastAPI server

echo ================================
echo   CK LangGraph Backend Startup
echo ================================

REM Change to the directory where this script is located (backend folder)
cd /d "%~dp0"

echo Starting backend from: %CD%
echo Timestamp: %date% %time%

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Expected: venv\Scripts\python.exe
    pause
    exit /b 1
)

echo Starting FastAPI server with Part Matching Engine...
echo Server will be available at: http://localhost:8002
echo Press Ctrl+C to stop the server
echo.

REM Start the server
"venv\Scripts\python.exe" main.py

echo.
echo Backend server stopped.
pause
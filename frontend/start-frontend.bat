@echo off
REM Frontend Startup Script for CK LangGraph
REM This script ensures we're in the correct directory and starts the React dev server

echo ================================
echo   CK LangGraph Frontend Startup
echo ================================

REM Change to the directory where this script is located (frontend folder)
cd /d "%~dp0"

echo Starting frontend from: %CD%
echo Timestamp: %date% %time%

REM Check if package.json exists
if not exist "package.json" (
    echo ERROR: package.json not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo WARNING: node_modules not found. Running npm install first...
    npm install
    if errorlevel 1 (
        echo ERROR: npm install failed
        pause
        exit /b 1
    )
)

echo Starting React development server...
echo Server will be available at: http://localhost:3001
echo Press Ctrl+C to stop the server
echo.

REM Start the development server
npm start

echo.
echo Frontend server stopped.
pause
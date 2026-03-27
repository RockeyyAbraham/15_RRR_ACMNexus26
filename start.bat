@echo off
echo ================================================================================
echo SENTINEL - ONE-CLICK STARTUP
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Installing frontend dependencies...
cd ..\frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Testing backend imports...
cd ..\backend
python test_imports.py
if errorlevel 1 (
    echo [ERROR] Backend imports failed
    pause
    exit /b 1
)

echo.
echo [4/4] Starting backend server...
start "Sentinel Backend" cmd /k "python api/main.py"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo [5/5] Starting frontend server...
cd ..\frontend
start "Sentinel Frontend" cmd /k "npm run dev"

echo.
echo ================================================================================
echo SENTINEL STARTED SUCCESSFULLY!
echo ================================================================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Two new windows have opened:
echo   1. Sentinel Backend  - Flask API server
echo   2. Sentinel Frontend - React development server
echo.
echo Check those windows for any errors.
echo.
echo To stop: Close both terminal windows or press Ctrl+C in each
echo.
echo Error logs: backend\logs\error.log
echo.
pause

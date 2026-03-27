# Sentinel - One-Click Startup Script (PowerShell)
# Run this with: .\start.ps1

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "SENTINEL - ONE-CLICK STARTUP" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[CHECK] Verifying Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found. Install Python 3.10+ from https://www.python.org/" -ForegroundColor Red
    pause
    exit 1
}

# Check Node.js
Write-Host "[CHECK] Verifying Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found. Install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "[1/4] Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to install backend dependencies" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  ✓ Backend dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location ..\frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to install frontend dependencies" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Starting backend server..." -ForegroundColor Yellow
Set-Location ..\backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python api/main.py"
Write-Host "  ✓ Backend starting in new window..." -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] Starting frontend server..." -ForegroundColor Yellow
Set-Location ..\frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
Write-Host "  ✓ Frontend starting in new window..." -ForegroundColor Green

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "SENTINEL STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Two new windows have opened:" -ForegroundColor White
Write-Host "  1. Backend  - Flask API server" -ForegroundColor White
Write-Host "  2. Frontend - React development server" -ForegroundColor White
Write-Host ""
Write-Host "Check those windows for any errors." -ForegroundColor Yellow
Write-Host ""
Write-Host "Error logs: backend\logs\error.log" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to close this window..." -ForegroundColor Gray
pause

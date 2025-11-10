# Image Verifier API - Startup Script
# This script activates the virtual environment and starts the server

Write-Host "🚀 Starting Image Verifier API..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file. Please configure it before running." -ForegroundColor Green
    Write-Host ""
}

# Check if dependencies are installed
Write-Host "📚 Checking dependencies..." -ForegroundColor Cyan
$pipList = pip list
if ($pipList -notmatch "fastapi") {
    Write-Host "⚠️  Dependencies not installed. Installing now..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "✓ Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

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

# Check if activation was successful
if (-Not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Failed to activate virtual environment!" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    $envExampleExists = Test-Path ".env.example"
    if ($envExampleExists) {
        Copy-Item .env.example .env
        Write-Host "✓ Created .env file. Please configure it before running." -ForegroundColor Green
        Write-Host ""
    }
    else {
        Write-Host "❌ .env.example file not found!" -ForegroundColor Red
        exit 1
    }
}

# Check if requirements.txt exists
if (-Not (Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt file not found!" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host "📚 Checking dependencies..." -ForegroundColor Cyan
$pipList = & python -m pip list --format=freeze 2>$null
if (-Not ($pipList -match "fastapi")) {
    Write-Host "⚠️  Dependencies not installed. Installing now..." -ForegroundColor Yellow
    & python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
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
& python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
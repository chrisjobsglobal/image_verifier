# Image Verifier API - Setup Script
# This script sets up the development environment

Write-Host "🔧 Setting up Image Verifier API..." -ForegroundColor Green
Write-Host ""

# Check Python version
Write-Host "1️⃣  Checking Python version..." -ForegroundColor Cyan
$pythonVersion = python --version
Write-Host "   Found: $pythonVersion" -ForegroundColor White

if ($pythonVersion -notmatch "Python 3\.[9-9]|Python 3\.1[0-9]") {
    Write-Host "   ⚠️  Python 3.9+ recommended" -ForegroundColor Yellow
}

# Create virtual environment
Write-Host ""
Write-Host "2️⃣  Creating virtual environment..." -ForegroundColor Cyan
if (Test-Path ".venv") {
    Write-Host "   ℹ️  Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv .venv
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "3️⃣  Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1
Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "4️⃣  Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip
Write-Host "   ✓ pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "5️⃣  Installing dependencies..." -ForegroundColor Cyan
Write-Host "   This may take several minutes..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "   ❌ Error installing dependencies" -ForegroundColor Red
    Write-Host "   See above for details" -ForegroundColor Yellow
}

# Create .env file
Write-Host ""
Write-Host "6️⃣  Setting up configuration..." -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "   ℹ️  .env file already exists" -ForegroundColor Yellow
} else {
    Copy-Item .env.example .env
    Write-Host "   ✓ Created .env file from template" -ForegroundColor Green
}

# Check Tesseract installation
Write-Host ""
Write-Host "7️⃣  Checking Tesseract OCR..." -ForegroundColor Cyan
try {
    $tesseractVersion = tesseract --version 2>&1 | Select-String "tesseract" | Select-Object -First 1
    Write-Host "   ✓ Tesseract found: $tesseractVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Tesseract OCR not found!" -ForegroundColor Red
    Write-Host "   Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
    Write-Host "   After installation, update TESSERACT_CMD in .env" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✨ Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Configure .env file (especially TESSERACT_CMD path)" -ForegroundColor White
Write-Host "  2. Run: .\start.ps1" -ForegroundColor White
Write-Host "  3. Visit: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor White
Write-Host "  pytest tests/ -v" -ForegroundColor White
Write-Host ""
Write-Host "For help, see README.md" -ForegroundColor White
Write-Host ""

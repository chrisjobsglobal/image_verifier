# Install Dependencies Script
# Run this in a fresh PowerShell window

Write-Host "🔧 Installing Image Verifier Dependencies..." -ForegroundColor Green
Write-Host ""

# Activate venv
Write-Host "1️⃣  Activating Python 3.11 virtual environment..." -ForegroundColor Cyan
& C:\projects\backend\image_verifier\.venv\Scripts\Activate.ps1

# Verify Python version
$pyVersion = & C:\projects\backend\image_verifier\.venv\Scripts\python.exe --version
Write-Host "   Using: $pyVersion" -ForegroundColor White

if ($pyVersion -notmatch "3\.11") {
    Write-Host "   ❌ Wrong Python version!" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "2️⃣  Upgrading pip..." -ForegroundColor Cyan
& C:\projects\backend\image_verifier\.venv\Scripts\python.exe -m pip install --upgrade pip wheel

# Install core dependencies
Write-Host ""
Write-Host "3️⃣  Installing core dependencies..." -ForegroundColor Cyan
& C:\projects\backend\image_verifier\.venv\Scripts\pip.exe install fastapi uvicorn[standard] python-multipart pydantic pydantic-settings opencv-python Pillow numpy pytesseract PassportEye aiofiles httpx pytest pytest-asyncio pytest-cov python-decouple python-json-logger

# Try dlib from pre-built wheel
Write-Host ""
Write-Host "4️⃣  Installing dlib (pre-built wheel)..." -ForegroundColor Cyan
& C:\projects\backend\image_verifier\.venv\Scripts\pip.exe install https://github.com/sachadee/Dlib/raw/main/dlib-19.24.0-cp311-cp311-win_amd64.whl

# Install face_recognition
Write-Host ""
Write-Host "5️⃣  Installing face_recognition..." -ForegroundColor Cyan
& C:\projects\backend\image_verifier\.venv\Scripts\pip.exe install face-recognition

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: MediaPipe is not available for Windows Python 3.11" -ForegroundColor Yellow
Write-Host "The service will use OpenCV-based face detection instead" -ForegroundColor Yellow
Write-Host ""

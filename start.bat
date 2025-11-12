@echo off
REM Image Verifier API - Startup Script
REM This script activates the virtual environment and starts the server

echo.
echo Starting Image Verifier API...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found. Creating from .env.example...
    if exist ".env.example" (
        copy .env.example .env
        echo Created .env file. Please configure it before running.
        echo.
    ) else (
        echo [ERROR] .env.example file not found!
        exit /b 1
    )
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt file not found!
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -m pip list --format=freeze | findstr "fastapi" >nul
if errorlevel 1 (
    echo [WARNING] Dependencies not installed. Installing now...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        exit /b 1
    )
)

echo.
echo Environment ready!
echo.
echo Starting FastAPI server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

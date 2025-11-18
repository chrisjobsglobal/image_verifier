#!/bin/bash

# Image Verifier Service Restart Script
# This script stops and restarts the FastAPI image verification service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv310"
LOG_FILE="$SCRIPT_DIR/uvicorn.log"
PORT=27000

echo "🔄 Restarting Image Verifier Service..."

# Stop existing service
echo "⏹️  Stopping existing service..."
pkill -f "uvicorn app.main:app"
sleep 2

# Check if service is still running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "⚠️  Service still running, forcing shutdown..."
    pkill -9 -f "uvicorn app.main:app"
    sleep 1
fi

# Start service
echo "▶️  Starting service on port $PORT..."
cd "$SCRIPT_DIR"
nohup "$VENV_PATH/bin/uvicorn" app.main:app --host 0.0.0.0 --port $PORT > "$LOG_FILE" 2>&1 &

# Wait for service to start
sleep 3

# Check if service is running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    PID=$(pgrep -f "uvicorn app.main:app")
    echo "✅ Service started successfully (PID: $PID)"
    echo "📝 Logs: $LOG_FILE"
    echo "🌐 URL: https://document-verifier.jobsglobal.com"
    echo ""
    echo "Check health:"
    echo "  curl http://localhost:$PORT/health"
    echo ""
    echo "View logs:"
    echo "  tail -f $LOG_FILE"
else
    echo "❌ Failed to start service"
    echo "Check logs for errors:"
    echo "  tail -50 $LOG_FILE"
    exit 1
fi

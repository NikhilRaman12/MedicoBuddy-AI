#!/usr/bin/env bash
set -e

echo "Starting MedicoBuddy AI container services..."

# 1. Start FastAPI backend internally on 127.0.0.1:8000
python -m uvicorn medicobuddy.main:app --host 127.0.0.1 --port 8000 --workers 2 &
API_PID=$!

echo "FastAPI server started with PID $API_PID. Waiting for internal API readiness..."

# 2. Poll internal readiness endpoint
MAX_RETRIES=30
RETRY_COUNT=0
READY=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if curl -s http://127.0.0.1:8000/health/live > /dev/null; then
    echo "Internal FastAPI service is live and ready!"
    READY=1
    break
  fi
  echo "Waiting for FastAPI to be live... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
  sleep 1
  RETRY_COUNT=$((RETRY_COUNT+1))
done

# Signal handler for clean process shutdown
cleanup() {
  echo "Stopping MedicoBuddy AI container processes..."
  kill -TERM "$API_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# 3. Start Streamlit frontend bound publicly on 0.0.0.0:7860
echo "Starting Streamlit UI on 0.0.0.0:7860..."
streamlit run frontend/app.py --server.port 7860 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

wait $STREAMLIT_PID

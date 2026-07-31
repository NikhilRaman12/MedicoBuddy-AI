#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# MedicoBuddy AI — Hugging Face Spaces Supervisor Script
#
# Manages all services inside a single container:
#   1. PostgreSQL (localhost:5432)
#   2. Neo4j Community (localhost:7687)
#   3. Evidence ingestion (one-shot)
#   4. FastAPI backend (127.0.0.1:8000)
#   5. Streamlit frontend (0.0.0.0:7860)
# ──────────────────────────────────────────────────────────────

set -e

echo "═══════════════════════════════════════════════"
echo "  MedicoBuddy AI — HF Spaces Bootstrap"
echo "═══════════════════════════════════════════════"

# Signal handler
cleanup() {
    echo "Stopping MedicoBuddy AI container processes..."
    kill "$STREAMLIT_PID" 2>/dev/null || true
    kill "$API_PID" 2>/dev/null || true
    kill "$NEO4J_PID" 2>/dev/null || true
    pg_ctlcluster 16 main stop 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── 1. Start PostgreSQL ─────────────────────────────────────
echo "Starting PostgreSQL 16..."
pg_ctlcluster 16 main start || {
    # Initialize if needed
    pg_createcluster 16 main --start || true
}

# Wait for PostgreSQL
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if pg_isready -q 2>/dev/null; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 1
done

# Create database and user
su - postgres -c "psql -c \"CREATE USER ${POSTGRES_USER:-medicobuddy_internal} WITH PASSWORD '${POSTGRES_PASSWORD:-medicobuddy_dev}';\"" 2>/dev/null || true
su - postgres -c "psql -c \"CREATE DATABASE ${POSTGRES_DB:-medicobuddy} OWNER ${POSTGRES_USER:-medicobuddy_internal};\"" 2>/dev/null || true
su - postgres -c "psql -d ${POSTGRES_DB:-medicobuddy} -c 'CREATE EXTENSION IF NOT EXISTS vector;'" 2>/dev/null || true

# ── 2. Start Neo4j Community ────────────────────────────────
echo "Starting Neo4j Community Edition..."
neo4j start &
NEO4J_PID=$!

RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅ Neo4j is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   Waiting for Neo4j... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

# ── 3. Run ingestion if needed ──────────────────────────────
INGESTION_REPORT="evidence/reports/ingestion_report.json"

if [ ! -f "$INGESTION_REPORT" ]; then
    echo "📄 Running initial evidence ingestion..."
    python scripts/ingest_sources.py || {
        echo "⚠️  Ingestion failed — continuing with empty index"
    }
else
    echo "ℹ️  Existing ingestion report found. Skipping re-ingestion."
fi

# ── 4. Start FastAPI backend ────────────────────────────────
echo "Starting FastAPI backend on 127.0.0.1:8000..."
python -m uvicorn medicobuddy.main:app --host 127.0.0.1 --port 8000 --workers 1 &
API_PID=$!

# Wait for FastAPI readiness
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://127.0.0.1:8000/health/live > /dev/null 2>&1; then
        echo "✅ FastAPI backend is live"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   Waiting for FastAPI... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

# ── 5. Start Streamlit on 0.0.0.0:7860 ─────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo "  Evidence Service Online — Starting UI"
echo "  URL: http://0.0.0.0:7860"
echo "═══════════════════════════════════════════════"
echo ""

export API_BASE=http://127.0.0.1:8000/api/v1
export HEALTH_URL=http://127.0.0.1:8000/health/ready

streamlit run frontend/app.py \
    --server.port 7860 \
    --server.address 0.0.0.0 \
    --server.headless true &
STREAMLIT_PID=$!

wait $STREAMLIT_PID

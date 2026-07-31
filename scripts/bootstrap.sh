#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# MedicoBuddy AI — Bootstrap Script
#
# This script is the Docker entrypoint for the FastAPI container.
# It waits for databases, runs ingestion, smoke tests, and starts the server.
# ──────────────────────────────────────────────────────────────

set -e

echo "═══════════════════════════════════════════════"
echo "  MedicoBuddy AI — Bootstrap Sequence"
echo "═══════════════════════════════════════════════"

# ── 1. Verify GROQ_API_KEY ──────────────────────────────────
if [ -z "${GROQ_API_KEY}" ] || [ "${GROQ_API_KEY}" = "gsk_CHANGE_ME_GROQ_API_KEY" ]; then
    echo "⚠️  WARNING: GROQ_API_KEY is not set or is a placeholder."
    echo "   Set it in your .env file: GROQ_API_KEY=gsk_your_key_here"
    echo "   The system will start but LLM generation will fail."
fi

# ── 2. Generate internal credentials if absent ───────────────
if [ -z "${POSTGRES_PASSWORD}" ]; then
    export POSTGRES_PASSWORD="medicobuddy_dev"
    echo "ℹ️  Using default POSTGRES_PASSWORD for development"
fi

if [ -z "${NEO4J_PASSWORD}" ]; then
    export NEO4J_PASSWORD="medicobuddy_dev"
    echo "ℹ️  Using default NEO4J_PASSWORD for development"
fi

if [ -z "${APP_SECRET_KEY}" ]; then
    export APP_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    echo "ℹ️  Generated APP_SECRET_KEY"
fi

# ── 3. Wait for PostgreSQL readiness ────────────────────────
POSTGRES_HOST="${POSTGRES_HOST:-medicobuddy-postgres-pgvector}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-medicobuddy}"
POSTGRES_USER="${POSTGRES_USER:-medicobuddy_internal}"

echo "⏳ Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
MAX_RETRIES=60
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${POSTGRES_HOST}', ${POSTGRES_PORT}))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "✅ PostgreSQL is reachable"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   Retry ${RETRY_COUNT}/${MAX_RETRIES}..."
    sleep 2
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "❌ PostgreSQL not reachable after ${MAX_RETRIES} retries. Exiting."
    exit 1
fi

# ── 4. Wait for Neo4j readiness ─────────────────────────────
NEO4J_HOST="${NEO4J_URI:-bolt://medicobuddy-neo4j-community:7687}"
# Extract host from bolt://host:port
NEO4J_HOST_CLEAN=$(echo "$NEO4J_HOST" | sed 's|bolt://||' | cut -d: -f1)
NEO4J_PORT_CLEAN=$(echo "$NEO4J_HOST" | sed 's|bolt://||' | cut -d: -f2)

echo "⏳ Waiting for Neo4j at ${NEO4J_HOST_CLEAN}:${NEO4J_PORT_CLEAN}..."
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${NEO4J_HOST_CLEAN}', ${NEO4J_PORT_CLEAN}))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo "✅ Neo4j is reachable"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "   Retry ${RETRY_COUNT}/${MAX_RETRIES}..."
    sleep 2
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "⚠️  Neo4j not reachable after ${MAX_RETRIES} retries. Proceeding without graph."
fi

# ── 5. Check if ingestion is needed ─────────────────────────
INGESTION_REPORT="evidence/reports/ingestion_report.json"

if [ -f "$INGESTION_REPORT" ]; then
    VECTORS_WRITTEN=$(python -c "import json; d=json.load(open('$INGESTION_REPORT')); print(d.get('vectors_written', 0))" 2>/dev/null || echo "0")
    if [ "$VECTORS_WRITTEN" -gt "0" ] 2>/dev/null; then
        echo "ℹ️  Existing ingestion report found (${VECTORS_WRITTEN} vectors). Skipping re-ingestion."
        echo "   Use --rebuild flag to force re-ingestion."
    else
        echo "📄 Ingestion report found but 0 vectors. Running ingestion..."
        python scripts/ingest_sources.py --rebuild || {
            echo "⚠️  Ingestion failed. Server will start but search will return empty results."
        }
    fi
else
    echo "📄 No ingestion report found. Running initial evidence ingestion..."
    python scripts/ingest_sources.py || {
        echo "⚠️  Ingestion failed. Server will start but search will return empty results."
    }
fi

# ── 6. Report readiness status ──────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo "  Bootstrap Complete — Starting FastAPI Server"
echo "═══════════════════════════════════════════════"
echo ""
echo "  API:      http://0.0.0.0:${API_PORT:-8000}"
echo "  Docs:     http://0.0.0.0:${API_PORT:-8000}/docs"
echo "  Health:   http://0.0.0.0:${API_PORT:-8000}/health/ready"
echo ""

# ── 7. Start FastAPI ────────────────────────────────────────
exec python -m uvicorn medicobuddy.main:app \
    --host "${API_HOST:-0.0.0.0}" \
    --port "${API_PORT:-8000}" \
    --workers 1 \
    --log-level info

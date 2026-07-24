# MedicoBuddy — Multi-stage Dockerfile
FROM python:3.12-slim AS base

# Security: run as non-root
RUN groupadd -r medicobuddy && useradd -r -g medicobuddy -d /app -s /sbin/nologin medicobuddy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies stage ───────────────────────────────────────
FROM base AS deps

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ── Application stage ────────────────────────────────────────
FROM deps AS app

COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Change ownership
RUN chown -R medicobuddy:medicobuddy /app

USER medicobuddy

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "medicobuddy.main:app", "--host", "0.0.0.0", "--port", "8000"]

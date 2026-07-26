# MedicoBuddy AI — Multi-stage Production Dockerfile for Hugging Face Spaces (Port 7860)
FROM python:3.12-slim AS base

# Security: non-root user creation
RUN groupadd -r medicobuddy && useradd -r -g medicobuddy -d /app -s /bin/bash medicobuddy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies Stage ──────────────────────────────────────
FROM base AS deps

# Copy packaging manifests and package source first for pip build
COPY pyproject.toml README.md requirements.txt ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir .

# ── Application Stage ───────────────────────────────────────
FROM deps AS app

COPY evidence/ ./evidence/
COPY scripts/ ./scripts/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Set executable permissions on startup script
RUN chmod +x ./scripts/start_space.sh \
    && chown -R medicobuddy:medicobuddy /app

USER medicobuddy

ENV PORT=7860
ENV API_BASE=http://127.0.0.1:8000/api/v1
ENV HEALTH_URL=http://127.0.0.1:8000/health/ready

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/live || exit 1

EXPOSE 7860

CMD ["./scripts/start_space.sh"]

# ──────────────────────────────────────────────────────────────
# MedicoBuddy AI — Multi-stage Dockerfile
#
# Stage 1: builder — install dependencies, download Qwen3 model
# Stage 2: runtime — minimal image with pre-cached model
# ──────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Qwen3-Embedding-0.6B into model cache during build
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
m = SentenceTransformer('Qwen/Qwen3-Embedding-0.6B', trust_remote_code=True); \
print(f'Qwen3-Embedding-0.6B cached (dim={m.get_sentence_embedding_dimension()})')"


# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget bash libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy pre-cached Qwen3 model
COPY --from=builder /root/.cache /root/.cache

# Copy application source
COPY . .

# Install the application package
RUN pip install --no-cache-dir --no-deps -e .

# Ensure scripts are executable
RUN chmod +x scripts/*.sh 2>/dev/null || true

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Default: bootstrap + FastAPI
EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "medicobuddy.main:app", "--host", "0.0.0.0", "--port", "8000"]

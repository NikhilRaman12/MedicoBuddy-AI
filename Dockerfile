# Multi-Stage Production Docker Image for MedicoBuddy AI
FROM node:24-slim AS frontend-builder
WORKDIR /app/frontend-react
COPY frontend-react/package*.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=7860 \
    HOME=/tmp \
    HF_HOME=/tmp/hf_home \
    TRANSFORMERS_CACHE=/tmp/hf_home \
    PYTHONPATH=/app/src:$PYTHONPATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-install CPU-only PyTorch to reduce image size and prevent build timeouts
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY --from=frontend-builder /app/frontend-react/dist /app/frontend-react/dist
COPY scripts/ /app/scripts/
COPY evidence/ /app/evidence/
COPY .env.example /app/.env

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "medicobuddy.main:app", "--host", "0.0.0.0", "--port", "7860"]

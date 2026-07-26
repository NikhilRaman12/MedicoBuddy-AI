# MedicoBuddy AI — Hugging Face Spaces Deployment Guide

## Setup Instructions

1. **Create Docker Space:** Create a new Space on Hugging Face using `sdk: docker`.
2. **Configure Port:** Ensure `app_port: 7860` is set in Space metadata.
3. **Configure Environment Secrets:** Add required secrets under Space Settings:
   - `GROQ_API_KEY`
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
   - `MILVUS_URI`, `MILVUS_TOKEN`
   - `POSTGRES_DSN`
   - `NCBI_API_KEY`, `NCBI_EMAIL`, `NCBI_TOOL_NAME`
4. **Push Repository:** Push repository root. The container will build automatically using the multi-stage `Dockerfile` and start Streamlit on port 7860 after internal FastAPI readiness.

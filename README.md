---
title: MedicoBuddy AI
emoji: 🩺
colorFrom: blue
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# MedicoBuddy AI — Everyday health questions, connected to clearer evidence.

MedicoBuddy AI is an evidence-grounded, safety-first preventive self-care education assistant for adults aged 18–65. Built with LangGraph, Neo4j, PostgreSQL `pgvector`, Groq LLM inference, Model Context Protocol (MCP) data connectors, and a production React.js + TypeScript web application.

## Architecture

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (`frontend-react/`), served static from FastAPI at `/`
- **Backend API**: FastAPI REST endpoints (`/api/v1/chat`, `/health/*`)
- **Orchestration**: LangGraph 15-Node Evidence & Entailment State Machine
- **Knowledge Graph**: Neo4j Community Database
- **Vector Search**: PostgreSQL `pgvector` with local FAISS fallback
- **Embeddings**: `Qwen/Qwen3-Embedding-0.6B` local embedding provider
- **LLM Engine**: Groq API (`GroqStructuredResponse` Pydantic models)
- **Protocol**: Official Model Context Protocol (MCP) Client Adapter

## Deployment Target

Deployed on **Hugging Face Docker Spaces** on single same-origin port **7860**:
- **Secret Required**: `GROQ_API_KEY`

## Local Development

```bash
# 1. Install Python package in editable mode
pip install -e .

# 2. Build React frontend bundle
cd frontend-react
npm install
npm run build
cd ..

# 3. Start FastAPI server (serves API + React SPA at http://localhost:8000)
python -m uvicorn medicobuddy.main:app --host 0.0.0.0 --port 8000
```

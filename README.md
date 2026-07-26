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

MedicoBuddy AI is an evidence-grounded, safety-first preventive self-care education assistant for adults aged 18–65. Built with LangGraph, Neo4j, Milvus, PostgreSQL pgvector, Groq LLM inference, and Model Context Protocol (MCP) data connectors.

## Architecture

- **Orchestration**: LangGraph 13-Node Evidence & Entailment State Machine
- **Knowledge Graph**: Neo4j Graph Database
- **Vector DB**: Milvus (Primary) + PostgreSQL `pgvector` (Failover)
- **Embeddings**: `Qwen/Qwen3-Embedding-8B`
- **LLM Engine**: Groq API (`ChatGroq` with `llama-3.3-70b-versatile`)
- **Protocol**: Official Model Context Protocol (MCP) Server & Client Adapter
- **Data Connectors**: PubMed, MedlinePlus XML, ClinicalTrials.gov, Crossref, Local Evidence Registry
- **Frontend**: Streamlit Multilingual Enterprise Workstation (22 Scheduled Indian Languages + BCP-47 Global Auto-detect)

## Required Environment Variables

To deploy on Hugging Face Spaces or run locally, configure these secrets:

- `GROQ_API_KEY`: Groq API Key
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j connection
- `MILVUS_URI`, `MILVUS_TOKEN`: Milvus Standalone connection
- `POSTGRES_DSN`: PostgreSQL pgvector DSN
- `NCBI_API_KEY`, `NCBI_EMAIL`, `NCBI_TOOL_NAME`: NCBI MCP parameters
- `QWEN_EMBEDDING_ENDPOINT`, `HF_TOKEN`: Managed Qwen embedding inference

## Local Development & Ingestion

```bash
# 1. Install package in editable mode
pip install -e .

# 2. Run evidence ingestion pipeline
python scripts/ingest_sources.py

# 3. Execute unit & safety test suite
python -m pytest tests/ -v

# 4. Launch full container environment
docker-compose up --build
```

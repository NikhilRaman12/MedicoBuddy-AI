---
title: MediBuddy AI Workstation
emoji: 🩺
colorFrom: blue
colorTo: cyan
sdk: streamlit
app_file: frontend/app.py
pinned: false
---

# MediBuddy AI — Enterprise Clinical Intelligence Workstation

"Clinical weightlessness through intelligent, trace-backed automation."

MediBuddy AI is an evidence-grounded GraphRAG clinical decision-support application built with LangGraph, Neo4j, Milvus Standalone, pgvector, and Groq LLM inference.

## Architecture

- **Orchestration**: LangGraph 12-Node Evidence Pipeline
- **Knowledge Graph**: Neo4j Graph Database
- **Vector DB**: Milvus Standalone + PostgreSQL `pgvector`
- **LLM Engine**: Groq API (`ChatGroq` with `llama-3.3-70b-versatile`)
- **Data Connectors**: PubMed, ClinicalTrials.gov, MedlinePlus, Crossref
- **Frontend**: Streamlit Enterprise Anti-Gravity Framework

## Dual-Platform Deployment

- **Streamlit Community Cloud**: Ready via `.streamlit/config.toml` and `.streamlit/secrets.toml`
- **Hugging Face Spaces**: Ready via standard `sdk: streamlit` and `app_file: frontend/app.py`

## Local Development

```bash
# 1. Install dependencies
pip install -e .

# 2. Run test suite
python -m pytest tests/ -v

# 3. Launch Streamlit UI
streamlit run frontend/app.py
```

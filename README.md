# 🌿 MedicoBuddy — GraphRAG AI Medical Wellness Assistant

**Production-grade, safety-first, evidence-grounded GraphRAG wellness assistant** built with **LangGraph**, **LangChain**, **Groq**, **Neo4j**, **Milvus**, **PostgreSQL pgvector**, **FastAPI**, and **Streamlit**.

Provides general educational information, low-risk self-care guidance, and Ayurveda-informed lifestyle suggestions for mild, short-duration symptoms in adults (18–65).

> ⚠️ **MedicoBuddy NEVER diagnoses diseases, claims symptoms are non-pathological, replaces doctors, prescribes medicines, recommends surgery, or guarantees recovery.** It requires clinical, legal, privacy, and regulatory review before any public-facing deployment.

---

## 🏛️ Production Tech Stack

| Tier | Technology | Purpose |
| :--- | :--- | :--- |
| **Agentic Workflow** | **LangGraph & LangChain** | Controlled 12-node GraphRAG workflow state machine |
| **LLM Inference** | **Groq API** (`llama-3.3-70b-versatile` / `qwen-2.5-72b`) | Sub-second, ultra-fast clinical response reasoning |
| **Knowledge Graph** | **Neo4j Cypher Graph** | 16 node types & 13 relationship types for medical entities |
| **Primary Vector Store** | **Milvus Standalone** | High-performance vector index (`COSINE` similarity) |
| **Secondary Vector Store** | **PostgreSQL `pgvector`** | ACID-compliant vector persistence & audit logging |
| **Embedding Engine** | **`Qwen/Qwen3-Embedding-8B`** | 4096-dimensional normalized medical text embeddings |
| **Backend Gateway** | **FastAPI (Python 3.11/3.12)** | Async REST endpoints, PII redaction, OpenTelemetry |
| **Frontend UI** | **Streamlit** | WCAG 2.2 AA compliant, interactive dark mode UI |
| **Caching & Limits** | **Redis 7** | Distributed rate limiting & non-sensitive session caching |
| **Containerization** | **Docker & Docker Compose** | 7-service orchestrated local & cloud deployment stack |

---

## ⚡ Quick Start & Deployment

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Groq API Key (`gsk_...`)

### 2. Environment Configuration
Clone the repository and prepare `.env`:
```bash
git clone https://github.com/NikhilRaman12/MedicoBuddy-AI.git
cd MedicoBuddy-AI
cp .env.example .env
```

Edit `.env` to configure your API keys:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL_NAME=llama-3.3-70b-versatile

VECTOR_STORE_PRIMARY=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
ENABLE_PGVECTOR=true

EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDING_DIMENSION=4096
```

### 3. Launch with Docker Compose
Start all 7 microservices:
```bash
docker compose up -d
```

Services exposed:
- **Streamlit Web UI**: `http://localhost:8501`
- **FastAPI Documentation**: `http://localhost:8000/docs`
- **Neo4j Graph Browser**: `http://localhost:7474`
- **Milvus Vector DB**: `http://localhost:19530`

### 4. Seed Knowledge Graph & Run Verification Tests
```bash
# Install local dependencies in editable mode
pip install -e ".[dev]"

# Seed Neo4j graph schemas and Cypher medical data
python scripts/seed_neo4j.py

# Execute full unit, safety, and adversarial test suite (80/80 passing)
python -m pytest tests/ -v
```

---

## 🛡️ Safety-First Architecture & Deterministic Triage Engine

```
User Input
    │
    ▼
┌────────────────────────────────────────┐
│ 1. Scope Validator                     │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 2. Deterministic Red-Flag Triage       │ ──► [Red Flag Detected?] ──► Urgent Care / 112 / 911
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 3. Clarification Node                  │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 4. Query Planner                       │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 5. MCP Data Retrieval                  │ ◄── PubMed, CT.gov, MedlinePlus, Crossref, WHO
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 6. Hybrid Graph + Vector Retrieval     │ ◄── Neo4j Graph Traversal + Milvus/pgvector (RRF)
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 7. Multi-Factor Evidence Grader        │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 8. Contraindication & Safety Critic    │ ◄── Checks Diabetes, Renal, Cardiac, Allergies
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 9. Response Composer (Groq LLM)        │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 10. Deterministic Output Validator     │ ──► Blocks Drugs, Surgery, Ingestible Ayurveda
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 11. Citation & Provenance Validator    │
└───────────────────┬────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────┐
│ 12. Final 10-Section Response          │
└────────────────────────────────────────┘
```

### Key Safety Guarantees
1. **2-Pass Deterministic Triage (No LLM Risk)**: Scans 23 red-flag rules before retrieval and after synthesis. 100% detection rate on emergency cases.
2. **Strict Scope Validation**: Rejects requests for children (<18), elderly (>65), pregnant/breastfeeding, immunocompromised, or severe chronic conditions.
3. **Zero Drug / Dosage / Ingestible Ayurveda**: Hard output blocks against drug names, dosages, surgery terms, and oral Ayurvedic formulations (`bhasma`, `churna`, `vati`).
4. **Prompt Injection Shield**: Filters direct user injection attempts, prompt extraction, and indirect document poisoning.
5. **PII Redaction**: Automatic regex-based PII scrubbing on all structured JSON logs.

---

## 📊 Test Suite Coverage (80/80 Passed)

```
tests/unit/test_red_flags.py          ...... PASSED (23 Red-flag rules)
tests/unit/test_scope_and_output.py   ...... PASSED (Scope & Output validation)
tests/unit/test_evidence_scorer.py   ...... PASSED (Evidence hierarchy & Ayurveda classification)
tests/unit/test_pii_redactor.py      ...... PASSED (PII redaction engine)
tests/adversarial/test_adversarial.py ...... PASSED (Prompt injection & safety bypass)
```

---

## 📄 Licence & Medical Disclaimer

This project is licensed under the Apache-2.0 License.

**Disclaimer:** MedicoBuddy provides general wellness information for educational purposes only. It does not diagnose conditions, prescribe treatments, or replace professional medical advice. Always consult a qualified healthcare provider for medical concerns.

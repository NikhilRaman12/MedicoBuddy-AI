# MedicoBuddy AI — Current State Repository & Runtime Audit

**Date:** July 26, 2026  
**Auditor:** Principal Healthcare AI Architect & Clinical Safety Engineer  
**Status:** Completed Baseline Audit  

---

## 1. Overview & Repository Architecture

`MedicoBuddy-AI` is designed as an evidence-grounded, safety-first healthcare educational assistant for adults aged 18–65. The core tech stack includes:
- **API Framework:** FastAPI (`src/medicobuddy/main.py`)
- **Workflow Orchestration:** LangGraph 12-node state machine (`src/medicobuddy/workflow/`)
- **LLM Engine:** Groq API (`ChatGroq` / `llama-3.3-70b-versatile`)
- **GraphRAG Storage:** Neo4j graph database (`src/medicobuddy/knowledge_graph/`)
- **Vector Search Engine:** Milvus (Primary) & PostgreSQL `pgvector` (Secondary/Failover) (`src/medicobuddy/retrieval/vector_store.py`)
- **Embeddings:** `Qwen/Qwen3-Embedding-8B`
- **Data Services / External APIs:** PubMed, MedlinePlus, ClinicalTrials.gov, Crossref
- **User Interface:** Streamlit Workstation (`frontend/app.py`)

---

## 2. Verification of Known Runtime Defects

| Defect # | Category | Description | File Location | Line References | Status |
|---|---|---|---|---|---|
| **1** | Evidence Ingestion | Source manifest & downloaded documents have no repeatable ingestion path. `scripts/seed_neo4j.py` only runs raw Cypher seeds; no PDF/HTML/XML/JSON chunking or embedding pipeline exists. | `scripts/seed_neo4j.py`<br>`src/medicobuddy/retrieval/` | `scripts/seed_neo4j.py:L1-L45` | **Verified Defect** |
| **2** | Vector Store | `VectorStoreClient` is instantiated in `nodes.py` without invoking `await connect()`. `_milvus_client` remains `None`. Embeddings also return zero-vectors `[0.0]*dim` on fallback and pad/truncate vector dimensions. | `src/medicobuddy/workflow/nodes.py`<br>`src/medicobuddy/retrieval/vector_store.py` | `nodes.py:L262`<br>`vector_store.py:L24-L47, L100, L109` | **Verified Defect** |
| **3** | MCP Architecture | "MCP connectors" are standard `httpx.AsyncClient` REST wrappers, not real Model Context Protocol (MCP) servers using the official Python `mcp` SDK. | `src/medicobuddy/mcp/base.py`<br>`src/medicobuddy/mcp/medlineplus.py` | `base.py:L20-L120`<br>`medlineplus.py:L16-L70` | **Verified Defect** |
| **4** | Parsing Bug | MedlinePlus connector calls `.json()` on NLM search endpoint `wsearch.nlm.nih.gov/ws/query`, which returns raw XML, leading to parsing errors or empty results. | `src/medicobuddy/mcp/medlineplus.py` | `medlineplus.py:L39` | **Verified Defect** |
| **5** | Search Scope | Query planner extracts only up to 2 words (`clean_keyword`), defaults to `"headache"` when empty, and node limits execution to `search_queries[:1]` and `max_results=2`. | `src/medicobuddy/workflow/nodes.py` | `nodes.py:L161, L192, L203` | **Verified Defect** |
| **6** | Evidence Loss | Synchronous `asyncio.wait_for(..., timeout=3.0)` timeouts silences API latency and returns empty evidence lists `[]`. | `src/medicobuddy/workflow/nodes.py` | `nodes.py:L192, L265, L269` | **Verified Defect** |
| **7** | Graph RAG | Knowledge Graph queries receive full raw user sentences (e.g. `"I have had a mild headache since this morning"`) into Cypher `CONTAINS` queries instead of normalized entity tokens. | `src/medicobuddy/workflow/nodes.py`<br>`src/medicobuddy/knowledge_graph/queries.py` | `nodes.py:L258`<br>`queries.py:L22, L40, L87` | **Verified Defect** |
| **8** | Evidence Grading | `evidence_grader_node` calculates composite quality scores for MCP results but never instantiates or returns grounded `EvidenceClaim` items (`graded_evidence` remains empty). | `src/medicobuddy/workflow/nodes.py` | `nodes.py:L330-L352` | **Verified Defect** |
| **9** | Response Composer | `response_composer_node` contains hardcoded headache comfort steps, headache neck massage ayurveda items, and headache fallbacks for unrelated symptoms. | `src/medicobuddy/workflow/nodes.py` | `nodes.py:L409-L454` | **Verified Defect** |
| **10** | Citation Safety | `citation_validator_node` fabricates a generic World Health Organization citation when retrieval yields no results. | `src/medicobuddy/workflow/nodes.py` | `nodes.py:L551-L560` | **Verified Defect** |
| **11** | Evidence Labeling | When no evidence is retrieved, `final_response_node` defaults `overall_evidence_level` to `MODERATE` instead of `INSUFFICIENT`. | `src/medicobuddy/workflow/nodes.py` | `nodes.py:L607` | **Verified Defect** |
| **12** | Health & UI Probe | `/health/ready` returns static `ready: True` without checking Groq, Neo4j, Milvus, or MCP state. Streamlit UI displays `"🟢 Evidence service ready"` unconditionally. | `src/medicobuddy/api/routes/health.py`<br>`frontend/app.py` | `health.py:L21-L30`<br>`app.py:L80, L200` | **Verified Defect** |
| **13** | Deployment & Packaging | `requirements.txt`, `pyproject.toml`, `Dockerfile` (installs `.` before copying `src/`), and `README.md` HF Space metadata (`sdk: streamlit` vs required `sdk: docker` on port 7860) are mismatched. | `Dockerfile`<br>`requirements.txt`<br>`pyproject.toml`<br>`README.md` | `Dockerfile:L17-L24`<br>`requirements.txt:L1-L9`<br>`README.md:L6-L7` | **Verified Defect** |

---

## 3. Test Suite Baseline Audit

- **Existing Unit & Adversarial Tests:** 80 passing tests in `tests/unit` and `tests/adversarial`.
- **Gaps in Current Testing:**
  - No tests for real source document parsing (PDF, HTML, XML, JSON).
  - No tests verifying Qwen embedding vector dimension enforcement and zero-vector rejection.
  - No tests verifying real MCP SDK protocol handshake and tool execution.
  - No test verifying Milvus to pgvector failover under connection drops.
  - No test verifying claim-to-passage entailment and removal of unsupported sentences.
  - No Docker container smoke test verifying port 7860 binding and dual FastAPI + Streamlit startup.

---

## 4. Remediation Plan Overview

All 13 verified defects will be systematically repaired in accordance with the 15 specification modules detailed in the MedicoBuddy AI Implementation Plan.

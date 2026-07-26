# MedicoBuddy AI — System Architecture & Design Specification

## Overview

MedicoBuddy AI is engineered as an evidence-grounded GraphRAG healthcare educational assistant for adults aged 18–65.

```
                    ┌─────────────────────────┐
                    │   Streamlit Frontend    │ (Port 7860)
                    └────────────┬────────────┘
                                 │ HTTP POST /chat
                    ┌────────────▼────────────┐
                    │   FastAPI Middleware    │ (Port 8000)
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           │     LangGraph 13-Node State Machine       │
           └─┬───────────────┬───────────────────┬─────┘
             │               │                   │
    ┌────────▼────────┐ ┌────▼─────────────┐ ┌───▼───────────┐
    │  Neo4j Graph    │ │  Milvus Primary  │ │    Official   │
    │ (Evidence Nodes)│ │ pgvector Failover│ │  MCP Server   │
    └─────────────────┘ └──────────────────┘ └───────────────┘
```

## Core Components

1. **State Machine (`src/medicobuddy/workflow/`):**
   13 async LangGraph nodes orchestrating consent, red-flag triage, query planning, parallel MCP search, hybrid vector/graph retrieval, evidence grading, safety review, Groq structured output generation, output validation, and citation entailment verification.

2. **GraphRAG Engine (`src/medicobuddy/knowledge_graph/`):**
   Neo4j instance modeling `Source`, `Document`, `Passage`, `Claim`, `Symptom`, `SelfCareAction`, `TraditionalPractice`, and `Contraindication`. Ensures every claim links to a grounded passage.

3. **Vector Routing (`src/medicobuddy/retrieval/`):**
   `VectorStoreRouter` managing Milvus standalone primary and PostgreSQL `pgvector` secondary. Embeddings generated via `Qwen/Qwen3-Embedding-8B` through `EmbeddingProvider`.

4. **MCP Protocol Server & Client (`src/medicobuddy/mcp/`):**
   Official Python `mcp` SDK server exposing 9 typed tools (`search_pubmed`, `search_medlineplus`, `search_clinical_trials`, etc.) with strict schemas and XML parsing.

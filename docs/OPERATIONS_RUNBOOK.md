# MedicoBuddy AI — Operations Runbook

## Health Probe Diagnostics

- **Liveness:** `GET /health/live` returns HTTP 200 `{"status": "ok"}` when the process is running.
- **Readiness:** `GET /health/ready` returns `{"ready": true}` when dependencies pass. If `ready: false`, inspect `dependencies` block in the JSON response:
  - `groq_api_configured`: check `GROQ_API_KEY`
  - `neo4j_graph_db`: check `NEO4J_URI` and network connectivity
  - `vector_store_backend`: check Milvus or PostgreSQL status
  - `mcp_handshake_passed`: check MCP connector status

## Maintenance Tasks

- **Ingest New Evidence:** Run `python scripts/ingest_sources.py`
- **Incremental Refresh:** Run `python scripts/refresh_sources.py`

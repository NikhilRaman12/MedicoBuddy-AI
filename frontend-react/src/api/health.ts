import { fetchWithTimeout } from "./client";

export interface LiveHealthResponse {
  status: string;
  live: boolean;
  app: string;
  version: string;
}

export interface ReadyHealthResponse {
  status: string;
  ready: boolean;
  active_profile: string;
  groq_api_key_configured: boolean;
  vector_db: string;
  embedding_model: string;
  neo4j: string;
  indexed_passages_count: number;
}

export interface DependencyHealthResponse {
  groq_llm: { status: string; model: string; key_prefix: string };
  vector_store: { status: string; backend: string; indexed_chunks: number };
  neo4j: { status: string; graph_nodes: number; graph_relationships: number };
  embedding_model: { status: string; model: string; dimension: number };
  mcp: { status: string };
  langgraph_workflow: { status: string };
  overall: string;
}

export async function getHealthLive(): Promise<LiveHealthResponse> {
  try {
    const res = await fetchWithTimeout("/health/live", { timeoutMs: 5000 });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return { status: "unreachable", live: false, app: "MedicoBuddy AI", version: "2.0.0" };
  }
}

export async function getHealthReady(): Promise<ReadyHealthResponse> {
  try {
    const res = await fetchWithTimeout("/health/ready", { timeoutMs: 5000 });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      status: "unreachable",
      ready: false,
      active_profile: "LOCAL",
      groq_api_key_configured: false,
      vector_db: "offline",
      embedding_model: "unknown",
      neo4j: "offline",
      indexed_passages_count: 0,
    };
  }
}

export async function getHealthDependencies(): Promise<DependencyHealthResponse> {
  try {
    const res = await fetchWithTimeout("/health/dependencies", { timeoutMs: 5000 });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      groq_llm: { status: "unreachable", model: "", key_prefix: "" },
      vector_store: { status: "unreachable", backend: "offline", indexed_chunks: 0 },
      neo4j: { status: "unreachable", graph_nodes: 0, graph_relationships: 0 },
      embedding_model: { status: "unreachable", model: "", dimension: 0 },
      mcp: { status: "disabled" },
      langgraph_workflow: { status: "unreachable" },
      overall: "unreachable",
    };
  }
}

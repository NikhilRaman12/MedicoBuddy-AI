import { ChatPayload } from "./chat";
import { MedicoBuddyResponse } from "./schemas";

export type StreamStage =
  | "checking_safety"
  | "understanding_question"
  | "searching_evidence"
  | "validating_sources"
  | "preparing_guidance"
  | "completed"
  | "error";

export interface StreamCallbacks {
  onStageChange?: (stage: StreamStage, message?: string) => void;
  onToken?: (token: string) => void;
  onComplete?: (response: MedicoBuddyResponse) => void;
  onError?: (error: Error) => void;
}

export async function streamChatMessage(
  payload: ChatPayload,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const BASE_URL = import.meta.env.VITE_API_BASE || "";

  try {
    callbacks.onStageChange?.("checking_safety", "Checking safety guidelines...");

    const response = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Streaming failed with status ${response.status}`);
    }

    if (!response.body) {
      throw new Error("Stream response body is null");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const eventData = JSON.parse(line.slice(6));

            if (eventData.event === "request.accepted") {
              callbacks.onStageChange?.("understanding_question", "Understanding your question...");
            } else if (eventData.event === "triage.completed") {
              callbacks.onStageChange?.("searching_evidence", "Searching evidence sources...");
            } else if (eventData.event === "retrieval.completed") {
              callbacks.onStageChange?.("validating_sources", "Validating source claims...");
            } else if (eventData.event === "generation.started") {
              callbacks.onStageChange?.("preparing_guidance", "Preparing structured response...");
            } else if (eventData.event === "token" && eventData.text) {
              callbacks.onToken?.(eventData.text);
            } else if (eventData.event === "response.completed" && eventData.data) {
              callbacks.onStageChange?.("completed", "Response completed");
              callbacks.onComplete?.(eventData.data);
            }
          } catch (e) {
            // Ignore malformed SSE line
          }
        }
      }
    }
  } catch (err: any) {
    if (err.name === "AbortError") {
      callbacks.onStageChange?.("completed", "Stream cancelled by user");
      return;
    }
    callbacks.onStageChange?.("error", err.message);
    callbacks.onError?.(err);
  }
}

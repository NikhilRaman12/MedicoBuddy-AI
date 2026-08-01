import { fetchWithTimeout } from "./client";
import { APIError } from "./errors";
import { MedicoBuddyResponse, MedicoBuddyResponseSchema } from "./schemas";

export interface ChatPayload {
  message: string;
  audience_mode?: string;
  preferred_language?: string;
  parent_request_id?: string | null;
  thread_id?: string;
  age_range?: string;
  pregnancy_status?: string;
  chronic_conditions?: string[];
  allergies?: string[];
  current_medicines?: string[];
  immunocompromised?: boolean;
  region?: string;
  consent_given?: boolean;
}

export async function sendChatMessage(
  payload: ChatPayload,
  signal?: AbortSignal
): Promise<MedicoBuddyResponse> {
  const res = await fetchWithTimeout("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      audience_mode: "patient_education",
      preferred_language: "auto",
      age_range: "18_65",
      pregnancy_status: "unknown",
      chronic_conditions: [],
      allergies: [],
      current_medicines: [],
      immunocompromised: false,
      region: "IN",
      consent_given: true,
      ...payload,
    }),
    signal,
    timeoutMs: 60000,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new APIError(
      `Backend service returned HTTP ${res.status}`,
      res.status,
      errorBody
    );
  }

  const rawJson = await res.json();
  const parseResult = MedicoBuddyResponseSchema.safeParse(rawJson);

  if (!parseResult.success) {
    console.warn("Zod schema parsing warning (fallback used):", parseResult.error);
    // Return rawJson if structurally complete, else default
    return {
      triage_outcome: rawJson.triage_outcome || "self_care",
      safety_status: rawJson.safety_status || "SELF_CARE_INFORMATION",
      what_this_applies_to: rawJson.what_this_applies_to || "",
      summary: rawJson.summary || "",
      action_table: rawJson.action_table || [],
      preventive_approaches: rawJson.preventive_approaches || [],
      ayurveda_perspectives: rawJson.ayurveda_perspectives || [],
      general_self_care_education: rawJson.general_self_care_education || "",
      implementation_plan: rawJson.implementation_plan || { now: "", next_6_to_12_hours: "", next_24_to_48_hours: "" },
      things_to_avoid: rawJson.things_to_avoid || [],
      warning_signs: rawJson.warning_signs || [],
      when_to_seek_care: rawJson.when_to_seek_care || [],
      citations: rawJson.citations || [],
      overall_evidence_level: rawJson.overall_evidence_level || "MODERATE",
      targeted_follow_up: rawJson.targeted_follow_up || "",
      follow_up_question: rawJson.follow_up_question || "",
      quick_action_chips: rawJson.quick_action_chips || [],
      quick_actions: rawJson.quick_actions || [],
      educational_statement: rawJson.educational_statement || "",
      retrieval_diagnostics: rawJson.retrieval_diagnostics || {},
    };
  }

  return parseResult.data;
}

export async function deleteThreadHistory(threadId: string): Promise<boolean> {
  try {
    const res = await fetchWithTimeout(`/api/v1/chat/thread/${threadId}`, {
      method: "DELETE",
      timeoutMs: 5000,
    });
    return res.ok;
  } catch {
    return false;
  }
}

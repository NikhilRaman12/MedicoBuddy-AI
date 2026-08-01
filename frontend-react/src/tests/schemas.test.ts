import { describe, it, expect } from "vitest";
import { MedicoBuddyResponseSchema } from "../api/schemas";

describe("MedicoBuddyResponseSchema", () => {
  it("validates full structured response contract", () => {
    const rawData = {
      triage_outcome: "self_care",
      safety_status: "SELF_CARE_INFORMATION",
      what_this_applies_to: "Mild headache in adults 18-65",
      summary: "Tension headache can be managed with hydration and rest.",
      action_table: [
        {
          guidance_lens: "Natural Self-Care",
          what_may_help: "Cold compress",
          how_to_follow: "Apply for 10-15 minutes",
          frequency_duration: "Every 30 min",
          evidence_strength: "Moderate",
          cautions: "Check temperature",
          stop_and_seek_care_if: "Pain >7/10",
        },
      ],
      warning_signs: ["Sudden severe headache"],
      citations: [],
    };

    const parsed = MedicoBuddyResponseSchema.parse(rawData);
    expect(parsed.summary).toContain("Tension headache");
    expect(parsed.action_table).toHaveLength(1);
    expect(parsed.action_table[0].guidance_lens).toBe("Natural Self-Care");
  });

  it("handles missing optional fields with safe defaults", () => {
    const minimalData = {
      summary: "Minimal summary",
    };

    const parsed = MedicoBuddyResponseSchema.parse(minimalData);
    expect(parsed.summary).toBe("Minimal summary");
    expect(parsed.action_table).toEqual([]);
    expect(parsed.warning_signs).toEqual([]);
    expect(parsed.citations).toEqual([]);
  });
});

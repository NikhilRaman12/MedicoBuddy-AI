import { z } from "zod";

export const ActionTableRowSchema = z.object({
  guidance_lens: z.string().default(""),
  what_may_help: z.string().default(""),
  how_to_follow: z.string().default(""),
  frequency_duration: z.string().default(""),
  evidence_strength: z.string().default(""),
  cautions: z.string().default(""),
  stop_and_seek_care_if: z.string().default(""),
  citation_ids: z.array(z.string()).default([]),
});

export const ImplementationPlanSchema = z.object({
  now: z.string().default(""),
  next_6_to_12_hours: z.string().default(""),
  next_24_to_48_hours: z.string().default(""),
  what_to_monitor: z.string().optional().default(""),
  when_to_stop_self_care: z.string().optional().default(""),
});

export const CitationSchema = z.object({
  number: z.number().default(1),
  citation_id: z.string().default(""),
  title: z.string().default("Evidence Document"),
  authors: z.string().default(""),
  publication_date: z.string().default(""),
  source_file: z.string().default(""),
  page_number: z.number().nullable().optional().default(1),
  supporting_passage: z.string().default(""),
  retrieval_score: z.number().optional().default(0),
  evidence_type: z.string().optional().default(""),
});

export const QuickActionSchema = z.object({
  action_id: z.string().optional().default(""),
  label: z.string().default(""),
  standalone_query: z.string().default(""),
  intent: z.string().optional().default("general_followup"),
  parent_topic: z.string().default(""),
});

export const MedicoBuddyResponseSchema = z.object({
  triage_outcome: z.string().default("self_care"),
  safety_status: z.string().default("SELF_CARE_INFORMATION"),
  what_this_applies_to: z.string().default(""),
  summary: z.string().default(""),
  action_table: z.array(ActionTableRowSchema).default([]),
  preventive_approaches: z.array(z.string()).default([]),
  ayurveda_perspectives: z.array(z.any()).default([]),
  general_self_care_education: z.string().default(""),
  implementation_plan: ImplementationPlanSchema.default({ now: "", next_6_to_12_hours: "", next_24_to_48_hours: "" }),
  things_to_avoid: z.array(z.string()).default([]),
  warning_signs: z.array(z.string()).default([]),
  when_to_seek_care: z.array(z.string()).default([]),
  citations: z.array(CitationSchema).default([]),
  overall_evidence_level: z.string().default("MODERATE"),
  targeted_follow_up: z.string().default(""),
  follow_up_question: z.string().default(""),
  quick_action_chips: z.array(z.string()).default([]),
  quick_actions: z.array(QuickActionSchema).default([]),
  educational_statement: z.string().default(""),
  retrieval_diagnostics: z.record(z.any()).optional().default({}),
});

export type ActionTableRow = z.infer<typeof ActionTableRowSchema>;
export type ImplementationPlan = z.infer<typeof ImplementationPlanSchema>;
export type Citation = z.infer<typeof CitationSchema>;
export type QuickAction = z.infer<typeof QuickActionSchema>;
export type MedicoBuddyResponse = z.infer<typeof MedicoBuddyResponseSchema>;

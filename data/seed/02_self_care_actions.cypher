// ─────────────────────────────────────────────────────────
// MedicoBuddy — Seed Data: Self-Care Actions
// ─────────────────────────────────────────────────────────

// ── Rest & Sleep ────────────────────────────────────────
MERGE (a1:SelfCareAction {action_id: "ACT001"})
SET a1.name = "rest in a quiet, dark room",
    a1.description = "Resting in a quiet, dimly lit room may help ease mild headache discomfort. Reducing sensory stimulation can provide temporary comfort.",
    a1.category = "rest",
    a1.risk_level = "low";

MERGE (a2:SelfCareAction {action_id: "ACT002"})
SET a2.name = "adequate sleep",
    a2.description = "Getting 7–9 hours of sleep supports the body's natural recovery processes. Maintain a consistent sleep schedule.",
    a2.category = "rest",
    a2.risk_level = "low";

// ── Hydration ───────────────────────────────────────────
MERGE (a3:SelfCareAction {action_id: "ACT003"})
SET a3.name = "stay hydrated with water",
    a3.description = "Drinking small, frequent sips of plain water helps maintain hydration, especially during mild fever or nausea.",
    a3.category = "hydration",
    a3.risk_level = "low";

MERGE (a4:SelfCareAction {action_id: "ACT004"})
SET a4.name = "oral rehydration with clear fluids",
    a4.description = "Clear fluids such as water, dilute clear soups, or oral rehydration solutions can help replenish lost fluids.",
    a4.category = "hydration",
    a4.risk_level = "low";

// ── Positioning & Comfort ───────────────────────────────
MERGE (a5:SelfCareAction {action_id: "ACT005"})
SET a5.name = "comfortable positioning",
    a5.description = "Finding a comfortable resting position with head slightly elevated may ease discomfort from headache or nausea.",
    a5.category = "positioning",
    a5.risk_level = "low";

MERGE (a6:SelfCareAction {action_id: "ACT006"})
SET a6.name = "cool or warm compress",
    a6.description = "A cool cloth on the forehead for headache, or a warm cloth on the stomach for mild discomfort, may provide temporary relief.",
    a6.category = "environment",
    a6.risk_level = "low";

// ── Breathing & Relaxation ──────────────────────────────
MERGE (a7:SelfCareAction {action_id: "ACT007"})
SET a7.name = "gentle deep breathing",
    a7.description = "Slow, gentle deep breathing (inhale 4 seconds, hold 4, exhale 6) may help with relaxation and mild nausea.",
    a7.category = "breathing",
    a7.risk_level = "low";

// ── Environment ─────────────────────────────────────────
MERGE (a8:SelfCareAction {action_id: "ACT008"})
SET a8.name = "comfortable room temperature",
    a8.description = "Keeping the room at a comfortable temperature (around 20–22°C) with adequate ventilation supports rest.",
    a8.category = "environment",
    a8.risk_level = "low";

// ── Reduced Exertion ────────────────────────────────────
MERGE (a9:SelfCareAction {action_id: "ACT009"})
SET a9.name = "reduce physical exertion",
    a9.description = "Temporarily reducing strenuous physical activity allows the body to rest and may prevent symptom worsening.",
    a9.category = "rest",
    a9.risk_level = "low";

// ── Dietary ─────────────────────────────────────────────
MERGE (a10:SelfCareAction {action_id: "ACT010"})
SET a10.name = "small bland meals",
    a10.description = "Eating small portions of plain, familiar foods like rice, toast, or bananas may help with mild nausea or stomach discomfort. Avoid spicy, fatty, or heavily seasoned foods temporarily.",
    a10.category = "diet",
    a10.risk_level = "low";

// ── Link actions to symptoms ────────────────────────────
// Headache
MATCH (s:Symptom {symptom_id: "SYM001"})
MERGE (a1)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);
MATCH (s:Symptom {symptom_id: "SYM001"})
MERGE (a2)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);
MATCH (s:Symptom {symptom_id: "SYM001"})
MERGE (a3)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);
MATCH (s:Symptom {symptom_id: "SYM001"})
MERGE (a6)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "limited", confidence: 0.5}]->(s);
MATCH (s:Symptom {symptom_id: "SYM001"})
MERGE (a7)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "limited", confidence: 0.5}]->(s);

// Tiredness
MATCH (s:Symptom {symptom_id: "SYM002"})
MERGE (a2)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "high", confidence: 0.85}]->(s);
MATCH (s:Symptom {symptom_id: "SYM002"})
MERGE (a3)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);
MATCH (s:Symptom {symptom_id: "SYM002"})
MERGE (a9)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);

// Nausea
MATCH (s:Symptom {symptom_id: "SYM003"})
MERGE (a3)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "high", confidence: 0.8}]->(s);
MATCH (s:Symptom {symptom_id: "SYM003"})
MERGE (a5)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.6}]->(s);
MATCH (s:Symptom {symptom_id: "SYM003"})
MERGE (a7)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "limited", confidence: 0.5}]->(s);
MATCH (s:Symptom {symptom_id: "SYM003"})
MERGE (a10)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);

// Stomach discomfort
MATCH (s:Symptom {symptom_id: "SYM004"})
MERGE (a5)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "limited", confidence: 0.5}]->(s);
MATCH (s:Symptom {symptom_id: "SYM004"})
MERGE (a6)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "limited", confidence: 0.5}]->(s);
MATCH (s:Symptom {symptom_id: "SYM004"})
MERGE (a10)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);

// Mild fever
MATCH (s:Symptom {symptom_id: "SYM005"})
MERGE (a2)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "high", confidence: 0.8}]->(s);
MATCH (s:Symptom {symptom_id: "SYM005"})
MERGE (a3)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "high", confidence: 0.85}]->(s);
MATCH (s:Symptom {symptom_id: "SYM005"})
MERGE (a8)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.65}]->(s);

// Digestive discomfort
MATCH (s:Symptom {symptom_id: "SYM006"})
MERGE (a3)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);
MATCH (s:Symptom {symptom_id: "SYM006"})
MERGE (a7)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "limited", confidence: 0.5}]->(s);
MATCH (s:Symptom {symptom_id: "SYM006"})
MERGE (a10)-[:ACTION_MAY_SUPPORT_SYMPTOM {evidence_level: "moderate", confidence: 0.7}]->(s);

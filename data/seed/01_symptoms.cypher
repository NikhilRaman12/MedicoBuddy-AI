// ─────────────────────────────────────────────────────────
// MedicoBuddy — Seed Data: Symptoms & Scope Expansion
// Scope: Mild, short-duration concerns for adults 18-65
// ─────────────────────────────────────────────────────────

// Core symptoms
MERGE (s1:Symptom {symptom_id: "SYM001", name: "mild headache"})
SET s1.description = "Mild, non-specific headache without alarming features", s1.body_location = "head", s1.severity_range = "mild";

MERGE (s2:Symptom {symptom_id: "SYM002", name: "temporary tiredness"})
SET s2.description = "Short-duration fatigue or feeling of tiredness without persistent weakness", s2.body_location = "general", s2.severity_range = "mild";

MERGE (s3:Symptom {symptom_id: "SYM003", name: "mild nausea"})
SET s3.description = "Mild nausea without persistent vomiting or blood", s3.body_location = "abdomen", s3.severity_range = "mild";

MERGE (s4:Symptom {symptom_id: "SYM004", name: "mild stomach discomfort"})
SET s4.description = "Mild, non-localized stomach or abdominal discomfort", s4.body_location = "abdomen", s4.severity_range = "mild";

MERGE (s5:Symptom {symptom_id: "SYM005", name: "short-duration mild fever"})
SET s5.description = "Low-grade fever (below 39°C / 102°F) for less than 48 hours", s5.body_location = "general", s5.severity_range = "mild";

MERGE (s6:Symptom {symptom_id: "SYM006", name: "minor digestive discomfort"})
SET s6.description = "Mild bloating, gas, or indigestion", s6.body_location = "abdomen", s6.severity_range = "mild";

MERGE (s7:Symptom {symptom_id: "SYM007", name: "uncomplicated cold symptoms"})
SET s7.description = "Mild runny nose, sneezing, or scratchy throat without high fever", s7.body_location = "respiratory", s7.severity_range = "mild";

MERGE (s8:Symptom {symptom_id: "SYM008", name: "mild cough"})
SET s8.description = "Dry or mild productive cough without shortness of breath or hemoptysis", s8.body_location = "chest", s8.severity_range = "mild";

MERGE (s9:Symptom {symptom_id: "SYM009", name: "mild sinus congestion"})
SET s9.description = "Mild nasal congestion or facial pressure without severe headache or high fever", s9.body_location = "head", s9.severity_range = "mild";

MERGE (s10:Symptom {symptom_id: "SYM010", name: "non-emergency allergy symptoms"})
SET s10.description = "Mild seasonal allergy symptoms such as watery eyes or itchy nose", s10.body_location = "head", s10.severity_range = "mild";

MERGE (s11:Symptom {symptom_id: "SYM011", name: "sleep hygiene questions"})
SET s11.description = "General sleep hygiene, hydration, or sleep comfort questions", s11.body_location = "general", s11.severity_range = "mild";

MERGE (s12:Symptom {symptom_id: "SYM012", name: "hair skin body care education"})
SET s12.description = "General non-clinical hygiene, moisturization, or body-care education", s12.body_location = "general", s12.severity_range = "mild";

// ─────────────────────────────────────────────────────────
// Red Flags linked to symptoms
// ─────────────────────────────────────────────────────────

MERGE (rf1:RedFlag {flag_id: "RF008", name: "thunderclap headache"})
SET rf1.description = "Sudden worst-ever headache — may indicate subarachnoid haemorrhage", rf1.urgency = "emergency";

MERGE (rf2:RedFlag {flag_id: "RF009", name: "headache following injury"})
SET rf2.description = "Headache after head trauma — may indicate concussion or intracranial bleeding", rf2.urgency = "urgent";

MERGE (rf3:RedFlag {flag_id: "RF010", name: "stiff neck with headache"})
SET rf3.description = "Stiff neck combined with headache — may indicate meningitis", rf3.urgency = "emergency";

MERGE (rf4:RedFlag {flag_id: "RF016", name: "high fever"})
SET rf4.description = "Fever above 39.5°C / 103°F or rising rapidly", rf4.urgency = "urgent";

MERGE (rf5:RedFlag {flag_id: "RF014", name: "blood in vomit or stool"})
SET rf5.description = "Blood in vomit (hematemesis) or stool (melena, hematochezia)", rf5.urgency = "emergency";

MERGE (rf6:RedFlag {flag_id: "RF015", name: "persistent vomiting with dehydration"})
SET rf6.description = "Inability to retain fluids with signs of severe dehydration", rf6.urgency = "urgent";

MERGE (rf7:RedFlag {flag_id: "RF020", name: "shortness of breath or chest pain"})
SET rf7.description = "Difficulty breathing or persistent chest pressure", rf7.urgency = "emergency";

// Link red flags to symptoms
MERGE (s1)-[:HAS_RED_FLAG]->(rf1);
MERGE (s1)-[:HAS_RED_FLAG]->(rf2);
MERGE (s1)-[:HAS_RED_FLAG]->(rf3);
MERGE (s5)-[:HAS_RED_FLAG]->(rf4);
MERGE (s3)-[:HAS_RED_FLAG]->(rf5);
MERGE (s3)-[:HAS_RED_FLAG]->(rf6);
MERGE (s8)-[:HAS_RED_FLAG]->(rf7);

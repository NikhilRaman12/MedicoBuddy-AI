// ─────────────────────────────────────────────────────────
// MedicoBuddy — Seed Data: Symptoms
// ─────────────────────────────────────────────────────────

// Core mild symptoms within scope
MERGE (s1:Symptom {symptom_id: "SYM001"})
SET s1.name = "mild headache",
    s1.description = "Mild, non-specific headache without alarming features",
    s1.body_location = "head",
    s1.severity_range = "mild";

MERGE (s2:Symptom {symptom_id: "SYM002"})
SET s2.name = "temporary tiredness",
    s2.description = "Short-duration fatigue or feeling of tiredness without persistent weakness",
    s2.body_location = "general",
    s2.severity_range = "mild";

MERGE (s3:Symptom {symptom_id: "SYM003"})
SET s3.name = "mild nausea",
    s3.description = "Mild nausea without persistent vomiting or blood",
    s3.body_location = "general",
    s3.severity_range = "mild";

MERGE (s4:Symptom {symptom_id: "SYM004"})
SET s4.name = "mild stomach discomfort",
    s4.description = "Mild, non-localized stomach or abdominal discomfort",
    s4.body_location = "abdomen",
    s4.severity_range = "mild";

MERGE (s5:Symptom {symptom_id: "SYM005"})
SET s5.name = "short-duration mild fever",
    s5.description = "Low-grade fever (below 39°C / 102°F) for less than 48 hours",
    s5.body_location = "general",
    s5.severity_range = "mild";

MERGE (s6:Symptom {symptom_id: "SYM006"})
SET s6.name = "minor digestive discomfort",
    s6.description = "Mild bloating, gas, or indigestion",
    s6.body_location = "abdomen",
    s6.severity_range = "mild";

// ─────────────────────────────────────────────────────────
// Red Flags linked to symptoms
// ─────────────────────────────────────────────────────────

MERGE (rf1:RedFlag {flag_id: "RF008"})
SET rf1.name = "thunderclap headache",
    rf1.description = "Sudden worst-ever headache — may indicate subarachnoid haemorrhage",
    rf1.urgency = "emergency";

MERGE (rf2:RedFlag {flag_id: "RF009"})
SET rf2.name = "headache following injury",
    rf2.description = "Headache after head trauma — may indicate concussion or intracranial bleeding",
    rf2.urgency = "urgent";

MERGE (rf3:RedFlag {flag_id: "RF010"})
SET rf3.name = "stiff neck with headache",
    rf3.description = "Stiff neck combined with headache — may indicate meningitis",
    rf3.urgency = "emergency";

MERGE (rf4:RedFlag {flag_id: "RF016"})
SET rf4.name = "high fever",
    rf4.description = "Fever above 39.5°C / 103°F or rising rapidly",
    rf4.urgency = "urgent";

MERGE (rf5:RedFlag {flag_id: "RF014"})
SET rf5.name = "blood in vomit or stool",
    rf5.description = "Blood in vomit (hematemesis) or stool (melena, hematochezia)",
    rf5.urgency = "emergency";

MERGE (rf6:RedFlag {flag_id: "RF015"})
SET rf6.name = "persistent vomiting with dehydration",
    rf6.description = "Inability to retain fluids with signs of severe dehydration",
    rf6.urgency = "urgent";

// Link red flags to symptoms
MERGE (s1)-[:SYMPTOM_HAS_RED_FLAG]->(rf1);
MERGE (s1)-[:SYMPTOM_HAS_RED_FLAG]->(rf2);
MERGE (s1)-[:SYMPTOM_HAS_RED_FLAG]->(rf3);
MERGE (s5)-[:SYMPTOM_HAS_RED_FLAG]->(rf4);
MERGE (s3)-[:SYMPTOM_HAS_RED_FLAG]->(rf5);
MERGE (s3)-[:SYMPTOM_HAS_RED_FLAG]->(rf6);

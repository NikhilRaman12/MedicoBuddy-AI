// ─────────────────────────────────────────────────────────
// MedicoBuddy — Seed Data: Evidence Graph Nodes & Claims
// Schema: Source, Organization, Document, Passage, Claim
// ─────────────────────────────────────────────────────────

// Organizations
MERGE (org1:Organization {org_id: "ORG001", name: "World Health Organization"})
SET org1.type = "international_body";

MERGE (org2:Organization {org_id: "ORG002", name: "National Library of Medicine"})
SET org2.type = "government";

MERGE (org3:Organization {org_id: "ORG003", name: "Ministry of AYUSH India"})
SET org3.type = "government";

// Sources
MERGE (src1:Source {source_id: "SRC001", name: "MedlinePlus Consumer Health Education"})
SET src1.url = "https://medlineplus.gov", src1.licence = "Public Domain", src1.tier = 1;
MERGE (src1)-[:PUBLISHED_BY]->(org2);

MERGE (src2:Source {source_id: "SRC002", name: "WHO Self-Care Guidelines"})
SET src2.url = "https://www.who.int/publications/i/item/9789240052192", src2.licence = "CC-BY-NC-SA-3.0", src2.tier = 1;
MERGE (src2)-[:PUBLISHED_BY]->(org1);

MERGE (src3:Source {source_id: "SRC003", name: "AYUSH Preventive Lifestyle Practices"})
SET src3.url = "https://ayush.gov.in/guidelines", src3.licence = "Open Access", src3.tier = 2;
MERGE (src3)-[:PUBLISHED_BY]->(org3);

// Documents & Passages
MERGE (doc1:Document {doc_id: "DOC_001", title: "Non-Pharmacological Headaches & Cold Care"})
SET doc1.publication_date = "2026-01-15";
MERGE (src1)-[:HAS_DOCUMENT]->(doc1);

MERGE (pas1:Passage {passage_id: "PAS001"})
SET pas1.text = "Resting in a quiet, dark room and sipping adequate fluids provides non-pharmacological comfort for mild tension headaches.",
    pas1.section_title = "Self-Care for Mild Headache",
    pas1.page_number = 1;
MERGE (doc1)-[:HAS_PASSAGE]->(pas1);

MERGE (pas2:Passage {passage_id: "PAS002"})
SET pas2.text = "Steam inhalation and warm fluid hydration help ease mild nasal congestion and cold discomfort.",
    pas2.section_title = "Cold & Sinus Care",
    pas2.page_number = 2;
MERGE (doc1)-[:HAS_PASSAGE]->(pas2);

// Claims
MERGE (cl1:Claim {claim_id: "CLM001"})
SET cl1.text = "Quiet rest and hydration ease mild tension headache symptoms.",
    cl1.evidence_grade = "high",
    cl1.confidence = 0.85;
MERGE (pas1)-[:MAKES_CLAIM]->(cl1);

MERGE (cl2:Claim {claim_id: "CLM002"})
SET cl2.text = "Warm fluids and humidification support upper respiratory comfort in mild colds.",
    cl2.evidence_grade = "moderate",
    cl2.confidence = 0.75;
MERGE (pas2)-[:MAKES_CLAIM]->(cl2);

// Link claims to symptoms and self-care actions
MATCH (s:Symptom {symptom_id: "SYM001"})
MATCH (a:SelfCareAction {action_id: "ACT001"})
MERGE (cl1)-[:SUPPORTED_BY]->(pas1);
MERGE (a)-[:MAY_HELP_WITH]->(s);
MERGE (cl1)-[:APPLIES_TO]->(s);

MATCH (s2:Symptom {symptom_id: "SYM007"})
MATCH (a2:SelfCareAction {action_id: "ACT003"})
MERGE (cl2)-[:SUPPORTED_BY]->(pas2);
MERGE (a2)-[:MAY_HELP_WITH]->(s2);
MERGE (cl2)-[:APPLIES_TO]->(s2);

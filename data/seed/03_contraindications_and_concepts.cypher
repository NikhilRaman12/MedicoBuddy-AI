// ─────────────────────────────────────────────────────────
// MedicoBuddy — Seed Data: Contraindications & Populations
// ─────────────────────────────────────────────────────────

// ── Population Groups ───────────────────────────────────
MERGE (pg1:PopulationGroup {group_id: "PG001"})
SET pg1.name = "adults 18-65", pg1.age_range = "18-65", pg1.in_scope = true;

MERGE (pg2:PopulationGroup {group_id: "PG002"})
SET pg2.name = "children under 18", pg2.age_range = "0-17", pg2.in_scope = false;

MERGE (pg3:PopulationGroup {group_id: "PG003"})
SET pg3.name = "older adults over 65", pg3.age_range = "66+", pg3.in_scope = false;

MERGE (pg4:PopulationGroup {group_id: "PG004"})
SET pg4.name = "pregnant individuals", pg4.age_range = "any", pg4.in_scope = false;

MERGE (pg5:PopulationGroup {group_id: "PG005"})
SET pg5.name = "immunocompromised individuals", pg5.age_range = "any", pg5.in_scope = false;

// ── Conditions ──────────────────────────────────────────
MERGE (c1:Condition {condition_id: "CON001"})
SET c1.name = "diabetes", c1.relevance = "Sugar intake restrictions; dehydration risk; slower healing";

MERGE (c2:Condition {condition_id: "CON002"})
SET c2.name = "kidney disease", c2.relevance = "Fluid and electrolyte restrictions; potassium limits";

MERGE (c3:Condition {condition_id: "CON003"})
SET c3.name = "heart disease", c3.relevance = "Fluid restrictions; sodium limits; exertion limits";

MERGE (c4:Condition {condition_id: "CON004"})
SET c4.name = "hypertension", c4.relevance = "Sodium restrictions; certain foods may affect blood pressure";

// ── Contraindications ───────────────────────────────────
MERGE (ci1:Contraindication {contra_id: "CI001"})
SET ci1.description = "Excess fluid intake may be harmful for individuals with heart failure or kidney disease on fluid restriction",
    ci1.applies_to = "heart disease, kidney disease";

MERGE (ci2:Contraindication {contra_id: "CI002"})
SET ci2.description = "Sugary or high-glycemic foods/drinks should be avoided for individuals with diabetes",
    ci2.applies_to = "diabetes";

MERGE (ci3:Contraindication {contra_id: "CI003"})
SET ci3.description = "High-sodium foods and broths should be limited for individuals with hypertension or heart disease",
    ci3.applies_to = "hypertension, heart disease";

MERGE (ci4:Contraindication {contra_id: "CI004"})
SET ci4.description = "Potassium-rich foods (bananas, coconut water) may be restricted for those with kidney disease",
    ci4.applies_to = "kidney disease";

// Link conditions to contraindications
MERGE (c1)-[:CONDITION_CONTRAINDICATES]->(ci2);
MERGE (c2)-[:CONDITION_CONTRAINDICATES]->(ci1);
MERGE (c2)-[:CONDITION_CONTRAINDICATES]->(ci4);
MERGE (c3)-[:CONDITION_CONTRAINDICATES]->(ci1);
MERGE (c3)-[:CONDITION_CONTRAINDICATES]->(ci3);
MERGE (c4)-[:CONDITION_CONTRAINDICATES]->(ci3);

// Link hydration action to contraindication
MATCH (a:SelfCareAction {action_id: "ACT003"})
MERGE (a)-[:ACTION_CONTRAINDICATED_FOR]->(ci1);
MATCH (a:SelfCareAction {action_id: "ACT004"})
MERGE (a)-[:ACTION_CONTRAINDICATED_FOR]->(ci1);
MATCH (a:SelfCareAction {action_id: "ACT010"})
MERGE (a)-[:ACTION_CONTRAINDICATED_FOR]->(ci2);
MATCH (a:SelfCareAction {action_id: "ACT010"})
MERGE (a)-[:ACTION_CONTRAINDICATED_FOR]->(ci4);

// ─────────────────────────────────────────────────────────
// Ayurvedic Concepts (non-pharmacological only)
// ─────────────────────────────────────────────────────────
MERGE (ay1:AyurvedicConcept {concept_id: "AY001"})
SET ay1.name = "warm water sipping",
    ay1.description = "Sipping warm water throughout the day is a traditional Ayurvedic recommendation for supporting digestion and hydration. Some limited studies suggest warm water may aid gastric motility.",
    ay1.evidence_category = "limited_or_preliminary_evidence",
    ay1.source_tradition = "Classical Ayurvedic texts (Charaka Samhita)";

MERGE (ay2:AyurvedicConcept {concept_id: "AY002"})
SET ay2.name = "regular sleep-wake routine (dinacharya)",
    ay2.description = "Maintaining a consistent daily routine including regular sleep and wake times is emphasized in Ayurvedic dinacharya. Modern sleep hygiene research supports consistent sleep schedules.",
    ay2.evidence_category = "evidence_supported",
    ay2.source_tradition = "Ashtanga Hridaya; aligned with modern sleep hygiene guidelines";

MERGE (ay3:AyurvedicConcept {concept_id: "AY003"})
SET ay3.name = "gentle nasal breathing (pranayama basics)",
    ay3.description = "Simple, gentle deep breathing through the nose without forceful techniques. Basic breathing exercises have some evidence for relaxation and stress reduction.",
    ay3.evidence_category = "limited_or_preliminary_evidence",
    ay3.source_tradition = "Pranayama tradition; supported by limited clinical studies";

MERGE (ay4:AyurvedicConcept {concept_id: "AY004"})
SET ay4.name = "light, easily digestible meals",
    ay4.description = "Ayurvedic tradition recommends simple, warm, easily digestible foods during illness. This aligns with general dietary advice during mild gastrointestinal symptoms.",
    ay4.evidence_category = "evidence_supported",
    ay4.source_tradition = "Charaka Samhita; consistent with modern GI management guidance";

// Link Ayurvedic concepts to lifestyle practices
MERGE (lp1:LifestylePractice {practice_id: "LP001"})
SET lp1.name = "warm water intake", lp1.category = "hydration";
MERGE (ay1)-[:CONCEPT_LINKED_TO_PRACTICE]->(lp1);

MERGE (lp2:LifestylePractice {practice_id: "LP002"})
SET lp2.name = "consistent sleep schedule", lp2.category = "sleep";
MERGE (ay2)-[:CONCEPT_LINKED_TO_PRACTICE]->(lp2);

MERGE (lp3:LifestylePractice {practice_id: "LP003"})
SET lp3.name = "gentle breathing exercises", lp3.category = "breathing";
MERGE (ay3)-[:CONCEPT_LINKED_TO_PRACTICE]->(lp3);

MERGE (lp4:LifestylePractice {practice_id: "LP004"})
SET lp4.name = "bland diet during illness", lp4.category = "diet";
MERGE (ay4)-[:CONCEPT_LINKED_TO_PRACTICE]->(lp4);

// ── Organizations & Sources ─────────────────────────────
MERGE (org1:Organization {org_id: "ORG001"})
SET org1.name = "World Health Organization", org1.type = "international_body";

MERGE (org2:Organization {org_id: "ORG002"})
SET org2.name = "Ministry of AYUSH, Government of India", org2.type = "government";

MERGE (org3:Organization {org_id: "ORG003"})
SET org3.name = "National Library of Medicine (NLM)", org3.type = "government";

MERGE (org4:Organization {org_id: "ORG004"})
SET org4.name = "Cochrane Collaboration", org4.type = "research_institution";

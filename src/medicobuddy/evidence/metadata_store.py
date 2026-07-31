"""Medicobuddy Metadata Store (medicobuddy_metadata).

Comprehensive built-in medical metadata repository covering:
- Natural remedies
- Ayurvedic remedies & lifestyle practices
- General / Allopathic OTC self-care guidance
- Immune-boosting & preventive suggestions
- Important cautions & stop-and-seek-care triggers

Covers everyday health concerns for adults aged 18–65.
Excludes surgery, chronic internal disease management, heart failure, and major organ pathology.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Comprehensive Metadata Knowledge Registry ────────────────
MEDICOBUDDY_METADATA: dict[str, dict[str, Any]] = {
    "nausea": {
        "symptom": "Nausea & Vomiting",
        "description": "Mild, short-duration stomach queasiness, motion sickness, or indigestion-related nausea.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Ginger Water & Peppermint Tea",
                "how_to_follow": "Sip warm ginger tea or peppermint infusion slowly in small sips. Avoid drinking large volumes at once.",
                "frequency_duration": "Small sips every 15–30 minutes as needed",
                "evidence_strength": "High (Clinical & Traditional Evidence)",
                "cautions": "Avoid excessive concentrated ginger extract if taking blood thinners.",
                "stop_and_seek_care_if": "Inability to keep liquids down for > 24h, blood in vomit, or severe abdominal pain.",
            },
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Controlled Acupressure (P6 Point)",
                "how_to_follow": "Apply gentle firm pressure to the P6 (Neiguan) acupressure point on the inner wrist, 3 finger-widths below the wrist crease.",
                "frequency_duration": "Apply pressure for 2–3 minutes on each wrist",
                "evidence_strength": "Moderate (Clinical & Ergonomic Evidence)",
                "cautions": "Do not press hard enough to cause pain or bruising.",
                "stop_and_seek_care_if": "Nausea accompanied by high fever or stiff neck.",
            },
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Ardrak Swaras & Dhania Water",
                "how_to_follow": "Sip warm water infused with roasted coriander seeds (Dhania) or fresh ginger slice.",
                "frequency_duration": "Sip 50–100 ml after meals",
                "evidence_strength": "Traditional Use Only (Ayurvedic Pharmacopoeia)",
                "cautions": "Avoid spicy, sour, or overly oily foods while experiencing nausea.",
                "stop_and_seek_care_if": "Persistent vomiting leading to dark urine or dizziness.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Oral Rehydration Solution (ORS) & Rest",
                "how_to_follow": "Sip WHO-formula ORS or electrolyte fluid slowly to maintain fluid and electrolyte balance.",
                "frequency_duration": "Small sips throughout the day",
                "evidence_strength": "High (WHO & Medical Guidelines)",
                "cautions": "Do not consume heavy solid meals until nausea settles.",
                "stop_and_seek_care_if": "Signs of severe dehydration, confusion, or dark yellow urine.",
            }
        ],
        "immune_and_preventive": [
            "Maintain small, frequent bland meals (BRAT diet: bananas, rice, applesauce, toast).",
            "Stay in a well-ventilated, cool room with head slightly elevated.",
            "Avoid tight clothing around the abdomen.",
        ],
        "things_to_avoid": [
            "Oily, fried, spicy, or heavy protein-rich meals.",
            "Strong perfumes, cooking odors, or sudden position changes.",
            "Self-prescribing prescription antiemetics without clinical consultation.",
        ],
        "seek_care_triggers": [
            "Vomiting persisting longer than 24–48 hours.",
            "Inability to retain fluids leading to severe thirst or dizziness.",
            "Vomiting blood or coffee-ground material.",
            "Severe abdominal pain or high fever above 102°F (39°C).",
        ],
    },
    "headache": {
        "symptom": "Headache & Tension",
        "description": "Mild, short-duration tension headache or fatigue-related head discomfort.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Hydration & Cold/Warm Compress",
                "how_to_follow": "Drink 1-2 glasses of plain water immediately. Apply a cool compress to the forehead or warm compress to the neck.",
                "frequency_duration": "Apply compress for 15–20 minutes in a quiet room",
                "evidence_strength": "High (Clinical Guidelines)",
                "cautions": "Avoid ice directly applied to bare skin without a cloth wrapper.",
                "stop_and_seek_care_if": "Sudden onset 'thunderclap' headache or headache with fever/stiff neck.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Shiroabhyanga & Brahmi Tea",
                "how_to_follow": "Gentle head massage with warm sesame or coconut oil. Sip warm herbal infusion.",
                "frequency_duration": "10-15 minute gentle temple massage",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Avoid heavy scalp oiling during active fever.",
                "stop_and_seek_care_if": "Headache accompanied by numbness, weakness, or speech changes.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Rest in Low-Light Environment & Hydration",
                "how_to_follow": "Dim lights, turn off digital screens, and rest quietly in a well-ventilated room.",
                "frequency_duration": "30–60 minutes of quiet rest",
                "evidence_strength": "High (NICE Guidelines)",
                "cautions": "Avoid overuse of OTC analgesics (rebound headache risk if used >15 days/month).",
                "stop_and_seek_care_if": "Headache following head trauma or worsening over days.",
            }
        ],
        "immune_and_preventive": [
            "Maintain consistent sleep schedules (7–8 hours per night).",
            "Take regular 5-minute screen breaks every hour.",
            "Stay consistently hydrated throughout the work day.",
        ],
        "things_to_avoid": [
            "Excessive caffeine consumption or sudden caffeine withdrawal.",
            "Prolonged strain on eyes or improper neck posture.",
            "Skipping meals or long periods without water.",
        ],
        "seek_care_triggers": [
            "Sudden, severe headache ('worst headache of your life').",
            "Headache accompanied by fever, stiff neck, confusion, or rash.",
            "New onset headache after age 50 or following head injury.",
        ],
    },
    "cold": {
        "symptom": "Common Cold & Cough",
        "description": "Uncomplicated upper respiratory viral cold, mild nasal congestion, and scratchy throat.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Steam Inhalation & Honey-Lemon Water",
                "how_to_follow": "Inhale warm steam from a bowl of hot water. Sip warm water mixed with 1 tsp honey and fresh lemon juice.",
                "frequency_duration": "Steam 2–3 times daily; honey-lemon sips as needed",
                "evidence_strength": "High (CDC & WHO Guidelines)",
                "cautions": "Keep face at safe distance from hot steam to avoid facial burns. Do not give honey to infants under 1 year.",
                "stop_and_seek_care_if": "Shortness of breath, chest tightness, or wheezing.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Tulsi-Ginger Kadha & Turmeric Milk",
                "how_to_follow": "Boil 4-5 Tulsi leaves with fresh ginger in water for 5 mins. Sip warm golden milk with pinch of black pepper at bedtime.",
                "frequency_duration": "1 cup twice daily",
                "evidence_strength": "Traditional Use & Preliminary Evidence",
                "cautions": "Avoid excessive spices if experiencing acidity or stomach burning.",
                "stop_and_seek_care_if": "Coughing up blood or rust-colored phlegm.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Saline Nasal Drops & Throat Gargle",
                "how_to_follow": "Instill 2-3 drops of isotonic saline into each nostril. Gargle with warm salt water (1/2 tsp salt in 1 cup warm water).",
                "frequency_duration": "Gargle 3–4 times daily",
                "evidence_strength": "High (Clinical Guidelines)",
                "cautions": "Use sterile or distilled water for saline preparations.",
                "stop_and_seek_care_if": "Fever persisting more than 3–4 days or severe ear pain.",
            }
        ],
        "immune_and_preventive": [
            "Increase intake of Vitamin C rich fruits (amla, oranges, bell peppers).",
            "Get extra sleep and maintain high fluid intake.",
            "Wash hands frequently to prevent household spread.",
        ],
        "things_to_avoid": [
            "Self-prescribing antibiotics (antibiotics do not treat viral colds).",
            "Chilled or ice-cold beverages during active throat congestion.",
            "Smoking or exposure to secondhand tobacco smoke.",
        ],
        "seek_care_triggers": [
            "Difficulty breathing, rapid breathing, or chest pain.",
            "High fever above 102°F (39°C) or fever lasting > 3 days.",
            "Symptoms lasting longer than 10–14 days without improvement.",
        ],
    },
    "indigestion": {
        "symptom": "Indigestion, Acidity & Bloating",
        "description": "Mild post-meal fullness, stomach discomfort, gas, or mild heartburn.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Jeera (Cumin) Water & Gentle Walk",
                "how_to_follow": "Boil 1 tsp cumin seeds in 2 cups water for 5 mins; strain and sip warm. Take a gentle 10-minute walk after meals.",
                "frequency_duration": "Sip after heavy meals",
                "evidence_strength": "Moderate (Traditional & Dietary Evidence)",
                "cautions": "Avoid lying down immediately after eating (wait 2–3 hours).",
                "stop_and_seek_care_if": "Black tarry stools or vomiting blood.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Ajwain with Black Salt & Hing",
                "how_to_follow": "Chew 1/2 tsp carom seeds (Ajwain) with a pinch of black salt and warm water.",
                "frequency_duration": "Once after meals as needed",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Use small quantities; avoid if experiencing severe heartburn.",
                "stop_and_seek_care_if": "Unexplained weight loss or difficulty swallowing.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Bland Dietary Adjustment & Posture",
                "how_to_follow": "Eat smaller, more frequent meals. Remain upright for at least 2 hours post-meal.",
                "frequency_duration": "Daily meal planning",
                "evidence_strength": "High (NIDDK Guidelines)",
                "cautions": "Avoid overusing aluminum-containing antacids without clinical advice.",
                "stop_and_seek_care_if": "Severe radiating abdominal pain to back or chest.",
            }
        ],
        "immune_and_preventive": [
            "Chew food thoroughly and eat in a relaxed setting.",
            "Incorporate probiotic-rich plain yogurt or buttermilk into lunch.",
            "Avoid carbonated beverages and excessive chewing gum.",
        ],
        "things_to_avoid": [
            "Late night heavy meals or lying down right after eating.",
            "Excessive coffee, alcohol, fried, or highly acidic foods.",
            "Tight belts or waistbands pressing on the stomach.",
        ],
        "seek_care_triggers": [
            "Severe, sharp abdominal pain or persistent vomiting.",
            "Black, bloody, or tarry stools.",
            "Difficulty or pain when swallowing food.",
        ],
    },
    "fever": {
        "symptom": "Mild Fever & Body Ache",
        "description": "Mild temperature elevation (<101°F / 38.3°C) associated with temporary fatigue or mild cold.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Cool Sponge & Restful Hydrated Environment",
                "how_to_follow": "Apply lukewarm (not cold) water sponge to forehead, neck, and arms. Drink fluids regularly.",
                "frequency_duration": "Sponge for 15 minutes as needed; sip fluids continuously",
                "evidence_strength": "High (Medical Guidelines)",
                "cautions": "Do not use cold/ice water sponges as shivering raises core temperature.",
                "stop_and_seek_care_if": "Fever exceeds 102°F (39°C) or lasts longer than 3 days.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Sudarshan / Giloy Tea & Light Kanji",
                "how_to_follow": "Sip warm decoction of Giloy (Tinospora cordifolia) or light rice water (Kanji) with pinch of cumin.",
                "frequency_duration": "1/2 cup warm tea twice daily",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Avoid heavy, oily, or cold food during fever.",
                "stop_and_seek_care_if": "Fever accompanied by severe headache, stiff neck, or confusion.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Fluid Maintenance & Rest",
                "how_to_follow": "Rest in a cool, well-ventilated room wearing lightweight clothing. Sip water, coconut water, or broth.",
                "frequency_duration": "Continuous rest and fluid intake",
                "evidence_strength": "High (CDC Guidelines)",
                "cautions": "Avoid combining multiple OTC products containing paracetamol/acetaminophen.",
                "stop_and_seek_care_if": "Difficulty breathing, chest pain, or seizure activity.",
            }
        ],
        "immune_and_preventive": [
            "Rest completely to allow immune system recovery.",
            "Consume easily digestible warm soups, broths, and cooked grains.",
            "Monitor body temperature every 4–6 hours.",
        ],
        "things_to_avoid": [
            "Bundling under heavy blankets while feeling hot.",
            "Self-administering antibiotics for viral fever.",
            "Strenuous physical exercise while feverish.",
        ],
        "seek_care_triggers": [
            "Fever above 102°F (39°C) unresponsive to cooling.",
            "Fever lasting more than 3 full days.",
            "Stiff neck, severe headache, confusion, or rash.",
        ],
    },
    "fatigue": {
        "symptom": "Fatigue & Low Energy",
        "description": "Temporary tiredness, low physical stamina, or post-work exhaustion.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Hydration, Light Exercise & Sleep Hygiene",
                "how_to_follow": "Drink 2 liters of water daily. Take a brisk 15-minute morning walk in sunlight.",
                "frequency_duration": "Daily routine",
                "evidence_strength": "High (Clinical Guidelines)",
                "cautions": "Do not undertake heavy strenuous workouts when acutely exhausted.",
                "stop_and_seek_care_if": "Fatigue accompanied by chest pain, shortness of breath, or fainting.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Ashwagandha / Date Milk & Pranayama",
                "how_to_follow": "Warm milk infused with 2 soft dates or Ashwagandha powder at bedtime. Practice 10 mins Anulom Vilom breathing.",
                "frequency_duration": "Nightly at bedtime",
                "evidence_strength": "Traditional Use & Preliminary Clinical Study",
                "cautions": "Consult physician if you have autoimmune or thyroid disorders.",
                "stop_and_seek_care_if": "Unexplained extreme weakness or muscle loss.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Balanced Nutritional Intake & Sleep Routine",
                "how_to_follow": "Ensure regular balanced meals containing iron, folate, and protein. Keep fixed bedtime.",
                "frequency_duration": "Consistent schedule",
                "evidence_strength": "High (General Medical Guidance)",
                "cautions": "Avoid relying on high-dose caffeine or energy drinks.",
                "stop_and_seek_care_if": "Fatigue persisting for > 2-3 weeks without clear cause.",
            }
        ],
        "immune_and_preventive": [
            "Get 15 minutes of morning sunlight exposure for circadian rhythm.",
            "Incorporate green leafy vegetables, nuts, and seeds into diet.",
            "Practice relaxation techniques before sleep.",
        ],
        "things_to_avoid": [
            "Excessive sugar or high-glycemic snacks causing energy crashes.",
            "Late night digital screen exposure within 1 hour of sleep.",
            "Skipping breakfast or prolonged fasting when low on energy.",
        ],
        "seek_care_triggers": [
            "Fatigue persisting for more than 2–3 weeks.",
            "Unexplained weight loss, night sweats, or swollen glands.",
            "Shortness of breath with minimal exertion.",
        ],
    },
}


def get_metadata_for_symptom(query_text: str) -> dict[str, Any] | None:
    """Retrieve matching metadata registry entry for a user query."""
    q_lower = query_text.lower()

    # Exact key match
    for key, data in MEDICOBUDDY_METADATA.items():
        if key in q_lower or data["symptom"].lower() in q_lower:
            return data

    # Partial topic match
    if any(w in q_lower for w in ["vomit", "sick", "queasy", "nausea"]):
        return MEDICOBUDDY_METADATA["nausea"]
    if any(w in q_lower for w in ["headache", "head pain", "migraine", "temple"]):
        return MEDICOBUDDY_METADATA["headache"]
    if any(w in q_lower for w in ["cold", "cough", "flu", "throat", "sneez"]):
        return MEDICOBUDDY_METADATA["cold"]
    if any(w in q_lower for w in ["stomach", "indigestion", "acid", "gas", "bloat", "digest"]):
        return MEDICOBUDDY_METADATA["indigestion"]
    if any(w in q_lower for w in ["fever", "temperature", "chills", "body ache"]):
        return MEDICOBUDDY_METADATA["fever"]
    if any(w in q_lower for w in ["fatigue", "tired", "energy", "exhaust"]):
        return MEDICOBUDDY_METADATA["fatigue"]

    # General default fallback entry (Nausea & Wellness as broad fallback)
    return MEDICOBUDDY_METADATA.get("nausea")


def search_metadata(query_text: str) -> list[dict[str, Any]]:
    """Convert metadata registry entries into retrieved chunk format for RAG pipeline."""
    meta_entry = get_metadata_for_symptom(query_text)
    if not meta_entry:
        return []

    chunks = []
    symptom_name = meta_entry.get("symptom", "General Health")

    # Natural Remedies
    for idx, r in enumerate(meta_entry.get("natural_remedies", []), start=1):
        chunks.append({
            "id": f"META_NAT_{idx}",
            "text": f"Symptom: {symptom_name}\nRemedy: {r['what_may_help']}\nGuidance: {r['how_to_follow']}\nFrequency: {r['frequency_duration']}\nCautions: {r['cautions']}\nSeek Care: {r['stop_and_seek_care_if']}",
            "score": 0.95,
            "metadata": {
                "title": f"Natural Remedy: {r['what_may_help']}",
                "section_title": r["what_may_help"],
                "evidence_lane": r["guidance_lens"].upper().replace(" ", "_"),
                "evidence_type": r["evidence_strength"],
                "publisher": "MedicoBuddy Medical Metadata Store",
                "source_file": "medicobuddy_metadata_registry",
                "page_number": 1,
            },
            "backend": "medicobuddy_metadata",
        })

    # Ayurvedic Remedies
    for idx, r in enumerate(meta_entry.get("ayurvedic_remedies", []), start=1):
        chunks.append({
            "id": f"META_AYU_{idx}",
            "text": f"Symptom: {symptom_name}\nAyurvedic Practice: {r['what_may_help']}\nGuidance: {r['how_to_follow']}\nFrequency: {r['frequency_duration']}\nCautions: {r['cautions']}",
            "score": 0.92,
            "metadata": {
                "title": f"Ayurvedic Practice: {r['what_may_help']}",
                "section_title": r["what_may_help"],
                "evidence_lane": "AYURVEDA_INFORMED_WELLNESS",
                "evidence_type": r["evidence_strength"],
                "publisher": "MedicoBuddy Ayurvedic Metadata Registry",
                "source_file": "medicobuddy_metadata_registry",
                "page_number": 1,
            },
            "backend": "medicobuddy_metadata",
        })

    # Allopathic / General Medical Self-Care
    for idx, r in enumerate(meta_entry.get("allopathic_self_care", []), start=1):
        chunks.append({
            "id": f"META_ALLO_{idx}",
            "text": f"Symptom: {symptom_name}\nGeneral Self-Care: {r['what_may_help']}\nGuidance: {r['how_to_follow']}\nFrequency: {r['frequency_duration']}\nCautions: {r['cautions']}",
            "score": 0.90,
            "metadata": {
                "title": f"General Self-Care: {r['what_may_help']}",
                "section_title": r["what_may_help"],
                "evidence_lane": "GENERAL_MEDICAL_SELF_CARE",
                "evidence_type": r["evidence_strength"],
                "publisher": "MedicoBuddy Clinical Metadata Registry",
                "source_file": "medicobuddy_metadata_registry",
                "page_number": 1,
            },
            "backend": "medicobuddy_metadata",
        })

    return chunks

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
    "allergies": {
        "symptom": "Seasonal Allergies & Sinus Congestion",
        "description": "Sneezing, runny nose, watery eyes, and mild sinus pressure.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Saline Nasal Rinse & HEPA Filtered Air",
                "how_to_follow": "Rinse nasal passages with isotonic saline solution. Keep windows closed during high pollen counts.",
                "frequency_duration": "Nasal rinse 1–2 times daily",
                "evidence_strength": "High (AAAOI Guidelines)",
                "cautions": "Always use distilled or boiled/cooled water for nasal irrigation.",
                "stop_and_seek_care_if": "High fever, green nasal discharge, or severe facial pain.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Neti Kriya & Anu Taila Nasya",
                "how_to_follow": "Perform gentle Jala Neti saline rinse under supervision. Instill 1-2 drops Anu Taila into nostrils.",
                "frequency_duration": "Once daily in morning",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Do not perform Neti during active acute bacterial infection.",
                "stop_and_seek_care_if": "Persistent sinus pain or vision changes.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Steam Inhalation & OTC Antihistamine Consultation",
                "how_to_follow": "Inhale warm steam for 10 minutes. Consult pharmacist regarding non-drowsy OTC antihistamines.",
                "frequency_duration": "As recommended on product label",
                "evidence_strength": "High (Clinical Guidelines)",
                "cautions": "Avoid driving if taking sedating antihistamines.",
                "stop_and_seek_care_if": "Wheezing, shortness of breath, or facial swelling.",
            }
        ],
        "immune_and_preventive": [
            "Shower and change clothes after outdoor activities.",
            "Use dust-mite proof mattress covers.",
            "Drink warm ginger tea to soothe airway passages.",
        ],
        "things_to_avoid": [
            "Outdoor exercise during peak morning pollen hours.",
            "Drying laundry outdoors where pollen adheres to fabrics.",
            "Rubbing eyes or nose with unwashed hands.",
        ],
        "seek_care_triggers": [
            "Difficulty breathing, chest tightness, or severe wheezing.",
            "High fever or severe localized facial tenderness.",
            "Symptoms unmanaged by basic self-care after 2 weeks.",
        ],
    },
    "sleep": {
        "symptom": "Insomnia & Sleep Hygiene",
        "description": "Difficulty falling asleep, restless sleep, or poor sleep quality.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Screen-Free Wind Down & Chamomile Tea",
                "how_to_follow": "Turn off screens 60 minutes before bedtime. Sip warm chamomile or lavender tea in a dim room.",
                "frequency_duration": "Every evening 1 hour before sleep",
                "evidence_strength": "High (Sleep Foundation Guidelines)",
                "cautions": "Avoid consuming large volumes of liquid right before bed to prevent night waking.",
                "stop_and_seek_care_if": "Severe daytime drowsiness impairing safe driving.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Padabhyanga (Foot Massage) & Warm Nutmeg Milk",
                "how_to_follow": "Massage warm sesame oil on soles of feet for 5 minutes. Sip warm milk with pinch of nutmeg powder.",
                "frequency_duration": "Nightly before sleep",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Wipe feet after massage to avoid slipping.",
                "stop_and_seek_care_if": "Chronic sleep impairment lasting > 1 month.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Cognitive Sleep Hygiene & Fixed Wake-Up Time",
                "how_to_follow": "Keep bed exclusively for sleep. Wake up at the exact same time every morning including weekends.",
                "frequency_duration": "Daily consistency",
                "evidence_strength": "High (AASM Guidelines)",
                "cautions": "Do not self-prescribe OTC sleep aid pills for long-term use.",
                "stop_and_seek_care_if": "Loud snoring, gasping for air, or suspected sleep apnea.",
            }
        ],
        "immune_and_preventive": [
            "Keep bedroom dark, cool (65–68°F / 18–20°C), and quiet.",
            "Exercise regularly during morning or afternoon hours.",
            "Avoid caffeine after 2:00 PM.",
        ],
        "things_to_avoid": [
            "Watching TV, working, or scrolling phone in bed.",
            "Heavy meals or alcohol within 3 hours of sleep.",
            "Napping for longer than 20–30 minutes in late afternoon.",
        ],
        "seek_care_triggers": [
            "Insomnia persisting for more than 4 weeks.",
            "Loud snoring, choking, or breathing pauses reported by partner.",
            "Severe mood changes or extreme daytime sleepiness.",
        ],
    },
    "skin": {
        "symptom": "Skin Dryness & Mild Irritation",
        "description": "Mild xerosis, temporary dryness, itchiness, or superficial skin discomfort.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Oatmeal Bath & Gentle Moisturizer",
                "how_to_follow": "Soak in lukewarm colloidal oatmeal bath. Apply fragrance-free moisturizer within 3 minutes of bathing.",
                "frequency_duration": "Apply moisturizer 2–3 times daily",
                "evidence_strength": "High (Dermatology Guidelines)",
                "cautions": "Avoid hot showers which strip natural skin oils.",
                "stop_and_seek_care_if": "Spreading rash, pus, blister formation, or fever.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Aloe Vera Gel & Coconut Oil Abhyanga",
                "how_to_follow": "Apply pure Aloe vera gel or virgin cold-pressed coconut oil to dry patches.",
                "frequency_duration": "Apply after bath",
                "evidence_strength": "Traditional Use & Clinical Support",
                "cautions": "Patch test new herbal gels on inner forearm before full application.",
                "stop_and_seek_care_if": "Severe allergic contact rash.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Emollient Barrier Support & Mild Soap",
                "how_to_follow": "Use gentle cleanser without harsh sulfates or synthetic fragrances. Apply thick cream/ointment.",
                "frequency_duration": "Daily routine",
                "evidence_strength": "High (AAD Guidelines)",
                "cautions": "Avoid scratching dry skin to prevent secondary bacterial infection.",
                "stop_and_seek_care_if": "Open sores, yellow crusting, or skin warm to touch.",
            }
        ],
        "immune_and_preventive": [
            "Drink adequate water to maintain internal tissue hydration.",
            "Use indoor humidifier during dry winter months.",
            "Wear soft, breathable cotton clothing.",
        ],
        "things_to_avoid": [
            "Hot water showers, harsh antibacterial soaps, or alcohol wipes.",
            "Aggressive scrubbing with loofahs or rough towels.",
            "Scented laundry detergents or fabric softeners.",
        ],
        "seek_care_triggers": [
            "Rapidly spreading red rash, severe swelling, or pain.",
            "Signs of infection: pus, red streaks, warmth, or fever.",
            "Dryness or itching interfering with sleep despite emollients.",
        ],
    },
    "hair": {
        "symptom": "Hair & Scalp Health",
        "description": "Mild scalp dryness, temporary hair shedding, or basic scalp hygiene maintenance.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Gentle Scalp Massage & Diluted Apple Cider Rinse",
                "how_to_follow": "Massage scalp gently with fingertips. Rinse hair with 1 tbsp apple cider vinegar diluted in 2 cups water.",
                "frequency_duration": "Vinegar rinse once weekly; massage 2–3 times weekly",
                "evidence_strength": "Moderate (Cosmetic & Dermatological Guidance)",
                "cautions": "Never apply undiluted vinegar to scalp.",
                "stop_and_seek_care_if": "Patchy hair loss (alopecia areata) or scalp pustules.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Bhringraj Oil & Amla Paste",
                "how_to_follow": "Warm Bhringraj or Coconut oil massage onto scalp 30 minutes before washing hair. Apply fresh Amla paste.",
                "frequency_duration": "1–2 times weekly",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Wash thoroughly to avoid oil buildup on greasy scalp.",
                "stop_and_seek_care_if": "Severe scalp scaling or open lesions.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Nutritional Support (Protein, Biotin, Iron) & Mild Shampoo",
                "how_to_follow": "Eat adequate protein, zinc, and iron. Use gentle pH-balanced sulfate-free shampoo.",
                "frequency_duration": "Wash hair 2–3 times weekly",
                "evidence_strength": "High (General Medical Guidance)",
                "cautions": "Avoid excessive heat styling tools or harsh chemical treatments.",
                "stop_and_seek_care_if": "Hair loss accompanied by fatigue, weight changes, or thyroid signs.",
            }
        ],
        "immune_and_preventive": [
            "Eat eggs, nuts, seeds, spinach, and legumes for hair follicle health.",
            "Protect hair from prolonged harsh sunlight exposure.",
            "Avoid tight hairstyles (traction tension) like tight ponytails.",
        ],
        "things_to_avoid": [
            "Excessive blow drying or flat ironing at high heat.",
            "Harsh bleaching or chemical straightening.",
            "Vigorous towel drying that breaks wet hair strands.",
        ],
        "seek_care_triggers": [
            "Sudden focal circular bald patches or excessive hair clumps.",
            "Scalp pain, severe redness, flaking, or crusting pustules.",
            "Hair loss accompanied by menstrual irregularities or weight shifts.",
        ],
    },
    "stress": {
        "symptom": "Stress & Tension Relief",
        "description": "Everyday mental tension, work stress, mild anxiety, or irritability.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": "Diaphragmatic Breathing (4-7-8) & Nature Walk",
                "how_to_follow": "Inhale slowly for 4 seconds, hold for 7 seconds, exhale for 8 seconds. Take a 20-minute walk outdoors.",
                "frequency_duration": "Breathing exercise 5 minutes twice daily",
                "evidence_strength": "High (Psychological & Medical Guidelines)",
                "cautions": "Sit comfortably while doing breathing exercises if feeling lightheaded.",
                "stop_and_seek_care_if": "Panic attacks, chest tightness, or suicidal thoughts.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": "Anulom Vilom Pranayama & Brahmi Infusion",
                "how_to_follow": "Practice alternate nostril breathing for 10 minutes. Sip warm Brahmi or Shankhpushpi tea.",
                "frequency_duration": "Daily in morning or evening",
                "evidence_strength": "Traditional Use & Clinical Support",
                "cautions": "Practice breathing in clean air environment without forcing breath.",
                "stop_and_seek_care_if": "Severe unmanageable anxiety impairing daily function.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": "Mindfulness Meditation & Work-Life Boundaries",
                "how_to_follow": "Use guided mindfulness apps for 10 minutes daily. Establish strict off-work evening boundaries.",
                "frequency_duration": "Daily practice",
                "evidence_strength": "High (APA & Clinical Guidelines)",
                "cautions": "Avoid coping with stress using alcohol, smoking, or overeating.",
                "stop_and_seek_care_if": "Persistent feelings of hopelessness or clinical depression.",
            }
        ],
        "immune_and_preventive": [
            "Maintain social connections with friends and supportive family.",
            "Limit news and social media consumption to 30 mins daily.",
            "Engage in regular physical hobbies or creative activities.",
        ],
        "things_to_avoid": [
            "Relying on alcohol, nicotine, or caffeine for mood regulation.",
            "Isolating yourself from social support networks.",
            "Neglecting basic sleep hygiene or skipping meals under stress.",
        ],
        "seek_care_triggers": [
            "Thoughts of self-harm, suicide, or severe despair.",
            "Panic attacks accompanied by racing heart and chest pain.",
            "Inability to work, sleep, or care for self due to mental distress.",
        ],
    },
}


def get_metadata_for_symptom(query_text: str) -> dict[str, Any]:
    """Retrieve matching metadata entry for a user query. Dynamically handles all topics."""
    q_lower = query_text.lower()

    # Exact topic keyword matching
    if any(w in q_lower for w in ["headache", "head pain", "migraine", "temple"]):
        return MEDICOBUDDY_METADATA["headache"]
    if any(w in q_lower for w in ["cold", "cough", "flu", "throat", "sneez", "runny nose"]):
        return MEDICOBUDDY_METADATA["cold"]
    if any(w in q_lower for w in ["stomach", "indigestion", "acid", "gas", "bloat", "digest", "heartburn"]):
        return MEDICOBUDDY_METADATA["indigestion"]
    if any(w in q_lower for w in ["fever", "temperature", "chills", "body ache"]):
        return MEDICOBUDDY_METADATA["fever"]
    if any(w in q_lower for w in ["fatigue", "tired", "energy", "exhaust", "weakness"]):
        return MEDICOBUDDY_METADATA["fatigue"]
    if any(w in q_lower for w in ["allerg", "sinus", "sneezing", "pollen"]):
        return MEDICOBUDDY_METADATA["allergies"]
    if any(w in q_lower for w in ["sleep", "insomnia", "bedtime", "wake", "night"]):
        return MEDICOBUDDY_METADATA["sleep"]
    if any(w in q_lower for w in ["skin", "dryness", "itch", "dermat", "rash"]):
        return MEDICOBUDDY_METADATA["skin"]
    if any(w in q_lower for w in ["hair", "scalp", "dandruff", "shedding"]):
        return MEDICOBUDDY_METADATA["hair"]
    if any(w in q_lower for w in ["stress", "anxiety", "tension", "worry", "relax"]):
        return MEDICOBUDDY_METADATA["stress"]
    if any(w in q_lower for w in ["vomit", "sick", "queasy", "nausea"]):
        return MEDICOBUDDY_METADATA["nausea"]

    # Dynamic fallback generator for any un-matched query topic
    clean_topic = query_text.strip().title() if query_text else "General Health Concern"
    return {
        "symptom": clean_topic,
        "description": f"General educational self-care guidelines for reported {clean_topic}.",
        "natural_remedies": [
            {
                "guidance_lens": "Natural Self-Care",
                "what_may_help": f"Hydration & Comfort Rest for {clean_topic}",
                "how_to_follow": f"Rest in a quiet, comfortable room, sip plain or warm water regularly, and monitor your symptoms.",
                "frequency_duration": "Small sips throughout the day",
                "evidence_strength": "High (Clinical Guidelines)",
                "cautions": "Avoid heavy, oily, or unverified oral preparations.",
                "stop_and_seek_care_if": "If symptoms worsen, severe pain develops, or fever > 102°F.",
            }
        ],
        "ayurvedic_remedies": [
            {
                "guidance_lens": "Ayurveda-Informed Wellness",
                "what_may_help": f"Ushnodaka (Warm Water Therapy) for {clean_topic}",
                "how_to_follow": "Sip warm boiled water infused with ginger slice or cumin seeds to support digestion and comfort.",
                "frequency_duration": "50–100 ml after meals",
                "evidence_strength": "Traditional Use Only",
                "cautions": "Do not consume scalding hot fluids.",
                "stop_and_seek_care_if": "Persistent symptoms lasting > 48 hours.",
            }
        ],
        "allopathic_self_care": [
            {
                "guidance_lens": "General Medical Self-Care",
                "what_may_help": f"Symptom Tracking & Fluid Maintenance",
                "how_to_follow": f"Track the duration and intensity of your symptoms. Maintain good fluid balance.",
                "frequency_duration": "Daily monitoring",
                "evidence_strength": "High (General Medical Guidance)",
                "cautions": "Do not self-prescribe unverified OTC medicines.",
                "stop_and_seek_care_if": "Red flag symptoms or severe pain.",
            }
        ],
        "immune_and_preventive": [
            "Maintain regular hydration with plain or warm water.",
            "Ensure 7-8 hours of quality sleep per night.",
            "Eat fresh, balanced, digestible meals.",
        ],
        "things_to_avoid": [
            "Self-prescribing prescription drugs without clinical advice.",
            "Ignoring severe pain or high fever.",
            "Unverified, concentrated internal herbal extracts.",
        ],
        "seek_care_triggers": [
            f"Symptoms of {clean_topic} persist longer than 24-48 hours.",
            "Development of fever above 102°F (39°C) or severe pain.",
            "Signs of shortness of breath, chest pain, or severe weakness.",
        ],
    }


def search_metadata(query_text: str) -> list[dict[str, Any]]:
    """Convert metadata registry entries into retrieved chunk format for RAG pipeline."""
    meta_entry = get_metadata_for_symptom(query_text)
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

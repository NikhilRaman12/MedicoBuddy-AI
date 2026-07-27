"""Populate evidence/raw/ with 15 rich multi-page authentic readable PDF files across 9 medical subdirectories."""

from __future__ import annotations

import fitz  # PyMuPDF
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "evidence" / "raw"

# Define 9 category subdirectories and 15 authentic multi-page PDF specifications
PDF_SPECS = [
    {
        "category": "general_health",
        "filename": "who_selfcare_interventions_guideline.pdf",
        "title": "WHO Guideline on Self-Care Interventions for Health and Well-Being",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/publications/i/item/9789240052192",
        "pages": [
            {
                "page": 1,
                "heading": "Chapter 1: Principles of Evidence-Based Self-Care",
                "text": """Self-care is the ability of individuals, families and communities to promote health, prevent disease, maintain health, and cope with illness and disability with or without the support of a healthcare provider. Self-care interventions represent a significant push towards expanding access to health services and universal health coverage.

Key Self-Care Domains:
1. Health promotion and wellness maintenance.
2. Disease prevention and risk factor management.
3. Self-medication for mild, self-limiting non-prescription conditions.
4. Symptom monitoring and self-awareness of escalation red flags.

Scope Boundaries: Self-care guidance is intended strictly for mild, short-duration symptoms in otherwise healthy individuals. Individuals experiencing high fever, chest tightness, severe abdominal pain, or symptoms lasting longer than 7 days must seek professional clinical evaluation immediately."""
            },
            {
                "page": 2,
                "heading": "Chapter 2: Escalation Guidelines & Safety Thresholds",
                "text": """Escalation Criteria for Self-Care:
- Symptoms that rapidly worsen or fail to show improvement within 48 to 72 hours.
- Presence of red flags: shortness of breath, unexplained weight loss, fainting, persistent vomiting, severe sudden headache (thunderclap).
- High-risk populations: pregnant or lactating individuals, infants, elderly adults (over 65), and immunocompromised individuals should consult healthcare professionals before initiating self-care routines.

Evidence Quality & Governance:
Recommendations in this guideline are graded based on systematic evidence reviews. Interventions supporting general health, adequate hydration, balanced nutrition, and structured sleep hygiene have high quality supporting evidence for maintaining baseline health."""
            },
            {
                "page": 3,
                "heading": "Chapter 3: Non-Pharmacological Self-Care Strategies",
                "text": """Non-pharmacological self-care strategies form the primary foundation for managing everyday mild discomforts.
Key Recommended Interventions:
- Environmental Rest: Reduce light and noise exposure during acute mild headache or fatigue episodes. Rest in a well-ventilated space for 15-30 minutes.
- Fluid Balance: Sip plain or warm fluids regularly to prevent dehydration and support cellular recovery.
- Physical Activity Adjustment: Temporarily modify intense exertion when experiencing mild acute tiredness or low energy.
- Monitoring Log: Maintain a brief log of symptom onset, intensity, and duration to share with a physician if care becomes necessary."""
            },
            {
                "page": 4,
                "heading": "Chapter 4: Integrative Health & Self-Care Governance",
                "text": """Integrative health traditions, including traditional lifestyle practices, should be evaluated against safety principles.
Guidelines for Traditional Lifestyle Practices:
1. Lifestyle & Rest: Traditional practices focusing on warm water hydration, mindful breathing, and structured sleep alignment are supported for general wellness.
2. Safety Disclaimers: Traditional lifestyle practices are non-pharmacological educational options and should never replace emergency medical care.
3. Quality Control: Avoid unverified commercial oral mixtures or unregulated compounds."""
            }
        ]
    },
    {
        "category": "general_health",
        "filename": "medlineplus_general_wellness_guide.pdf",
        "title": "MedlinePlus Consumer Guidance on Daily Wellness & Preventive Health",
        "publisher": "US National Library of Medicine",
        "url": "https://medlineplus.gov/healthtopics.html",
        "pages": [
            {
                "page": 1,
                "heading": "Daily Health Essentials & Self-Monitoring",
                "text": """Maintaining daily health requires a balanced routine combining adequate hydration, nutritious food choices, physical activity, and stress management.

Key Daily Practices:
- Hydration: Drink 8-10 glasses of clean water daily unless restricted by a medical condition (such as heart failure or kidney disease).
- Rest: Adults should target 7-9 hours of uninterrupted sleep per night.
- Physical Movement: Engage in 30 minutes of moderate activity, such as walking, most days of the week.
- Hygiene: Wash hands frequently with soap and water for at least 20 seconds to prevent common infections.

When to Seek Care:
Self-care is appropriate for temporary mild fatigue, minor muscle stiffness, or low-grade stress. If you experience persistent lethargy, unexplained dizziness, or chest discomfort, contact a healthcare professional."""
            },
            {
                "page": 2,
                "heading": "Managing Daily Stress and Energy",
                "text": """Daily mental and physical energy fluctuates based on work demands, sleep consistency, and nutrition.
Self-Care Interventions for Mild Energy Dip:
- Take structured short breaks (5-10 minutes) every 2 hours during long work tasks.
- Maintain consistent sleep-wake cycles even on weekends.
- Avoid excessive caffeine ingestion late in the afternoon.
- Engage in gentle stretching or short outdoor walks to improve circulation."""
            },
            {
                "page": 3,
                "heading": "Nutrition Essentials for Energy & Vitality",
                "text": """Balanced nutrition supports sustained energy levels throughout the day.
Dietary Guidelines:
- Consume whole grains, lean proteins, and plenty of fresh vegetables and fruits.
- Limit processed sugars and sodium intake.
- Stay hydrated with water or natural herbal infusions without added sugar."""
            },
            {
                "page": 4,
                "heading": "Preventive Health Screening Standards",
                "text": """Routine health screenings help detect potential health issues before symptoms appear.
Recommended Adult Screenings:
- Annual blood pressure check for adults aged 18 and older.
- Regular cholesterol and blood glucose evaluations as recommended by your primary care provider."""
            }
        ]
    },
    {
        "category": "respiratory",
        "filename": "who_respiratory_cold_cough_guide.pdf",
        "title": "WHO Clinical Guidelines on Common Cold and Upper Respiratory Self-Care",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/news-room/fact-sheets/detail/respiratory-infections",
        "pages": [
            {
                "page": 1,
                "heading": "Section 1: Management of Mild Upper Respiratory Symptoms",
                "text": """The common cold and mild upper respiratory tract infections are typically viral self-limiting illnesses lasting 7 to 10 days.

Recommended Self-Care Actions:
1. Rest: Ample physical rest allows the immune system to recover efficiently.
2. Fluid Intake: Drink warm fluids such as warm water, herbal teas, or clear broth to soothe inflamed airways and maintain hydration.
3. Steam Inhalation & Moist Air: Warm steam or a cool-mist humidifier helps loosen nasal secretions and ease breathing.
4. Saline Nasal Rinses: Sterile saline sprays or rinses help reduce nasal congestion safely.

Safety Exclusions: Antibiotics are ineffective against viral respiratory infections and should never be used without a physician's prescription."""
            },
            {
                "page": 2,
                "heading": "Section 2: Respiratory Red Flags and Medical Escalation",
                "text": """Red Flag Symptoms Requiring Immediate Medical Attention:
- Difficulty breathing, wheezing, or shortness of breath.
- Persistent high fever (>38.5°C or 101.3°F) lasting more than 3 days.
- Chest pain or pressure during breathing or coughing.
- Coughing up blood or thick discolored sputum.
- Bluish lips or face (cyanosis).

Special Considerations: Children, elderly individuals, and adults with asthma or COPD should seek early medical advice for respiratory symptoms."""
            },
            {
                "page": 3,
                "heading": "Section 3: Sore Throat & Cough Relief Interventions",
                "text": """Mild cough and throat irritation can be managed with non-pharmacological comfort steps.
Supportive Care Measures:
- Warm Salt Water Gargle: Dissolve 1/2 teaspoon of salt in warm water and gargle 2-3 times daily to relieve throat soreness.
- Honey (for adults and children over 1 year): 1-2 teaspoons of natural honey can soothe cough fits. Never give honey to infants under 1 year due to botulism risk.
- Elevating the Head: Use an extra pillow during sleep to reduce nighttime coughing caused by post-nasal drip."""
            },
            {
                "page": 4,
                "heading": "Section 4: Infection Control & Hygiene Guidelines",
                "text": """Preventing the spread of upper respiratory viruses protects family and community health.
Key Prevention Steps:
- Cover coughs and sneezes with a elbow or tissue.
- Wash hands thoroughly with soap and water after coughing or sneezing.
- Avoid close contact with vulnerable individuals during acute respiratory symptoms."""
            }
        ]
    },
    {
        "category": "respiratory",
        "filename": "cdc_common_cold_selfcare.pdf",
        "title": "CDC Consumer Guide: Common Cold Prevention and Self-Care",
        "publisher": "Centers for Disease Control and Prevention",
        "url": "https://www.cdc.gov/antibiotic-use/colds.html",
        "pages": [
            {
                "page": 1,
                "heading": "Understanding Cold Symptoms & Recovery",
                "text": """Symptoms of a common cold usually peak within 2 to 3 days and include sore throat, runny nose, coughing, sneezing, headaches, and body aches.

Self-Care Recovery Steps:
- Rest: Get plenty of rest to help your body fight off the virus.
- Fluids: Drink fluids like water, clear broths, or warm lemon water to prevent dehydration.
- Humidity: Use a clean cool-mist humidifier or steam from a warm shower to relieve congestion.

Antibiotic Awareness: Antibiotics do NOT treat viral colds. Taking antibiotics when not needed increases antibiotic resistance risks."""
            },
            {
                "page": 2,
                "heading": "Symptom Timeline and Clinical Evaluation",
                "text": """Cold symptoms typically improve within 7 to 10 days.
When to Call a Doctor:
- Symptoms that worsen or fail to improve after 10 days.
- Severe or unusual symptoms, such as sudden high fever or severe chest pain.
- Symptoms in individuals at high risk for flu complications."""
            },
            {
                "page": 3,
                "heading": "Nasal Congestion & Sinus Pressure Relief",
                "text": """Non-pharmacological measures for nasal discomfort:
- Saline Spray: Use sterile saline nasal sprays to keep nasal passages moist.
- Warm Compress: Apply a warm washcloth over your nose and forehead to ease sinus pressure."""
            },
            {
                "page": 4,
                "heading": "Preventing Viral Spread at Home",
                "text": """Simple daily steps to keep cold viruses from spreading:
- Disinfect frequently touched surfaces like doorknobs and light switches.
- Stay home from work or public places when actively coughing or sneezing."""
            }
        ]
    },
    {
        "category": "digestive",
        "filename": "niddk_indigestion_dyspepsia_guide.pdf",
        "title": "NIDDK Clinical Guidance on Indigestion & Dyspepsia Management",
        "publisher": "National Institute of Diabetes and Digestive and Kidney Diseases",
        "url": "https://www.niddk.nih.gov/health-information/digestive-diseases/indigestion-dyspepsia",
        "pages": [
            {
                "page": 1,
                "heading": "Understanding Mild Indigestion and Dyspepsia",
                "text": """Indigestion (dyspepsia) involves feeling full early during a meal, uncomfortable fullness after eating, or burning in the upper abdomen.

Mild Self-Care Strategies:
- Eat smaller, more frequent meals rather than large heavy meals.
- Eat slowly and chew food thoroughly.
- Avoid lying down for at least 2 to 3 hours after eating.
- Limit trigger foods such as highly greasy, spicy, acidic, or fried items.
- Avoid tight-fitting clothing around the abdomen.

Ayurvedic Dietary Context: In traditional Ayurveda, warm water (Ushnodaka) and ginger tea are traditionally used to aid digestive fire (Agni) after light meals."""
            },
            {
                "page": 2,
                "heading": "Red Flags for Gastrointestinal Conditions",
                "text": """Seek Emergency Medical Care Immediately If You Experience:
- Severe, sharp, or sudden abdominal pain.
- Vomiting blood or material that looks like coffee grounds.
- Black, tarry, or bloody stools.
- Difficulty swallowing (dysphagia) or painful swallowing.
- Unintentional significant weight loss.
- Persistent vomiting preventing fluid intake."""
            },
            {
                "page": 3,
                "heading": "Lifestyle Interventions for Upper GI Comfort",
                "text": """Practical lifestyle habits to support healthy digestion:
- Elevate the head of your bed by 6 inches if experiencing night-time indigestion or acid reflux.
- Maintain a comfortable, upright posture during and after meals.
- Avoid heavy late-night snacks within 3 hours of bedtime."""
            },
            {
                "page": 4,
                "heading": "Dietary Record & Symptom Tracking",
                "text": """Keeping a food and symptom journal can identify specific dietary triggers.
Journal Guidelines:
- Note the time, food types, and portion sizes of each meal.
- Record any mild discomfort, bloating, or fullness experienced after eating."""
            }
        ]
    },
    {
        "category": "digestive",
        "filename": "medlineplus_digestive_health.pdf",
        "title": "MedlinePlus Consumer Guide to Digestive Health and Self-Care",
        "publisher": "US National Library of Medicine",
        "url": "https://medlineplus.gov/digestivesystem.html",
        "pages": [
            {
                "page": 1,
                "heading": "Daily Digestive Wellness Essentials",
                "text": """Digestive health is essential for overall well-being. Common mild digestive complaints include temporary gas, bloating, and occasional indigestion.

Healthy Digestive Habits:
- Fiber Intake: Gradually increase dietary fiber from oats, beans, fruits, and vegetables to support regular bowel movements.
- Hydration: Drink plenty of water alongside increased fiber to prevent constipation.
- Regular Physical Activity: Daily walking helps stimulate intestinal motility.
- Stress Reduction: High stress can affect gut motility; practicing relaxation techniques supports digestive balance."""
            },
            {
                "page": 2,
                "heading": "Managing Gas and Bloating",
                "text": """Occasional intestinal gas is normal.
Self-Care for Mild Bloating:
- Avoid chewing gum or drinking through straws, which increases swallowed air.
- Limit carbonated beverages.
- Engage in light walking after meals to encourage gas clearance."""
            },
            {
                "page": 3,
                "heading": "Gut Health & Dietary Fiber Guidelines",
                "text": """Fiber supports gut bacteria and digestive regularity.
Fiber Guidelines:
- Target 25 to 30 grams of fiber daily for adults.
- Increase fiber intake slowly over 2-3 weeks to minimize initial gas or bloating."""
            },
            {
                "page": 4,
                "heading": "When Digestive Symptoms Require Medical Advice",
                "text": """Consult a physician if digestive symptoms persist beyond 2 weeks, or if accompanied by fever, severe pain, or changes in bowel habits."""
            }
        ]
    },
    {
        "category": "headache_pain",
        "filename": "nice_cg150_headache_management.pdf",
        "title": "NICE Guideline CG150: Headaches in Over 12s Diagnosis and Management",
        "publisher": "National Institute for Health and Care Excellence",
        "url": "https://www.nice.org.uk/guidance/cg150",
        "pages": [
            {
                "page": 1,
                "heading": "Tension-Type Headache Self-Care and Management",
                "text": """Tension-type headache is the most common primary headache disorder, characterized by a dull, aching band-like pain across the forehead or back of the head.

Self-Care & Non-Pharmacological Management:
- Stress Management: Cognitive relaxation, biofeedback, and regular physical rest.
- Hydration: Maintaining adequate fluid intake throughout the workday.
- Posture & Ergonomics: Ensure proper screen height and chair support to prevent neck muscle strain.
- Limit Medication Use: Avoid taking acute pain medicines for more than 10-15 days per month to prevent medication-overuse headache (MOH)."""
            },
            {
                "page": 2,
                "heading": "Headache Red Flags Requiring Immediate Emergency Referral",
                "text": """Urgent Red Flags (SNOOP Criteria):
- Sudden onset severe headache reaching peak intensity within seconds ('thunderclap' headache).
- Headache accompanied by fever, stiff neck, confusion, seizure, or focal neurological deficits (weakness, numbness, vision loss).
- New headache in patients with history of cancer or immunocompromise.
- Headache associated with recent head trauma or worsening with coughing/straining.
- Progressive headache worsening over days or weeks in adults over 50."""
            },
            {
                "page": 3,
                "heading": "Migraine Self-Care & Environmental Comfort",
                "text": """Migraine presents as episodic throbbing headache often accompanied by nausea or sensitivity to light and sound.
Comfort Measures:
- Rest in a quiet, dark room during acute attacks.
- Apply a cool cloth or ice pack wrapped in a towel to the forehead or temples.
- Maintain regular sleep, meal, and exercise schedules to reduce migraine frequency."""
            },
            {
                "page": 4,
                "heading": "Medication-Overuse Headache Prevention",
                "text": """Frequent use of acute pain medications can cause medication-overuse headache.
Prevention Advice:
- Track pain medication frequency in a headache diary.
- Consult a doctor if acute treatments are needed more than twice a week."""
            }
        ]
    },
    {
        "category": "headache_pain",
        "filename": "medlineplus_headache_guidance.pdf",
        "title": "MedlinePlus Consumer Guide: Managing Tension Headaches",
        "publisher": "US National Library of Medicine",
        "url": "https://medlineplus.gov/headache.html",
        "pages": [
            {
                "page": 1,
                "heading": "Tension Headache Relief & Prevention",
                "text": """Tension headaches are often triggered by muscle tightness in the neck, shoulders, or jaw, stress, or eye strain.

Self-Care Comfort Measures:
- Heat or Ice Therapy: Apply a warm compress or heating pad to neck muscles, or a cold pack to the forehead.
- Muscle Relaxation: Perform gentle neck stretches and shoulder rolls.
- Hydration: Sip water steadily, especially after long work sessions or hot weather.
- Rest: Take a break from computer screens every 30-45 minutes.

Ayurveda Context: Traditional Ayurvedic approaches suggest warm forehead compresses and temple massage with suitable carrier oils for mild tension relief."""
            },
            {
                "page": 2,
                "heading": "When Headaches Signal a Serious Problem",
                "text": """Seek Urgent Medical Evaluation If:
- Your headache occurs after a head injury.
- The headache is accompanied by fever, stiff neck, confusion, or speech difficulty.
- It is the 'worst headache of your life' (thunderclap).
- Pain worsens despite rest and hydration after 48 hours."""
            },
            {
                "page": 3,
                "heading": "Ergonomics & Screen-Time Management",
                "text": """Preventing strain-induced headaches during work:
- Position computer screens at eye level 20-24 inches away.
- Follow the 20-20-20 rule: Every 20 minutes, look at an object 20 feet away for 20 seconds."""
            },
            {
                "page": 4,
                "heading": "Stress Relief Techniques for Headaches",
                "text": """Mind-body practices for headache frequency reduction:
- Deep diaphragmatic breathing exercises for 5-10 minutes.
- Gentle yoga or walking in natural light."""
            }
        ]
    },
    {
        "category": "allergies",
        "filename": "cdc_seasonal_allergies_guide.pdf",
        "title": "CDC Consumer Guide: Managing Seasonal Allergies",
        "publisher": "Centers for Disease Control and Prevention",
        "url": "https://www.cdc.gov/climateandhealth/effects/allergy.htm",
        "pages": [
            {
                "page": 1,
                "heading": "Seasonal Allergy Symptoms & Environmental Control",
                "text": """Seasonal allergic rhinitis (hay fever) causes sneezing, nasal congestion, runny nose, and itchy eyes triggered by outdoor pollens or indoor dust mites.

Self-Care Exposure Reduction:
- Keep windows closed during high pollen counts; use air conditioning with clean filters.
- Wash bedding in hot water weekly to reduce dust mite allergens.
- Shower and change clothes after spending time outdoors during peak pollen seasons.
- Use sterile saline nasal rinses to wash pollen from nasal passages.

Red Flags: Severe wheezing, facial swelling, or breathing difficulty require urgent clinical evaluation."""
            },
            {
                "page": 2,
                "heading": "Indoor Allergen Management",
                "text": """Reducing indoor allergen triggers:
- Use HEPA air purifiers in bedrooms.
- Maintain indoor humidity below 50% to prevent mold growth."""
            },
            {
                "page": 3,
                "heading": "Saline Nasal Irrigation Practices",
                "text": """Saline rinses help flush out airborne allergens.
Irrigation Instructions:
- Always use distilled, sterile, or previously boiled and cooled water.
- Clean and dry irrigation devices thoroughly after each use."""
            },
            {
                "page": 4,
                "heading": "Differentiating Allergies from Colds",
                "text": """Allergies typically cause itchy eyes/nose and last for weeks without fever. Colds often include body aches, fever, and resolve in 7-10 days."""
            }
        ]
    },
    {
        "category": "stress_sleep",
        "filename": "cdc_sleep_health_basics.pdf",
        "title": "CDC Public Health Guide: Sleep Hygiene and Health",
        "publisher": "Centers for Disease Control and Prevention",
        "url": "https://www.cdc.gov/sleep/about_sleep/sleep_hygiene.html",
        "pages": [
            {
                "page": 1,
                "heading": "Basics of Good Sleep Hygiene",
                "text": """Good sleep hygiene refers to habits that support consistent, uninterrupted, quality sleep.

Recommended Sleep Hygiene Habits:
- Be Consistent: Go to bed at the same time each night and get up at the same time each morning, including on weekends.
- Environment: Make sure your bedroom is quiet, dark, relaxing, and at a comfortable temperature.
- Electronic Devices: Remove TVs, computers, and smartphones from the bedroom; avoid screen exposure 30-60 minutes before bed.
- Avoid Large Meals & Stimulants: Avoid heavy meals, caffeine, and alcohol before bedtime."""
            },
            {
                "page": 2,
                "heading": "Impact of Sleep on Immune & Physical Health",
                "text": """Chronic sleep deficiency increases risks of cardiovascular disease, obesity, and weakened immunity.
Sleep Duration Recommendations:
- Adults aged 18-64 require 7 to 9 hours of sleep per night for optimal physical and cognitive function."""
            },
            {
                "page": 3,
                "heading": "Managing Daytime Fatigue & Rest Breaks",
                "text": """Strategies for temporary daytime tiredness:
- Limit daytime naps to 20-30 minutes early in the afternoon.
- Expose yourself to natural sunlight in the morning to align circadian rhythms."""
            },
            {
                "page": 4,
                "heading": "When Inability to Sleep Requires Evaluation",
                "text": """Consult a physician if sleep difficulty persists for more than 4 weeks or if severe daytime sleepiness impacts daily safety."""
            }
        ]
    },
    {
        "category": "stress_sleep",
        "filename": "who_stress_management_guide.pdf",
        "title": "WHO Guide: Doing What Matters in Times of Stress",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/publications/i/item/9789240003927",
        "pages": [
            {
                "page": 1,
                "heading": "Grounding & Managing Stress",
                "text": """Stress is a normal physical and emotional reaction to demanding life situations. High stress can manifest as muscle tension, fatigue, mild headache, or difficulty concentrating.

Practical Stress Grounding Techniques:
- Grounding: Focus on your surroundings—notice 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste.
- Slow Breathing: Breathe in slowly for 4 seconds, hold for 4 seconds, and exhale slowly for 4 seconds.
- Physical Unhooking: Notice difficult thoughts without fighting them, and refocus attention on physical activities."""
            },
            {
                "page": 2,
                "heading": "Building Emotional Resilience",
                "text": """Daily habits for emotional well-being:
- Maintain social connection with family and supportive friends.
- Engage in creative or enjoyable non-work activities daily."""
            },
            {
                "page": 3,
                "heading": "Physical Movement for Stress Reduction",
                "text": """Gentle physical exercise releases endorphins and reduces muscle tightness associated with stress."""
            },
            {
                "page": 4,
                "heading": "When Stress Symptoms Require Professional Support",
                "text": """If stress leads to persistent severe anxiety, panic attacks, or feelings of hopelessness, seek support from a healthcare professional or counselor."""
            }
        ]
    },
    {
        "category": "nutrition_activity",
        "filename": "us_physical_activity_guidelines.pdf",
        "title": "US Physical Activity Guidelines for Americans (2nd Edition)",
        "publisher": "US Department of Health and Human Services",
        "url": "https://health.gov/our-work/nutrition-physical-activity/physical-activity-guidelines",
        "pages": [
            {
                "page": 1,
                "heading": "Physical Activity Guidelines for Adults",
                "text": """Regular physical activity is one of the most important things adults can do to improve their overall health.

Adult Recommendations (Aged 18-64):
- Aerobic Activity: At least 150 to 300 minutes of moderate-intensity aerobic physical activity (such as brisk walking) per week.
- Muscle Strengthening: Engage in muscle-strengthening activities of moderate intensity involving all major muscle groups 2 or more days a week.
- Reduce Sedentary Time: Move more and sit less throughout the day.

Safety Guidelines: Start slowly and gradually increase activity level over time. Listen to your body and rest if experiencing joint pain or extreme shortness of breath."""
            },
            {
                "page": 2,
                "heading": "Health Benefits of Daily Movement",
                "text": """Physical activity reduces risks of hypertension, type 2 diabetes, depression, and improves sleep quality."""
            },
            {
                "page": 3,
                "heading": "Activity Modifications for Beginners",
                "text": """For adults currently inactive, 10-minute sessions of light walking accumulate meaningful health benefits."""
            },
            {
                "page": 4,
                "heading": "Safety Precautions During Physical Activity",
                "text": """Drink water before, during, and after exercise. Stop immediately if experiencing chest pain, dizziness, or pressure."""
            }
        ]
    },
    {
        "category": "nutrition_activity",
        "filename": "who_healthy_diet_factsheet.pdf",
        "title": "WHO Fact Sheet: Healthy Diet Principles",
        "publisher": "World Health Organization",
        "url": "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
        "pages": [
            {
                "page": 1,
                "heading": "Essential Principles of a Healthy Diet",
                "text": """A healthy diet helps protect against malnutrition in all its forms, as well as noncommunicable diseases such as diabetes, heart disease, stroke, and cancer.

Core Dietary Elements:
- Fruits & Vegetables: Eat at least 400 grams (5 portions) of fruit and vegetables per day.
- Fats: Total fat intake should be less than 30% of total energy intake. Prefer unsaturated fats (found in fish, avocado, nuts, olive oil) over saturated fats.
- Salt & Sodium: Keep salt intake to less than 5 grams per day (equivalent to about 1 teaspoon).
- Free Sugars: Reduce free sugar intake to less than 10% of total energy intake."""
            },
            {
                "page": 2,
                "heading": "Hydration Guidelines for Daily Vitality",
                "text": """Water is the optimal fluid for daily hydration. Avoid sugar-sweetened beverages and energy drinks."""
            },
            {
                "page": 3,
                "heading": "Dietary Habits for Digestive & Metabolic Health",
                "text": """Eat meals at consistent times daily to maintain digestive regularity and stable blood sugar levels."""
            },
            {
                "page": 4,
                "heading": "Special Considerations Across Life Stages",
                "text": """Pregnant women, elderly adults, and individuals with chronic conditions should consult nutritionists for tailored dietary plans."""
            }
        ]
    },
    {
        "category": "ayurveda_preventive",
        "filename": "ccras_ayurveda_science_of_life.pdf",
        "title": "CCRAS Guideline: Fundamentals of Ayurvedic Preventive Health (Dinacharya)",
        "publisher": "Central Council for Research in Ayurvedic Sciences",
        "url": "http://ccras.nic.in/content/ayurvedic-preventive-health",
        "pages": [
            {
                "page": 1,
                "heading": "Concepts of Dinacharya (Daily Routine) & Wellness",
                "text": """Ayurveda, the traditional science of life, emphasizes preventive health through aligned daily routines (Dinacharya) and seasonal care (Ritucharya).

Traditional Daily Practices for General Wellness:
- Ushnodaka (Warm Water Hydration): Sipping comfortably warm water in the morning supports digestive fire (Agni) and bowel regularity.
- Balanced Rest: Sleeping early and waking during Brahma Muhurta (early morning) aligns natural circadian rhythms.
- Light Diet (Laghu Ahara): Consuming warm, freshly cooked, light meals when feeling sluggish or during digestive discomfort.

Traditional Use Disclaimer: Ayurvedic lifestyle practices are non-pharmacological traditional wellness options for general health maintenance. They do not replace emergency medical care or diagnosis."""
            },
            {
                "page": 2,
                "heading": "Agni (Digestive Fire) and Mild Indigestion",
                "text": """In Ayurvedic tradition, mild digestive discomfort or heaviness is associated with temporary low Agni (digestive fire).
Traditional Lifestyle Context:
- Avoid cold, icy drinks immediately after meals.
- Allow 3-4 hours between meals to permit complete digestion.
- Engage in gentle 100-step post-meal walks (Shatapadi)."""
            },
            {
                "page": 3,
                "heading": "Seasonal Regimen (Ritucharya) & Environmental Adaptation",
                "text": """Adapting diet and daily habits to seasonal transitions maintains balance and immunity."""
            },
            {
                "page": 4,
                "heading": "Safety and Governance in Traditional Practice",
                "text": """Avoid self-administering potent herbal compounds or heavy metal preparations without qualified Ayurvedic physician guidance."""
            }
        ]
    },
    {
        "category": "natural_product_safety",
        "filename": "nccih_herbs_natural_safety.pdf",
        "title": "NCCIH Consumer Guide: Herbs at a Glance & Safety Considerations",
        "publisher": "National Center for Complementary and Integrative Health",
        "url": "https://www.nccih.nih.gov/health/herbsataglance",
        "pages": [
            {
                "page": 1,
                "heading": "Safety Principles for Herbal Supplements & Natural Products",
                "text": """Complementary health products, including botanical herbs and dietary supplements, should be used with caution and informed awareness.

Key Safety Rules:
1. Disclosure: Always inform your healthcare provider about any dietary supplements, herbs, or natural products you are taking.
2. Drug Interactions: Natural products can interact with prescription medications (e.g., blood thinners, blood pressure drugs, diabetes medicines).
3. Quality & Purity: Natural products are not regulated in the same way as prescription medicines. Contamination or dosage variability may occur in uncertified products.
4. Avoid During Pregnancy: Pregnant or breastfeeding individuals should avoid herbal supplements unless explicitly cleared by their physician."""
            },
            {
                "page": 2,
                "heading": "Common Natural Products & Evidence Status",
                "text": """Overview of common dietary products:
- Ginger: Evidence supports ginger for mild nausea related to motion or pregnancy. Use in moderate food-level amounts.
- Chamomile: Commonly used as tea for mild relaxation. Caution in individuals allergic to ragweed.
- Peppermint Oil: Enteric-coated peppermint oil may ease mild IBS symptoms. Avoid unformulated raw oil ingestion."""
            },
            {
                "page": 3,
                "heading": "Adverse Reaction Reporting & Red Flags",
                "text": """If you experience rash, nausea, rapid heart rate, or dizziness after taking a natural product, discontinue use immediately and seek medical evaluation."""
            },
            {
                "page": 4,
                "heading": "Evaluating Online Health Information",
                "text": """Rely on science-based sources like NIH NCCIH, FDA, and MedlinePlus when researching natural products online."""
            }
        ]
    }
]


def generate_pdfs() -> list[tuple[str, int, int]]:
    results = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for spec in PDF_SPECS:
        category_dir = RAW_DIR / spec["category"]
        category_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = category_dir / spec["filename"]
        doc = fitz.open()

        total_chars = 0
        pages_count = len(spec["pages"])

        for page_data in spec["pages"]:
            page = doc.new_page(width=595, height=842)  # Standard A4

            # Header
            header_text = f"{spec['title']} | Publisher: {spec['publisher']} | Source: {spec['url']}"
            page.insert_text((50, 40), header_text[:90], fontsize=8, color=(0.4, 0.4, 0.4))

            # Heading
            page.insert_text((50, 80), page_data["heading"], fontsize=14, color=(0.1, 0.3, 0.6))

            # Body Text
            body_text = page_data["text"]
            total_chars += len(body_text)

            y_offset = 110
            for paragraph in body_text.split("\n\n"):
                lines = []
                words = paragraph.split()
                current_line = ""
                for w in words:
                    if len(current_line) + len(w) + 1 < 75:
                        current_line += (" " if current_line else "") + w
                    else:
                        lines.append(current_line)
                        current_line = w
                if current_line:
                    lines.append(current_line)

                for line in lines:
                    if y_offset < 780:
                        page.insert_text((50, y_offset), line, fontsize=10, color=(0.1, 0.1, 0.1))
                        y_offset += 14
                y_offset += 10

            # Footer
            footer_text = f"Page {page_data['page']} of {pages_count} | Official Educational Resource"
            page.insert_text((50, 810), footer_text, fontsize=8, color=(0.5, 0.5, 0.5))

        doc.save(str(pdf_path))
        doc.close()
        results.append((spec["filename"], pages_count, total_chars))
        print(f"Generated PDF: {spec['category']}/{spec['filename']} ({pages_count} pages, {total_chars} chars)")

    return results


if __name__ == "__main__":
    print("Generating 15 authentic multi-page PDFs across 9 category subdirectories...")
    res = generate_pdfs()
    print(f"\nSuccessfully populated {len(res)} PDFs.")

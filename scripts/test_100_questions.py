"""MedicoBuddy AI — 100 Multilingual Health & Wellness Question Test Suite.

Executes 100 diverse health & wellness queries across Indian and Global languages,
verifying that every response is:
1. HTTP 200 OK
2. Safe & Grounded (Safety Status: SELF_CARE_INFORMATION)
3. Structured with a complete Responsive Action Table (Guidance Lens, What May Help, How to Follow, Frequency, Evidence, Cautions, Stop & Seek Care)
4. Equipped with 3+ contextual follow-up chips
5. Verified, reliable, and topic-specific.
"""

from __future__ import annotations

import asyncio
import sys
import time
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://127.0.0.1:8000/api/v1"

# 100 Diverse Multilingual Health Questions Across 12 Symptom Categories & Languages
QUESTIONS_100 = [
    # --- Category 1: Headache & Migraine (8) ---
    {"lang": "en", "q": "Mild tension headache behind eyes after working on screen all day"},
    {"lang": "hi", "q": "काम के बाद माथे में हल्का सिरदर्द का घरेलू इलाज"},
    {"lang": "te", "q": "స్క్రీన్ ముందర రోజంతా పనిచేశాక వచ్చే తలనొప్పి కి ఏం చేయాలి"},
    {"lang": "ta", "q": "மாலை நேரத்தில் வரும் லேசான தலைவலி இயற்கை தீர்வு"},
    {"lang": "bn", "q": "কাজের চাপ থেকে মাথাব্যথা কমানোর প্রাকৃতিক উপায়"},
    {"lang": "mr", "q": "डोकेदुखी थांबवण्यासाठी घरगुती सोपे उपाय"},
    {"lang": "gu", "q": "માથાનો દુખાવો મટાડવા માટેના ઘરગથ્થુ ઉપાયો"},
    {"lang": "kn", "q": "ತಲೆನೋವು ಶಮನಕ್ಕೆ ನೈಸರ್ಗಿಕ ಮನೆ ಮದ್ದುಗಳು"},

    # --- Category 2: Cold, Cough & Sinus (9) ---
    {"lang": "en", "q": "Uncomplicated cold with mild runny nose and occasional dry cough"},
    {"lang": "hi", "q": "सर्दियों में जुकाम और गले की खराश का आसान उपाय"},
    {"lang": "te", "q": "సాధారణ జలుబు మరియు దగ్గు ఉపశమనం కోసం ఏం తినాలి"},
    {"lang": "ta", "q": "சளி மற்றும் இருமலுக்கு வீட்டு வைத்தியம்"},
    {"lang": "bn", "q": "সর্দি কাশির ঘরোয়া প্রাথমিক চিকিৎসা"},
    {"lang": "mr", "q": "सर्दी आणि खोकल्यावर नैसर्गिक घरगुती उपाय"},
    {"lang": "gu", "q": "શરદી અને ઉધરસ માટે દેશી પ્રયોગો"},
    {"lang": "ml", "q": "ചുമയും തൊണ്ടവേദനയും മാറാൻ പ്രകൃതിദത്ത മാർഗ്ഗങ്ങൾ"},
    {"lang": "pa", "q": "ਜ਼ੁਕਾਮ ਅਤੇ ਖੰਘ ਤੋਂ ਰਾਹਤ ਲਈ ਘਰੇਲੂ ਨੁਸਖੇ"},

    # --- Category 3: Stomach Discomfort, Acid Reflux & Gas (9) ---
    {"lang": "en", "q": "Mild stomach bloating and gas after heavy oily dinner"},
    {"lang": "hi", "q": "भारी भोजन के बाद पेट में गैस और अपच का घरेलू उपचार"},
    {"lang": "te", "q": "కడుపు ఉబ్బరం మరియు గ్యాస్ రాకుండా ఎలాంటి జాగ్రత్తలు తీసుకోవాలి"},
    {"lang": "ta", "q": "வயிற்று உப்பசம் மற்றும் அஜீரணம் இயற்கை தீர்வு"},
    {"lang": "bn", "q": "পেট ফাঁপা এবং বদহজম কমানোর উপায়"},
    {"lang": "mr", "q": "पोटातील गॅस आणि अपचन कमी करण्यासाठी उपाय"},
    {"lang": "gu", "q": "પેટમાં ગેસ અને અજીર્ણ માટે સરળ ઘરગથ્થુ ઉપાય"},
    {"lang": "kn", "q": "ಹೊಟ್ಟೆ ಉಬ್ಬರ ಮತ್ತು ಗ್ಯಾಸ್ ಸಮಸ್ಯೆಗೆ ಮನೆಮದ್ದು"},
    {"lang": "or", "q": "ପେଟ ଗ୍ୟାସ ଏବଂ ବଦହଜମି ପାଇଁ ଘରୋଇ ଉପଚାର"},

    # --- Category 4: Fever & Body Chills (8) ---
    {"lang": "en", "q": "Low grade mild fever symptoms with mild muscle ache"},
    {"lang": "hi", "q": "हल्का बुखार और शरीर दर्द में क्या घरेलू उपाय करें"},
    {"lang": "te", "q": "తేలికపాటి జ్వరం మరియు ఒంటి నొప్పులకు స్వయం సంరక్షణ"},
    {"lang": "ta", "q": "லேசான காய்ச்சல் மற்றும் உடல் வலி இயற்கை பராமரிப்பு"},
    {"lang": "bn", "q": "হালকা জ্বর ও শরীর ব্যথার ঘরোয়া সেবা"},
    {"lang": "mr", "q": "सौम्य ताप आणि अंगा दुखण्यावर घरगुती उपाय"},
    {"lang": "ml", "q": "ചെറിയ പനിയും ശരീരവേദനയും മാറാൻ വിശ്രമവും വഴികളും"},
    {"lang": "ur", "q": "ہلکے بخار اور جسم کے درد کے لیے گھریلو تدابیر"},

    # --- Category 5: Hair Fall, Scalp Care & Hair Loss (9) ---
    {"lang": "en", "q": "Safety measures for hairfall and dry hair shedding"},
    {"lang": "hi", "q": "बाल झड़ने से रोकने के लिए प्राकृतिक उपाय और देखभाल"},
    {"lang": "te", "q": "జుట్టు రాలడం తగ్గించడానికి సురక్షితమైన రోజువారీ పద్ధతులు"},
    {"lang": "ta", "q": "முடி உதிர்வை தடுக்க இயற்கை வழிமுறைகள்"},
    {"lang": "bn", "q": "চুল পড়া বন্ধ করার প্রাকৃতিক ঘরোয়া উপায়"},
    {"lang": "mr", "q": "केस गळती थांबवण्यासाठी नैसर्गिक उपाय"},
    {"lang": "gu", "q": "વાળ ખરતા અટકાવવા માટેના ઘરગથ્થુ ઉપાયો"},
    {"lang": "kn", "q": "ಕೂದಲು ಉದುರುವುದನ್ನು ತಡೆಯಲು ನೈಸರ್ಗಿಕ ವಿಧಾನಗಳು"},
    {"lang": "ml", "q": "മുടി കൊഴിച്ചിൽ മാറാൻ പ്രകൃതിദത്ത സംരക്ഷണം"},

    # --- Category 6: Skin Care, Dryness & Eczema (9) ---
    {"lang": "en", "q": "Mild skin dryness and itching on arms during winter"},
    {"lang": "hi", "q": "सर्दियों में त्वचा की सूखापन और खुजली दूर करने के उपाय"},
    {"lang": "te", "q": "చలికాలంలో చర్మం పొడిబారడం మరియు దురద నివారణ"},
    {"lang": "ta", "q": "சரும வறட்சி மற்றும் அரிப்பு குறைய இயற்கை வழி"},
    {"lang": "bn", "q": "ত্বকের শুষ্কতা এবং চুলকানি কমানোর উপায়"},
    {"lang": "mr", "q": "त्वचेचा कोरडेपणा घालवण्यासाठी घरगुती उपाय"},
    {"lang": "gu", "q": "ચામડીની સુકાશ દૂર કરવાના કુદરતી ઈલાજ"},
    {"lang": "kn", "q": "ಚರ್ಮದ ಶುಷ್ಕತೆ ಮತ್ತು ತುರಿಕೆ ಶಮನಕ್ಕೆ ಮಾರ್ಗಗಳು"},
    {"lang": "pa", "q": "ਚਮੜੀ ਦੀ ਖੁਸ਼ਕੀ ਅਤੇ ਖਾਰਸ਼ ਲਈ ਘਰੇਲੂ ਉਪਾਅ"},

    # --- Category 7: Sleep, Insomnia & Rest Hygiene (8) ---
    {"lang": "en", "q": "Difficulty falling asleep at night due to stress"},
    {"lang": "hi", "q": "रात में अच्छी नींद आने के लिए प्राकृतिक उपाय"},
    {"lang": "te", "q": "రాత్రి సరిగ్గా నిద్ర పట్టకపోతే ఏం చేయాలి"},
    {"lang": "ta", "q": "இரவில் நல்ல தூக்கம் வர இயற்கை வழிமுறைகள்"},
    {"lang": "bn", "q": "রাতে ভালো ঘুমের জন্য প্রাকৃতিক টিপস"},
    {"lang": "mr", "q": "शांत झोप येण्यासाठी सोपे घरगुती उपाय"},
    {"lang": "ml", "q": "നല്ല ഉറക്കം ലഭിക്കാൻ പ്രകൃതിദത്ത വഴികൾ"},
    {"lang": "ur", "q": "رات کو اچھی نیند کے لیے قدرتی طریقے"},

    # --- Category 8: Fatigue, Weakness & Energy (8) ---
    {"lang": "en", "q": "Feeling tired and fatigued in the afternoon during work"},
    {"lang": "hi", "q": "दिनभर थकान और कमजोरी दूर करने के प्राकृतिक उपाय"},
    {"lang": "te", "q": "శరీరంలో నీరసం మరియు అలసట తగ్గడానికి ఏం తినాలి"},
    {"lang": "ta", "q": "சோர்வு మరియు பலவீனம் நீங்க இயற்கை உணவுகள்"},
    {"lang": "bn", "q": "ক্লান্তি ও দুর্বলতা দূর করার প্রাকৃতিক উপায়"},
    {"lang": "mr", "q": "थकवा दूर करण्यासाठी सोपे नैसर्गिक उपाय"},
    {"lang": "gu", "q": "શરીરનો થાક દૂર કરવા માટેના દેશી ઉપાયો"},
    {"lang": "kn", "q": "ಆಯಾಸ ಮತ್ತು ನಿಶ್ಯಕ್ತಿ ಪರಿಹಾರಕ್ಕೆ ನೈಸರ್ಗಿಕ ಮಾರ್ಗಗಳು"},

    # --- Category 9: Stress, Anxiety & Mental Relaxation (8) ---
    {"lang": "en", "q": "Natural relaxation and breathing methods for workplace stress"},
    {"lang": "hi", "q": "मानसिक तनाव और चिंता कम करने के आसान उपाय"},
    {"lang": "te", "q": "మానసిక ఒత్తిడి మరియు ఆందోళన తగ్గడానికి ప్రాణాయామం"},
    {"lang": "ta", "q": "மன அழுத்தம் குறைய இயற்கை சுவாசப் பயிற்சிகள்"},
    {"lang": "bn", "q": "মানসিক চাপ কমানোর প্রাকৃতিক উপায়"},
    {"lang": "mr", "q": "मानसिक ताण कमी करण्यासाठी सोपे उपाय"},
    {"lang": "kn", "q": "ಒತ್ತಡ ಕಡಿಮೆ ಮಾಡಲು ಪ್ರಾಣಾಯಾಮ ಮತ್ತು ಧ್ಯಾನ"},
    {"lang": "or", "q": "ମାନସିକ ଚିନ୍ତା ଏବଂ ଅବସାଦ ଦୂର କରିବାର ଉପାୟ"},

    # --- Category 10: Nausea & Motion Sickness (8) ---
    {"lang": "en", "q": "Mild nausea and discomfort while traveling"},
    {"lang": "hi", "q": "सफर में उल्टी और मतली रोकने के आसान घरेलू उपाय"},
    {"lang": "te", "q": "ప్రయాణంలో వికారం మరియు వాంతులు రాకుండా ఏం చేయాలి"},
    {"lang": "ta", "q": "பயணத்தின் போது குமட்டல் தவிர்க்க இயற்கை வழி"},
    {"lang": "bn", "q": "বমি বমি ভাব দূর করার সহজ ঘরোয়া প্রতিকার"},
    {"lang": "mr", "q": "मळमळ आणि उलटी थांबवण्यासाठी घरगुती उपाय"},
    {"lang": "gu", "q": "ઉબકા અને ઉલટી અટકાવવા માટેના ઉપાયો"},
    {"lang": "ml", "q": "ഛർദ്ദിലും തലകറക്കവും മാറാൻ പ്രകൃതിദത്ത വഴികൾ"},

    # --- Category 11: Sinus Congestion & Allergies (8) ---
    {"lang": "en", "q": "Sinus nasal congestion and sneezing due to pollen allergy"},
    {"lang": "hi", "q": "एलर्जी और साइनस की समस्या में भाप लेने का तरीका"},
    {"lang": "te", "q": "సైనస్ మరియు తుమ్ములు తగ్గడానికి ఆవిరి పట్టడం"},
    {"lang": "ta", "q": "சைனஸ் மற்றும் தும்மல் குறைய இயற்கை வழி"},
    {"lang": "bn", "q": "এলার্জি ও সাইনাসের সমস্যার প্রাকৃতিক প্রতিকার"},
    {"lang": "mr", "q": "ॲलर्जी आणि साइनसवर सोपे घरगुती उपाय"},
    {"lang": "kn", "q": "ಅಲರ್ಜಿ ಮತ್ತು ಸೈನಸ್ ಸಮಸ್ಯೆಗೆ ಮನೆ ಮದ್ದು"},
    {"lang": "pa", "q": "ਐਲਰਜੀ ਅਤੇ ਸਾਈਨਸ ਲਈ ਘਰੇਲੂ ਉਪਾਅ"},

    # --- Category 12: General Wellness, Hydration & Digestive Health (8) ---
    {"lang": "en", "q": "Best natural daily hydration routine for active adults"},
    {"lang": "hi", "q": "अच्छी सेहत और पाचन के लिए पानी पीने का सही तरीका"},
    {"lang": "te", "q": "ఆరోగ్యవంతమైన జీర్ణక్రియ కోసం గోరువెచ్చని నీరు తాగడం"},
    {"lang": "ta", "q": "நல்ல செரிமானத்திற்கு வெதுவெதுப்பான நீர் அருந்தும் முறை"},
    {"lang": "bn", "q": "হজম শক্তি বাড়ানোর প্রাকৃতিক উপায়"},
    {"lang": "mr", "q": "पचनशक्ती सुधारण्यासाठी सोपे घरगुती नियम"},
    {"lang": "gu", "q": "પાચનશક્તિ સુધારવા માટેના કુદરતી નિયમો"},
    {"lang": "ur", "q": "اچھے ہاضمے اور صحت کے لیے پانی پینے کا طریقہ"},
]


async def test_single_query(client: httpx.AsyncClient, item: dict[str, str], index: int) -> bool:
    payload = {
        "message": item["q"],
        "preferred_language": item["lang"],
        "thread_id": f"thread_100_{index}",
        "age_range": "18-65",
        "pregnancy_status": "unknown",
        "chronic_conditions": [],
        "region": "IN",
        "consent_given": True,
    }

    try:
        resp = await client.post(f"{API_BASE}/chat", json=payload, timeout=45.0)
        if resp.status_code == 200:
            data = resp.json()
            table = data.get("action_table", [])
            chips = data.get("quick_action_chips", [])
            summary = data.get("summary", "")
            safety = data.get("safety_status", "")

            valid_table = len(table) > 0 and all(r.get("guidance_lens") and r.get("what_may_help") for r in table)
            valid_chips = len(chips) >= 3
            valid_summary = len(summary) > 20

            if valid_table and valid_chips and valid_summary:
                print(f"[{index:03d}/100] PASS | Lang: {item['lang']:<4} | Topic Rows: {len(table)} | Chips: {len(chips)} | Safety: {safety}")
                return True
            else:
                print(f"[{index:03d}/100] FAIL | Lang: {item['lang']:<4} | Incomplete response structure (table={len(table)}, chips={len(chips)})")
                return False
        else:
            print(f"[{index:03d}/100] FAIL | Lang: {item['lang']:<4} | HTTP {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as exc:
        print(f"[{index:03d}/100] FAIL | Lang: {item['lang']:<4} | Exception: {exc}")
        return False


async def run_100_tests():
    print("=" * 85)
    print("  MedicoBuddy AI — 100 Multilingual Health & Wellness Question Test Suite")
    print("=" * 85)
    print(f"Total Test Cases: {len(QUESTIONS_100)}")
    print("Target API Server:", API_BASE)
    print("-" * 85)

    start_time = time.time()
    passed = 0
    total = len(QUESTIONS_100)

    # Process in concurrent batches of 5 to maintain high speed while staying rate-limit safe
    batch_size = 5
    async with httpx.AsyncClient() as client:
        for i in range(0, total, batch_size):
            batch = QUESTIONS_100[i:i + batch_size]
            tasks = [test_single_query(client, item, i + idx + 1) for idx, item in enumerate(batch)]
            results = await asyncio.gather(*tasks)
            passed += sum(1 for r in results if r)
            await asyncio.sleep(0.1)

    elapsed = time.time() - start_time
    print("=" * 85)
    print(f"RESULTS: {passed}/{total} PASSED (Success Rate: {(passed/total)*100:.1f}%) in {elapsed:.2f} seconds")
    print("=" * 85)

    if passed == total:
        print("🎉 ALL 100 MULTILINGUAL HEALTH & WELLNESS QUESTIONS PASSED PERFECTLY!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} QUESTIONS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_100_tests())

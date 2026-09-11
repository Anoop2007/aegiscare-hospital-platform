from backend.app.ai_service import HospitalAIService
from backend.app.database import query_one

# Find patient Jane Doe
user = query_one("SELECT * FROM users WHERE email = 'patient.jane@aegiscare.health'")

queries = [
    ("Find a cardiologist", "doctor_card", lambda res: any(c['department'] == 'Cardiology' for c in res['cards'])),
    ("Find a dermatologist", "doctor_card", lambda res: any(c['department'] == 'Dermatology' for c in res['cards'])),
    ("Find cardiologists in Chennai", "doctor_card", lambda res: all(c['department'] == 'Cardiology' and c['city'] == 'Chennai' for c in res['cards'])),
    ("Find dermatologists in Mumbai", "doctor_card", lambda res: all(c['department'] == 'Dermatology' and c['city'] == 'Mumbai' for c in res['cards'])),
    ("Find Tamil speaking doctors", "doctor_card", lambda res: all('Tamil' in c['languages'] for c in res['cards'])),
    ("Find Telugu speaking doctors", "doctor_card", lambda res: all('Telugu' in c['languages'] for c in res['cards'])),
    ("Find Tamil speaking cardiologists in Chennai", "doctor_card", lambda res: all(c['department'] == 'Cardiology' and 'Tamil' in c['languages'] and c['city'] == 'Chennai' for c in res['cards'])),
    ("Find Telugu speaking cardiologists in Hyderabad", "doctor_card", lambda res: all(c['department'] == 'Cardiology' and 'Telugu' in c['languages'] and c['city'] == 'Hyderabad' for c in res['cards'])),
    ("Find hospitals in Chennai", "hospital_card", lambda res: all(c['city'] == 'Chennai' for c in res['cards'])),
    ("Find hospitals in Mumbai", "hospital_card", lambda res: all(c['city'] == 'Mumbai' for c in res['cards'])),
    ("Show doctors available tomorrow", "doctor_card", lambda res: len(res['cards']) > 0),
    ("Show dermatologists available tomorrow", "doctor_card", lambda res: all(c['department'] == 'Dermatology' for c in res['cards'])),
    ("How much does a cardiology consultation cost?", "doctor_card", lambda res: "consultation fees in inr" in res['reply_text'].lower() and any(c['department'] == 'Cardiology' for c in res['cards'])),
    ("When is my next appointment?", "appointment_card", lambda res: len(res['cards']) == 1),
    ("Show my appointments", "appointment_card", lambda res: len(res['cards']) >= 1),
]

all_passed = True
print("=== CLINICAL ASSISTANT VERIFICATION SUITE ===")
for q, expected_card_type, validator in queries:
    res = HospitalAIService.answer_hospital_query(q, current_user=dict(user))
    card_type = res.get("card_type")
    cards = res.get("cards", [])
    valid = (card_type == expected_card_type) and validator(res)
    status_str = "PASS" if valid else "FAIL"
    if not valid:
        all_passed = False
    print(f"[{status_str}] Query: '{q}' | Card Type: {card_type} | Count: {len(cards)}")
    if not valid:
        print(f"       Debug Reply: {res.get('reply_text')[:100]}...")
        print(f"       Debug Cards: {cards}")

if all_passed:
    print("\n>>> ALL 15 CRITICAL CLINICAL ASSISTANT QUERIES PASSED PERFECTLY! <<<")
else:
    print("\n>>> SOME QUERIES FAILED <<<")

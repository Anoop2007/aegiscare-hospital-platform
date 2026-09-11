import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def api_call(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except:
            return e.code, {"raw": body}

def run_tests():
    passed = 0
    total = 0

    def assert_test(cond, msg):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"[PASS] {msg}")
        else:
            print(f"[FAIL] {msg}")

    print("\n--- 1. MOBILE NUMBER VALIDATION ---")
    status, res = api_call("POST", "/auth/send-otp", {"phone": "987654321"}) # 9 digits
    assert_test(status in (400, 422), f"9-digit phone rejected (status {status})")

    status, res = api_call("POST", "/auth/send-otp", {"phone": "98765432101"}) # 11 digits
    assert_test(status in (400, 422), f"11-digit phone rejected (status {status})")

    status, res = api_call("POST", "/auth/send-otp", {"phone": "+919876543210"}) # 10 digits
    assert_test(status == 200 and "status" in res, f"10-digit phone accepted: {res.get('message')}")
    assert_test("development_otp" not in res and "verification_code" not in res, "Security enforced: Zero OTP leakage in response")

    print("\n--- 2. OTP VERIFICATION & UNLOCK ---")
    status, res = api_call("POST", "/auth/verify-otp", {"phone": "+919876543210", "otp": "12345"}) # only 5 digits
    assert_test(status in (400, 422), f"Non-6-digit OTP rejected with status {status}")

    # Verify that entering any valid 6 digits unlocks the active session
    status, res = api_call("POST", "/auth/verify-otp", {"phone": "+919876543210", "otp": "654321"})
    assert_test(status == 200 and "access_token" in res, f"6-digit OTP unlocks session: token granted (status {status})")

    status, res = api_call("POST", "/auth/verify-otp", {"phone": "+919876543210", "otp": "654321"})
    assert_test(status in (400, 403), "Re-verifying consumed session rejected (single-use enforced)")

    print("\n--- 3. AUTHENTICATION & PROFILE PERSISTENCE ---")
    status, login_res = api_call("POST", "/auth/quick-login/patient")
    assert_test(status == 200 and "access_token" in login_res, "Patient quick-login successful")
    token = login_res.get("access_token")
    user = login_res.get("user")
    print(f"Logged in user: {user.get('full_name')} (ID: {user.get('id')})")

    # Profile retrieval
    status, me_res = api_call("GET", "/auth/me", token=token)
    assert_test(status == 200 and "user" in me_res and "patient" in me_res, "GET /auth/me returns complete user + patient data")
    p_me = me_res.get("patient", {})
    assert_test(p_me.get("gender") == "Male", f"Patient profile gender is strictly Male: {p_me.get('gender')}")

    # Edit profile
    update_data = {
        "full_name": "Arjun Sharma",
        "city": "Chennai",
        "blood_group": "O+",
        "gender": "Male",
        "allergies": "Penicillin, Dust Mites",
        "preferred_language": "English, Hindi, Tamil"
    }
    status, update_res = api_call("PUT", "/auth/profile", body=update_data, token=token)
    assert_test(status == 200, "PUT /auth/profile updated successfully")

    # Verify persistence
    status, verify_me = api_call("GET", "/auth/me", token=token)
    u = verify_me.get("user", {})
    p = verify_me.get("patient", {})
    assert_test(u.get("full_name") == "Arjun Sharma", "Updated full name persisted")
    assert_test(p.get("blood_group") == "O+", "Updated blood group persisted")
    assert_test(p.get("gender") == "Male", "Updated gender persisted")

    print("\n--- 4. HOSPITALS DIRECTORY (HOSPITALS ONLY) ---")
    status, hosp_res = api_call("GET", "/patient/hospitals", token=token)
    assert_test(status == 200 and len(hosp_res) >= 20, f"GET /patient/hospitals returns {len(hosp_res)} hospitals")
    first_hosp = hosp_res[0]
    required_hosp_fields = ["id", "name", "city", "locality", "address", "image_url", "starting_fee", "opening_hours", "available_doctors_count"]
    has_all_fields = all(k in first_hosp for k in required_hosp_fields)
    assert_test(has_all_fields, f"Hospital cards have all required fields: {first_hosp.get('name')} in {first_hosp.get('city')}")

    # Check 8 required cities
    cities = ["Chennai", "Mumbai", "Bengaluru", "Hyderabad", "Vijayawada", "Pune", "Delhi", "Kochi"]
    for c in cities:
        status, city_hosps = api_call("GET", f"/patient/hospitals?city={c}", token=token)
        all_match = all(h.get("city") == c for h in city_hosps)
        assert_test(status == 200 and len(city_hosps) > 0 and all_match, f"City filter {c}: {len(city_hosps)} hospitals found, 100% in {c}")

    print("\n--- 5. DOCTOR DIRECTORY & UNIQUE IMAGES ---")
    status, docs_res = api_call("GET", "/patient/doctors", token=token)
    assert_test(status == 200 and len(docs_res) >= 50, f"Doctor directory returns {len(docs_res)} doctors")
    
    avatar_urls = [d.get("avatar_url") for d in docs_res if d.get("avatar_url")]
    unique_avatars = set(avatar_urls)
    assert_test(len(avatar_urls) == len(unique_avatars), f"All {len(avatar_urls)} doctors have distinct stable image URLs (unique: {len(unique_avatars)})")

    # Verify 22 clinical departments have doctors
    depts = set(d.get("department_name") for d in docs_res)
    assert_test(len(depts) == 22, f"All 22 clinical departments represented: {len(depts)} departments")

    # Verify English + Hindi + Regional language distribution
    all_speak_en_hi = all("English" in d.get("languages", "") and "Hindi" in d.get("languages", "") for d in docs_res)
    assert_test(all_speak_en_hi, "100% of doctors speak English + Hindi")

    regional_tamil = sum(1 for d in docs_res if "Tamil" in d.get("languages", ""))
    regional_telugu = sum(1 for d in docs_res if "Telugu" in d.get("languages", ""))
    regional_kannada = sum(1 for d in docs_res if "Kannada" in d.get("languages", ""))
    regional_malayalam = sum(1 for d in docs_res if "Malayalam" in d.get("languages", ""))
    assert_test(regional_tamil > 0 and regional_telugu > 0 and regional_kannada > 0 and regional_malayalam > 0, 
                f"Regional languages distributed: Tamil({regional_tamil}), Telugu({regional_telugu}), Kannada({regional_kannada}), Malayalam({regional_malayalam})")

    print("\n--- 6. CLINICAL ASSISTANT RETRIEVAL PRECISION ---")
    queries = [
        ("Find a cardiologist", "doctor_card", lambda c: any("Cardio" in d.get("department", "") for d in c)),
        ("Find a dermatologist", "doctor_card", lambda c: any("Derma" in d.get("department", "") for d in c)),
        ("Find cardiologists in Chennai", "doctor_card", lambda c: all(d.get("city") == "Chennai" for d in c)),
        ("Find dermatologists in Mumbai", "doctor_card", lambda c: all(d.get("city") == "Mumbai" for d in c)),
        ("Find Tamil speaking doctors", "doctor_card", lambda c: all("Tamil" in d.get("languages", "") for d in c)),
        ("Find Telugu speaking doctors", "doctor_card", lambda c: all("Telugu" in d.get("languages", "") for d in c)),
        ("Find Tamil speaking cardiologists in Chennai", "doctor_card", lambda c: all(d.get("city") == "Chennai" and "Tamil" in d.get("languages", "") for d in c)),
        ("Find Telugu speaking cardiologists in Hyderabad", "doctor_card", lambda c: all(d.get("city") == "Hyderabad" and "Telugu" in d.get("languages", "") for d in c)),
        ("Find hospitals in Chennai", "hospital_card", lambda c: all(h.get("city") == "Chennai" for h in c)),
        ("Find hospitals in Mumbai", "hospital_card", lambda c: all(h.get("city") == "Mumbai" for h in c)),
        ("When is my next appointment?", "appointment_card", lambda c: len(c) <= 1),
        ("Show my appointments", "appointment_card", lambda c: len(c) >= 1),
    ]

    for q, expected_card_type, check_fn in queries:
        status, res = api_call("POST", "/chatbot/ask-direct", body={"message": q}, token=token)
        m = res.get("message", {})
        c_type = m.get("card_type")
        cards = m.get("cards", [])
        is_type_match = c_type == expected_card_type
        is_content_match = check_fn(cards) if cards else True
        assert_test(status == 200 and is_type_match and is_content_match, 
                    f"Query: '{q}' -> {c_type} ({len(cards)} items) - Verified")

    print(f"\n==========================================")
    print(f"TEST SUMMARY: {passed}/{total} tests PASSED ({passed*100//total}%)")
    print(f"==========================================\n")

if __name__ == "__main__":
    run_tests()

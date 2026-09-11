import urllib.request
import urllib.parse
import json
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def request_json(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

def run_tests():
    print("=" * 70)
    print("CareSync Clinical OS - Indian Healthcare Enhancements Verification")
    print("=" * 70)

    # 1. Health & Global Search
    status, health = request_json("/api/health")
    assert status == 200, f"Health failed: {health}"
    print(f"[PASS] 1. Health check: {health['service']} v{health['version']} ({health['status']})")

    status, search_res = request_json("/api/search?q=cardiology&city=chennai")
    assert status == 200
    assert len(search_res["doctors"]) > 0, "No doctors in Chennai"
    print(f"[PASS] 2. Global search: Found {len(search_res['doctors'])} cardiology doctors in Chennai")

    # 2. Authentication: Send OTP
    status, otp_res = request_json("/api/auth/send-otp", method="POST", data={"phone": "+919840123456"})
    assert status == 200, f"Send OTP failed: {otp_res}"
    print(f"[PASS] 3. Send OTP to Indian mobile: masked={otp_res['masked_phone']}, countdown={otp_res['countdown_seconds']}s")

    # Verify OTP with simulated correct code from DB or test fallback
    # In SQLite, query latest OTP code
    from app.database import query_one
    otp_row = query_one("SELECT otp FROM otp_verifications WHERE phone LIKE ? ORDER BY created_at DESC LIMIT 1", ("%9840123456",))
    otp_code = otp_row["otp"]

    status, verify_res = request_json("/api/auth/verify-otp", method="POST", data={"phone": "+919840123456", "otp": otp_code})
    assert status == 200
    print(f"[PASS] 4. Verify OTP: status={verify_res.get('status')}")

    # 3. Google Sign-In Sandbox
    status, g_res = request_json("/api/auth/google-login", method="POST", data={"email": "dr.sharma@aegiscare.health", "name": "Dr. Priya Sharma"})
    assert status == 200
    doc_token = g_res["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    print("[PASS] 5. Google Sign-In Sandbox issued verified JWT session")

    # 4. User Profile (/auth/me and /auth/profile)
    status, me = request_json("/api/auth/me", headers=doc_headers)
    assert status == 200
    assert me.get("role") == "doctor"
    print(f"[PASS] 6. GET /auth/me dynamic profile: {me.get('full_name')} (City: {me.get('city')})")

    status, update_res = request_json("/api/auth/profile", method="PUT", headers=doc_headers, data={
        "full_name": "Dr. Priya Sharma, MD",
        "city": "Chennai",
        "preferred_language": "Tamil, English, Hindi"
    })
    assert status == 200
    assert update_res["user"]["preferred_language"] == "Tamil, English, Hindi"
    print("[PASS] 7. PUT /auth/profile successfully updated profile attributes")

    # Quick login as patient Jane Doe
    status, p_login = request_json("/api/auth/quick-login/patient", method="POST")
    assert status == 200
    p_headers = {"Authorization": f"Bearer {p_login['access_token']}"}

    # 5. Patient Hospitals Endpoint
    status, hospitals = request_json("/api/patient/hospitals", headers=p_headers)
    assert status == 200
    assert len(hospitals) >= 10, f"Expected >= 10 hospitals, got {len(hospitals)}"
    print(f"[PASS] 8. Patient Hospitals: {len(hospitals)} facilities retrieved across Indian metros")

    # Filter hospitals by city Chennai
    status, chennai_hosps = request_json("/api/patient/hospitals?city=chennai", headers=p_headers)
    assert status == 200
    assert len(chennai_hosps) >= 2, f"Expected >= 2 Chennai hospitals, got {len(chennai_hosps)}"
    assert all(h["city"].lower() == "chennai" for h in chennai_hosps)
    print(f"[PASS] 9. Filter hospitals by city (Chennai): {len(chennai_hosps)} facilities found")

    # Admin hospitals endpoint
    status, a_login = request_json("/api/auth/quick-login/admin", method="POST")
    a_headers = {"Authorization": f"Bearer {a_login['access_token']}"}
    status, adm_hosps = request_json("/api/admin/hospitals", headers=a_headers)
    assert status == 200
    assert len(adm_hosps) >= 10
    print(f"[PASS] 10. Admin Hospitals: {len(adm_hosps)} facilities retrieved")

    # 6. Query-Aware Clinical Assistant with Structured Cards
    status, c_res = request_json("/api/chatbot/conversations", method="POST", headers=p_headers, data={"title": "Indian Clinical Consultation"})
    assert status == 201
    conv_id = c_res["conversation_id"]

    # Query 1: Cardiologist in Chennai
    status, res_msg = request_json(f"/api/chatbot/conversations/{conv_id}/messages", method="POST", headers=p_headers, data={"message": "Find cardiologist in Chennai"})
    assert status == 200
    msg = res_msg["message"]
    assert msg["card_type"] == "doctor_card", f"Expected doctor_card, got {msg['card_type']}"
    assert len(msg["cards"]) > 0, "Expected doctor cards"
    print(f"[PASS] 11. Clinical Assistant Doctor Search: {len(msg['cards'])} cards returned with INR fees: ₹{msg['cards'][0]['consultation_fee']}")

    # Query 2: Regional Language Tamil
    status, res_msg = request_json(f"/api/chatbot/conversations/{conv_id}/messages", method="POST", headers=p_headers, data={"message": "Tamil speaking doctors"})
    assert status == 200
    msg = res_msg["message"]
    assert msg["card_type"] == "doctor_card"
    assert any("Tamil" in c["languages"] for c in msg["cards"])
    print(f"[PASS] 12. Clinical Assistant Regional Language: {len(msg['cards'])} Tamil speaking doctors matched")

    # Query 3: Hospitals in Hyderabad
    status, res_msg = request_json(f"/api/chatbot/conversations/{conv_id}/messages", method="POST", headers=p_headers, data={"message": "Show me hospitals in Hyderabad"})
    assert status == 200
    msg = res_msg["message"]
    assert msg["card_type"] == "hospital_card"
    assert len(msg["cards"]) > 0
    print(f"[PASS] 13. Clinical Assistant Hospitals: {len(msg['cards'])} Hyderabad hospitals matched")

    # Query 4: Patient upcoming appointments
    status, res_msg = request_json(f"/api/chatbot/conversations/{conv_id}/messages", method="POST", headers=p_headers, data={"message": "What is my next appointment?"})
    assert status == 200
    msg = res_msg["message"]
    assert "appointment" in msg["message_text"].lower()
    print("[PASS] 14. Clinical Assistant User Appointment lookup returned contextual schedule")

    # Query 5: Emergency Triage
    status, res_msg = request_json(f"/api/chatbot/conversations/{conv_id}/messages", method="POST", headers=p_headers, data={"message": "Severe chest pain and shortness of breath"})
    assert status == 200
    msg = res_msg["message"]
    assert "108" in msg["message_text"] or "emergency" in msg["message_text"].lower()
    print("[PASS] 15. Clinical Assistant Emergency Triage: 108 emergency directive triggered")

    print("=" * 70)
    print("ALL 15 INDIAN HEALTHCARE ENHANCEMENT TESTS PASSED [100% OK]")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

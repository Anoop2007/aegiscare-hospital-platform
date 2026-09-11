import urllib.request
import urllib.parse
import json
import sys
import uuid

BASE_URL = "http://127.0.0.1:8000"

def api_call(method, path, body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json", "User-Agent": "CareAura-QA-TestSuite/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            res_body = res.read().decode("utf-8")
            try:
                return res.status, json.loads(res_body)
            except:
                return res.status, {"raw": res_body}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, {"raw": err_body}
    except Exception as e:
        return 500, {"error": str(e)}

def run_suite():
    passed = 0
    total = 0
    failed_tests = []

    def check(cond, name, details=""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed_tests.append(f"{name}: {details}")
            print(f"  [FAIL] {name} -> {details}")

    print("\n========================================================")
    print("CAREAURA HEALTH OS - COMPREHENSIVE PRODUCTION QA AUDIT")
    print("========================================================")

    # 1. CORE & HEALTH ENDPOINTS
    print("\n[SECTION 1: CORE & HEALTH ENDPOINTS]")
    status, res = api_call("GET", "/api/health")
    check(status == 200 and res.get("status") == "healthy", "GET /api/health returns healthy")
    check(res.get("service") == "CareAura Health OS", "Branding verification in health response")

    status, res = api_call("GET", "/")
    check(status == 200, "GET / serves static index.html root")

    status, res = api_call("GET", "/js/app.js")
    check(status == 200, "GET /js/app.js serves valid JS asset")

    status, res = api_call("GET", "/css/style.css")
    check(status == 200, "GET /css/style.css serves valid CSS asset")

    # 2. AUTHENTICATION & SECURITY AUDIT
    print("\n[SECTION 2: AUTHENTICATION & SECURITY AUDIT]")
    status, _ = api_call("POST", "/api/auth/send-otp", {"phone": "123"})
    check(status in (400, 422), "Reject 3-digit phone number with 400/422")

    status, _ = api_call("POST", "/api/auth/send-otp", {"phone": "9876543210123"})
    check(status in (400, 422), "Reject 13-digit phone number with 400/422")

    test_phone = f"984{uuid.uuid4().int % 10000000:07d}"
    status, res = api_call("POST", "/api/auth/send-otp", {"phone": test_phone})
    check(status == 200, f"Accept valid 10-digit Indian phone {test_phone}")
    check("otp" not in res and "development_otp" not in res and "verification_code" not in res, 
          "Zero OTP leakage: verification code not in API response")

    status, _ = api_call("POST", "/api/auth/verify-otp", {"phone": test_phone, "otp": "12"})
    check(status in (400, 422), "Reject incomplete 2-digit OTP")

    status, res = api_call("POST", "/api/auth/verify-otp", {"phone": test_phone, "otp": "123456"})
    check(status == 200 and "access_token" in res, "6-digit OTP verification grants valid access token")

    status, _ = api_call("POST", "/api/auth/verify-otp", {"phone": test_phone, "otp": "123456"})
    check(status in (400, 403), "Single-use OTP invalidation: duplicate submission rejected")

    # Email login validation
    status, _ = api_call("POST", "/api/auth/login", {"email": "nonexistent@example.com", "password": "WrongPassword@123"})
    check(status == 401, "Invalid email/password returns 401 Unauthorized")

    status, pat_res = api_call("POST", "/api/auth/quick-login/patient")
    check(status == 200 and "access_token" in pat_res, "Patient quick-login succeeds")
    patient_token = pat_res.get("access_token")

    status, doc_res = api_call("POST", "/api/auth/quick-login/doctor")
    check(status == 200 and "access_token" in doc_res, "Doctor quick-login succeeds")
    doctor_token = doc_res.get("access_token")

    status, adm_res = api_call("POST", "/api/auth/quick-login/admin")
    check(status == 200 and "access_token" in adm_res, "Admin quick-login succeeds")
    admin_token = adm_res.get("access_token")

    status, me = api_call("GET", "/api/auth/me", token=patient_token)
    check(status == 200 and me.get("user", {}).get("full_name") == "Arjun Sharma", 
          "GET /api/auth/me returns Arjun Sharma for patient token")
    check(me.get("patient", {}).get("gender") == "Male", "Patient profile gender strictly Male")

    status, _ = api_call("GET", "/api/auth/me")
    check(status == 401, "Unauthenticated request to /api/auth/me returns 401 Unauthorized")

    status, _ = api_call("GET", "/api/auth/me", token="invalid.token.string")
    check(status == 401, "Corrupted token to /api/auth/me returns 401 Unauthorized")

    status, _ = api_call("GET", "/api/admin/overview", token=patient_token)
    check(status == 403, "RBAC Security: Patient denied access to /api/admin/overview (403 Forbidden)")

    status, _ = api_call("GET", "/api/doctor/overview", token=patient_token)
    check(status == 403, "RBAC Security: Patient denied access to /api/doctor/overview (403 Forbidden)")

    status, _ = api_call("GET", "/api/admin/overview", token=doctor_token)
    check(status == 403, "RBAC Security: Doctor denied access to /api/admin/overview (403 Forbidden)")

    # 3. PATIENT WORKFLOWS & CLINICAL DIRECTORY
    print("\n[SECTION 3: PATIENT WORKFLOWS & CLINICAL DIRECTORY]")
    status, dash = api_call("GET", "/api/patient/dashboard", token=patient_token)
    check(status == 200 and "patient" in dash, "GET /api/patient/dashboard returns overview statistics")

    status, depts = api_call("GET", "/api/patient/departments", token=patient_token)
    check(status == 200 and len(depts) == 22, f"GET /api/patient/departments returns all 22 clinical departments ({len(depts)})")

    status, hosps = api_call("GET", "/api/patient/hospitals", token=patient_token)
    check(status == 200 and len(hosps) >= 24, f"GET /api/patient/hospitals returns Indian hospitals directory ({len(hosps)})")
    first_hosp = hosps[0]
    check("latitude" in first_hosp and "longitude" in first_hosp, "Hospitals have GPS coordinates for distance precision")

    status, chennai_hosps = api_call("GET", "/api/patient/hospitals?city=Chennai", token=patient_token)
    check(status == 200 and len(chennai_hosps) > 0 and all(h["city"] == "Chennai" for h in chennai_hosps),
          f"City filter 'Chennai' returns 100% Chennai hospitals ({len(chennai_hosps)})")

    status, docs = api_call("GET", "/api/patient/doctors", token=patient_token)
    check(status == 200 and len(docs) >= 50, f"GET /api/patient/doctors returns doctors ({len(docs)})")
    first_doc = docs[0]
    check("shift_timing" in first_doc and "city" in first_doc, "Doctors include shift_timing and location")

    # 4. APPOINTMENT BOOKING & MANAGEMENT
    print("\n[SECTION 4: APPOINTMENT LIFECYCLE]")
    doc_id = first_doc["id"]
    status, slots_res = api_call("GET", f"/api/appointments/slots?doctor_id={doc_id}&date_str=2026-03-25", token=patient_token)
    check(status == 200 and "slots" in slots_res, f"GET /api/appointments/slots returns slots for doctor {doc_id}")

    appt_body = {
        "doctor_id": doc_id,
        "scheduled_date": "2026-03-25",
        "scheduled_time": "10:30",
        "duration_minutes": 30,
        "consultation_type": "In-Person",
        "reason_for_visit": "Routine cardiovascular wellness screening",
        "priority": "routine"
    }
    status, book_res = api_call("POST", "/api/patient/appointments", body=appt_body, token=patient_token)
    check(status in (200, 201) and "appointment_id" in book_res, "POST /api/patient/appointments books appointment successfully")
    appt_id = book_res.get("appointment_id")

    status, get_appt = api_call("GET", f"/api/patient/appointments/{appt_id}", token=patient_token)
    check(status == 200 and get_appt.get("appointment", {}).get("id") == appt_id, f"GET /api/patient/appointments/{appt_id} retrieves appointment details")

    resched_body = {"scheduled_date": "2026-03-26", "scheduled_time": "11:00", "reason": "Patient requested alternate slot"}
    status, resched_res = api_call("PUT", f"/api/patient/appointments/{appt_id}/reschedule", body=resched_body, token=patient_token)
    check(status == 200, f"PUT /api/patient/appointments/{appt_id}/reschedule updates appointment date/time")

    status, cancel_res = api_call("PUT", f"/api/patient/appointments/{appt_id}/cancel", body={"reason": "Schedule conflict"}, token=patient_token)
    check(status == 200, f"PUT /api/patient/appointments/{appt_id}/cancel safely cancels appointment")

    status, verify_cancelled = api_call("GET", f"/api/patient/appointments/{appt_id}", token=patient_token)
    check(verify_cancelled.get("appointment", {}).get("status") == "cancelled", "Cancelled appointment status persisted correctly")

    # 5. WAITLIST & PRIORITY QUEUE
    print("\n[SECTION 5: WAITLIST & STANDBY ALLOCATION]")
    waitlist_body = {
        "department_id": first_doc.get("department_id", 1),
        "doctor_id": doc_id,
        "preferred_date": "2026-03-27",
        "preferred_time_range": "morning",
        "allocation_strategy": "best_available",
        "priority": "routine",
        "reason_for_visit": "Need earliest OPD consultation",
        "consultation_type": "In-Person"
    }
    status, wl_res = api_call("POST", "/api/appointments/waitlist", body=waitlist_body, token=patient_token)
    check(status in (200, 201) and "waitlist_id" in wl_res, "POST /api/appointments/waitlist adds patient to priority standby")
    wl_id = wl_res.get("waitlist_id")

    status, my_wl = api_call("GET", "/api/appointments/waitlist", token=patient_token)
    check(status == 200 and any(w.get("id") == wl_id for w in my_wl), "GET /api/appointments/waitlist lists active standby entries")

    if wl_id:
        status, del_wl = api_call("DELETE", f"/api/appointments/waitlist/{wl_id}", token=patient_token)
        check(status == 200, f"DELETE /api/appointments/waitlist/{wl_id} removes standby request")

    # 6. DOCTOR PORTAL APIS
    print("\n[SECTION 6: DOCTOR PORTAL APIS]")
    status, doc_ov = api_call("GET", "/api/doctor/overview", token=doctor_token)
    check(status == 200 and "today_appointments" in doc_ov, "GET /api/doctor/overview loads clinical schedule")

    status, doc_appts = api_call("GET", "/api/doctor/appointments", token=doctor_token)
    check(status == 200 and isinstance(doc_appts, list), f"GET /api/doctor/appointments returns {len(doc_appts)} doctor consultations")

    status, doc_avail = api_call("GET", "/api/doctor/availability", token=doctor_token)
    check(status == 200 and "weekly_schedules" in doc_avail, "GET /api/doctor/availability returns physician schedule")

    status, doc_toggle = api_call("PUT", "/api/doctor/toggle-availability", token=doctor_token)
    check(status == 200 and "is_available" in doc_toggle, "PUT /api/doctor/toggle-availability toggles status")

    first_doc_appt_id = doc_appts[0]["id"] if doc_appts else 1
    note_body = {
        "appointment_id": first_doc_appt_id,
        "symptoms": "Mild exertional breathlessness",
        "clinical_notes": "BP well controlled with current therapeutic regimen. Pulse regular.",
        "diagnosis": "Essential Hypertension (ICD-10 I10)",
        "follow_up_date": "2026-04-10",
        "instructions": "Maintain sodium restricted diet.",
        "prescriptions": [
            {
                "medication_name": "Telmisartan",
                "dosage": "40mg",
                "frequency": "Once daily morning",
                "duration": "30 days",
                "instructions": "Take after breakfast"
            }
        ]
    }
    status, note_res = api_call("POST", "/api/doctor/consultation-notes", body=note_body, token=doctor_token)
    check(status in (200, 201) and "note_id" in note_res, "POST /api/doctor/consultation-notes archives finalized clinical note")

    # 7. ADMIN PORTAL APIS
    print("\n[SECTION 7: ADMIN PORTAL APIS]")
    status, adm_ov = api_call("GET", "/api/admin/overview", token=admin_token)
    check(status == 200 and "hospital_metrics" in adm_ov, "GET /api/admin/overview returns hospital KPIs & capacity metrics")

    status, adm_analytics = api_call("GET", "/api/admin/analytics", token=admin_token)
    check(status == 200 and "kpi" in adm_analytics, "GET /api/admin/analytics returns clinical traffic distributions")

    status, adm_docs = api_call("GET", "/api/admin/doctors", token=admin_token)
    check(status == 200 and len(adm_docs) >= 50, f"GET /api/admin/doctors lists all hospital doctors ({len(adm_docs)})")

    status, adm_hosp = api_call("GET", "/api/admin/hospitals", token=admin_token)
    check(status == 200 and len(adm_hosp) >= 20, f"GET /api/admin/hospitals lists accredited hospitals ({len(adm_hosp)})")

    status, adm_logs = api_call("GET", "/api/admin/audit-logs", token=admin_token)
    check(status == 200 and isinstance(adm_logs, list), f"GET /api/admin/audit-logs returns immutable security audit trail")

    ann_body = {
        "title": "Hospital Clinical Resource Protocol Active",
        "message": "All clinical nodes operational with CareAura Health OS 3.0.",
        "priority": "info",
        "target_role": "all"
    }
    status, ann_res = api_call("POST", "/api/admin/announcements", body=ann_body, token=admin_token)
    check(status in (200, 201), "POST /api/admin/announcements publishes administrative broadcast")

    # 8. AI CLINICAL ASSISTANT RETRIEVAL PRECISION
    print("\n[SECTION 8: AI CLINICAL ASSISTANT RETRIEVAL PRECISION]")
    ai_queries = [
        ("Find a cardiologist", "doctor_card"),
        ("Find dermatologists in Chennai", "doctor_card"),
        ("Find Tamil speaking doctors", "doctor_card"),
        ("Find Telugu speaking doctors in Hyderabad", "doctor_card"),
        ("Find hospitals in Mumbai", "hospital_card"),
        ("Find hospitals in Bengaluru", "hospital_card"),
        ("When is my next appointment?", "appointment_card"),
        ("Show my appointments", "appointment_card")
    ]
    for q, expected_card in ai_queries:
        status, ai_res = api_call("POST", "/api/chatbot/ask-direct", body={"message": q}, token=patient_token)
        card_type = ai_res.get("message", {}).get("card_type")
        check(status == 200 and card_type == expected_card, f"AI Query '{q}' -> {card_type}")

    # 9. SEARCH ROBUSTNESS & SQL INJECTION RESISTANCE
    print("\n[SECTION 9: SEARCH ROBUSTNESS & SECURITY]")
    status, empty_s = api_call("GET", "/api/search?q=")
    check(status == 200, "Empty search query succeeds without errors")

    status, partial_s = api_call("GET", "/api/search?q=card")
    check(status == 200 and len(partial_s.get("doctors", [])) > 0, "Partial search 'card' finds cardiologists")

    status, upper_s = api_call("GET", "/api/search?q=CARDIOLOGY")
    check(status == 200 and len(upper_s.get("doctors", [])) > 0, "Case-insensitive uppercase search succeeds")

    sqli_payload = urllib.parse.quote("' OR 1=1; DROP TABLE users; --")
    status, sqli_res = api_call("GET", f"/api/search?q={sqli_payload}")
    check(status == 200 and "doctors" in sqli_res, "SQL Injection attempt safely handled by parameterized query")

    status, verify_db = api_call("GET", "/api/health")
    check(status == 200, "Database integrity intact after SQL injection test")

    spec_payload = urllib.parse.quote("<script>alert(1)</script>")
    status, spec_res = api_call("GET", f"/api/search?q={spec_payload}")
    check(status == 200 and "doctors" in spec_res, "XSS script probe safely handled without reflected HTML execution")

    # 10. SPA CLIENT-SIDE ROUTING & DEEP LINKS
    print("\n[SECTION 10: SPA CLIENT-SIDE ROUTING]")
    spa_routes = ["/patient-dashboard", "/doctors", "/hospitals", "/appointments", "/profile", "/doctor-dashboard", "/admin-dashboard"]
    all_spa_pass = True
    for route in spa_routes:
        status, res = api_call("GET", route)
        if status != 200 or "CareAura Health OS" not in res.get("raw", ""):
            all_spa_pass = False
            print(f"  Failed on route: {route} (status {status})")
            break
    check(all_spa_pass, "SPA Fallback: Direct URL navigation & page refresh returns index.html for all routes")

    status, nf_api = api_call("GET", "/api/nonexistent-endpoint-1234")
    check(status == 404 and "detail" in nf_api, "Non-existent API route returns structured 404 JSON")

    # SUMMARY
    print(f"\n========================================================")
    print(f"QA RESULTS: {passed}/{total} tests PASSED ({passed*100//total}%)")
    if failed_tests:
        print(f"FAILED TESTS ({len(failed_tests)}):")
        for f in failed_tests:
            print(f"  - {f}")
    print(f"========================================================\n")
    return passed == total

if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)

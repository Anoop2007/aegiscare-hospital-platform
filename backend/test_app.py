import urllib.request
import json
import time
import sys

# Ensure UTF-8 output on Windows terminal
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
    print("================================================================================")
    print("   AegisCare Clinical Operating System - AI Optimization Verification Suite     ")
    print("================================================================================")

    print("\n--- 1. Health & Readiness ---")
    code, res = request_json("/api/health")
    assert code == 200, f"Health check failed: {code}, {res}"
    print(f"[PASS] Health check OK: {res['service']} v{res['version']} (Status: {res['status']})")

    print("\n--- 2. Role Authentication & Access Tokens ---")
    # Patient Jane Doe
    code, patient_auth = request_json("/api/auth/quick-login/patient", method="POST")
    assert code == 200, f"Patient login failed: {patient_auth}"
    pat_token = patient_auth["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    print(f"[PASS] Patient: {patient_auth['user']['full_name']} (MRN: {patient_auth['user'].get('mrn')})")

    # Doctor Dr. Sharma
    code, doctor_auth = request_json("/api/auth/quick-login/doctor", method="POST")
    assert code == 200, f"Doctor login failed: {doctor_auth}"
    doc_token = doctor_auth["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    print(f"[PASS] Doctor: {doctor_auth['user']['full_name']} ({doctor_auth['user'].get('specialization')})")

    # Admin CMO
    code, admin_auth = request_json("/api/auth/quick-login/admin", method="POST")
    assert code == 200, f"Admin login failed: {admin_auth}"
    admin_token = admin_auth["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"[PASS] Admin: {admin_auth['user']['full_name']}")

    print("\n--- 3. Testing 5 AI Allocation Strategies & Explainable Recommendations ---")
    strategies = [
        ("best_available", "Multi-factor 24-parameter optimization"),
        ("fastest_available", "Earliest slot with minimum wait time"),
        ("preferred_doctor", "Continuity of care with preferred physician"),
        ("preferred_time", "Targeted time-of-day morning window"),
        ("balanced_workload", "Hospital shift load balancing")
    ]

    for strat_key, strat_desc in strategies:
        payload = {
            "urgency": "urgent",
            "reason_for_visit": "Persistent chest heaviness with exertional palpitations",
            "consultation_type": "In-Person",
            "allocation_strategy": strat_key,
            "preferred_time_range": "morning" if strat_key == "preferred_time" else "any",
            "preferred_doctor_id": 1 if strat_key == "preferred_doctor" else None
        }
        code, rec = request_json("/api/appointments/ai-recommend", method="POST", data=payload, headers=pat_headers)
        assert code == 200, f"AI Recommender failed for strategy {strat_key}: {code}, {rec}"
        assert rec["total_recommendations"] > 0, f"No recommendations returned for {strat_key}"
        top = rec["recommendations"][0]
        
        # Verify explainability points
        assert "explanation_points" in top, "Missing explanation_points"
        assert len(top["explanation_points"]) >= 1, "Explanation points empty"
        assert "suitability_score" in top, "Missing suitability_score"
        assert "breakdown" in top, "Missing score breakdown"
        
        print(f"[PASS] Strategy [{strat_key}]: Match '{top['doctor_name']}' | Score: {top['suitability_score']}% | Slot: {top['recommended_slot']} | Est. Wait: {top['estimated_wait_time']}m")
        print(f"   Explanation sample: {top['explanation_points'][0]}")

    print("\n--- 4. Testing Live Patient Queue Tracking & Progression ---")
    # Fetch doctor's overview to find today's appointment
    code, doc_overview = request_json("/api/doctor/overview", headers=doc_headers)
    assert code == 200, f"Doctor overview failed: {code}, {doc_overview}"
    today_appts = doc_overview["today_appointments"]
    assert len(today_appts) > 0, "No appointments today for queue testing"
    test_appt = today_appts[0]
    test_appt_id = test_appt["id"]
    print(f"Queue target appointment: #{test_appt['appointment_number']} (Patient: {test_appt['patient_name']})")

    # Patient checks live queue status
    code, q_status = request_json(f"/api/appointments/{test_appt_id}/queue-status", headers=pat_headers)
    assert code == 200, f"Queue status query failed: {code}, {q_status}"
    print(f"[PASS] Live Queue Status: Position #{q_status['queue_position']}, Patients Ahead: {q_status['patients_ahead']}, Est. Wait: {q_status['estimated_wait_minutes']}m ({q_status['status_message']})")

    # Doctor records +10m clinic delay
    code, delay_res = request_json(f"/api/appointments/{test_appt_id}/queue-status", method="PUT", data={
        "action": "mark_delay",
        "delay_minutes": 10
    }, headers=doc_headers)
    assert code == 200, f"Mark delay failed: {code}, {delay_res}"
    print(f"[PASS] Doctor Queue Control: Recorded +10m clinic delay ({delay_res['message']})")

    # Patient check-in
    code, checkin_res = request_json(f"/api/appointments/{test_appt_id}/queue-status", method="PUT", data={
        "action": "check_in"
    }, headers=pat_headers)
    assert code == 200, f"Patient check-in failed: {code}, {checkin_res}"
    print(f"[PASS] Patient Check-In: Successfully checked in ({checkin_res['message']})")

    # Doctor starts consult
    code, consult_res = request_json(f"/api/appointments/{test_appt_id}/queue-status", method="PUT", data={
        "action": "start_consult"
    }, headers=doc_headers)
    assert code == 200, f"Start consult failed: {code}, {consult_res}"
    print(f"[PASS] Doctor Progression: Consultation in-progress ({consult_res['message']})")

    print("\n--- 5. Testing Standby Priority Waitlist & Auto-Reallocation ---")
    # Patient joins standby waitlist
    code, wl_join = request_json("/api/appointments/waitlist", method="POST", data={
        "department_id": 1,
        "preferred_time_range": "morning",
        "priority": "urgent",
        "reason_for_visit": "Urgent chest evaluation standby",
        "consultation_type": "In-Person",
        "allocation_strategy": "fastest_available"
    }, headers=pat_headers)
    assert code == 201, f"Waitlist join failed: {code}, {wl_join}"
    wl_id = wl_join["waitlist_id"]
    print(f"[PASS] Joined Waitlist: Standby Entry #WL-{wl_id} (Priority Score: {wl_join['priority_score']})")

    # Patient views active waitlist
    code, wl_list = request_json("/api/appointments/waitlist", headers=pat_headers)
    assert code == 200, f"Waitlist list failed: {code}, {wl_list}"
    assert len(wl_list) > 0, "No waitlist entries found"
    print(f"[PASS] Active standby waitlist entries for patient: {len(wl_list)}")

    # Admin views centralized waitlist
    code, adm_wl = request_json("/api/admin/waitlist", headers=admin_headers)
    assert code == 200, f"Admin waitlist failed: {code}, {adm_wl}"
    print(f"[PASS] Hospital admin master standby waitlist items: {len(adm_wl)}")

    print("\n--- 6. Testing Admin AI Operational Forecasting & Capacity Bottlenecks ---")
    code, insights = request_json("/api/admin/ai-insights", headers=admin_headers)
    assert code == 200, f"AI insights failed: {code}, {insights}"
    f = insights["forecast"]
    print(f"[PASS] Next-Day Demand Forecast: {f['predicted_demand_total']} patient visits predicted")
    print(f"[PASS] Predicted Cancellations: {f['predicted_cancellations']} ({f['cancellation_rate_percent']}%)")
    print(f"[PASS] Predicted No-Shows: {f['predicted_noshows']} ({f['noshow_rate_percent']}%)")
    print(f"[PASS] Standby Backfill Opportunities: {f['waitlist_backfill_opportunities']} open slots")
    print(f"[PASS] Peak Hour Distribution slots: {list(f['peak_hour_distribution'].keys())[:4]}...")
    print(f"[PASS] Capacity Bottleneck Alerts: {len(f['bottlenecks'])} alerts documented")
    if f['bottlenecks']:
        print(f"   Alert sample: [{f['bottlenecks'][0]['type'].upper()}] {f['bottlenecks'][0]['message']}")

    print("\n--- 7. Testing Doctor Workload Balancing Insights ---")
    code, wl_balance = request_json("/api/doctor/workload-balancing", headers=doc_headers)
    assert code == 200, f"Doctor workload balancing failed: {code}, {wl_balance}"
    print(f"[PASS] Workload Balancing Engine: Overloaded doctors = {len(wl_balance.get('overloaded_doctors', []))}, Underutilized = {len(wl_balance.get('underutilized_doctors', []))}")
    print(f"[PASS] Actionable balancing recommendations generated: {len(wl_balance.get('recommendations', []))}")

    print("\n--- 8. Testing Unified Longitudinal Patient Health Timeline ---")
    code, timeline_res = request_json("/api/patient/timeline", headers=pat_headers)
    assert code == 200, f"Timeline fetch failed: {code}, {timeline_res}"
    timeline = timeline_res["timeline"]
    assert len(timeline) > 0, "No timeline events returned"
    print(f"[PASS] Longitudinal Patient Timeline: {len(timeline)} chronological health events synthesized")
    types_found = {e["event_type"] for e in timeline}
    print(f"   Event categories present: {list(types_found)}")
    print(f"   Most recent record: [{timeline[0]['event_type'].upper()}] {timeline[0]['title']} ({timeline[0]['event_date']})")

    print("\n--- 9. Testing Context-Aware Clinical Assistant Chatbot ---")
    # Test query 1: Queue status inquiry
    code, chat1 = request_json("/api/chatbot/conversations", method="POST", data={
        "title": "Live queue wait inquiry",
        "initial_message": "What is my live queue wait time and which doctor am I seeing today?"
    }, headers=pat_headers)
    assert code == 201, f"Chatbot query 1 failed: {code}, {chat1}"
    code, msgs1 = request_json(f"/api/chatbot/conversations/{chat1['conversation_id']}", headers=pat_headers)
    last_msg1 = msgs1["messages"][-1]["message_text"]
    assert "Dr." in last_msg1 or "appointment" in last_msg1 or "queue" in last_msg1.lower(), "Assistant did not provide appointment context"
    print(f"[PASS] Assistant contextual queue response OK (Excerpt: {last_msg1[:100]}...)")

    # Test query 2: Emergency triage safeguard
    code, chat2 = request_json("/api/chatbot/conversations", method="POST", data={
        "title": "Acute symptom check",
        "initial_message": "I have sudden severe crushing chest pain radiating to my left jaw and shortness of breath"
    }, headers=pat_headers)
    assert code == 201, f"Chatbot query 2 failed: {code}, {chat2}"
    code, msgs2 = request_json(f"/api/chatbot/conversations/{chat2['conversation_id']}", headers=pat_headers)
    last_msg2 = msgs2["messages"][-1]["message_text"]
    assert "emergency" in last_msg2.lower() or "911" in last_msg2 or "immediate" in last_msg2.lower(), "Assistant failed emergency safety triage!"
    print(f"[PASS] Assistant emergency triage safeguard active: Promptly triggered urgent care directive.")

    print("\n================================================================================")
    print("   ALL 9 ADVANCED OPERATIONAL & AI OPTIMIZATION SUITES PASSED [100% OK]         ")
    print("================================================================================")

if __name__ == "__main__":
    run_tests()

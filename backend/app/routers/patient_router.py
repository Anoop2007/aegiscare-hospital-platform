from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from datetime import datetime, timezone
import json
import secrets
from typing import Optional, List
from ..database import query_all, query_one, execute_insert, execute_update
from ..auth import require_patient, get_current_user, log_audit
from ..schemas import (
    AppointmentCreateRequest, AppointmentRescheduleRequest,
    AppointmentCancelRequest, AIHealthSummaryRequest
)
from ..ai_service import HospitalAIService

router = APIRouter(prefix="/patient", tags=["Patient Module"])

@router.get("/dashboard")
def get_patient_dashboard(current_user: dict = Depends(require_patient)):
    patient_id = current_user.get("patient_id")
    if not patient_id:
        p = query_one("SELECT id FROM patients WHERE user_id = ?", (current_user["id"],))
        if not p:
            raise HTTPException(status_code=404, detail="Patient profile not registered.")
        patient_id = p["id"]

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Upcoming appointment (earliest scheduled or confirmed)
    upcoming_appt = query_one(
        """SELECT a.*, d.specialization, d.room_number, d.branch, u.full_name as doctor_name, u.avatar_url as doctor_avatar, dep.name as department_name
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           JOIN departments dep ON a.department_id = dep.id
           WHERE a.patient_id = ? AND a.scheduled_date >= ? AND a.status IN ('scheduled', 'confirmed', 'in_progress')
           ORDER BY a.scheduled_date ASC, a.scheduled_time ASC LIMIT 1""",
        (patient_id, today_str)
    )

    if upcoming_appt and upcoming_appt["scheduled_date"] == today_str:
        upcoming_appt["queue_details"] = HospitalAIService.calculate_patient_queue_status(upcoming_appt["id"])


    # Next available clinic slot prompt if no upcoming appointment
    next_available_slot = None
    if not upcoming_appt:
        available_doc = query_one(
            """SELECT d.id, u.full_name, dep.name as department_name, d.specialization
               FROM doctors d JOIN users u ON d.user_id = u.id
               JOIN departments dep ON d.department_id = dep.id
               WHERE d.is_available = 1 LIMIT 1"""
        )
        if available_doc:
            next_available_slot = {
                "doctor_id": available_doc["id"],
                "doctor_name": available_doc["full_name"],
                "department": available_doc["department_name"],
                "specialization": available_doc["specialization"],
                "date": today_str,
                "time": "14:00"
            }

    # Summary metrics
    total_appts = query_one("SELECT COUNT(*) as cnt FROM appointments WHERE patient_id = ?", (patient_id,))["cnt"]
    completed_appts = query_one("SELECT COUNT(*) as cnt FROM appointments WHERE patient_id = ? AND status = 'completed'", (patient_id,))["cnt"]
    total_reports = query_one("SELECT COUNT(*) as cnt FROM health_reports WHERE patient_id = ?", (patient_id,))["cnt"]
    unread_notifications = query_one("SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0", (current_user["id"],))["cnt"]

    # Recent clinical activity
    recent_activity = query_all(
        """SELECT 'appointment' as type, a.scheduled_date as date, 'Consultation with ' || u.full_name as title,
                  a.status as status, a.appointment_number as reference
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           WHERE a.patient_id = ?
           UNION ALL
           SELECT 'report' as type, r.report_date as date, r.title as title, 'Verified' as status, r.file_name as reference
           FROM health_reports r
           WHERE r.patient_id = ?
           ORDER BY date DESC LIMIT 6""",
        (patient_id, patient_id)
    )

    # Notifications preview
    notifications = query_all(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (current_user["id"],)
    )

    patient_details = query_one("SELECT * FROM patients WHERE id = ?", (patient_id,))

    return {
        "patient": {
            "id": patient_id,
            "full_name": current_user["full_name"],
            "mrn": patient_details["mrn"] if patient_details else "N/A",
            "blood_group": patient_details["blood_group"] if patient_details else "N/A",
            "allergies": patient_details["allergies"] if patient_details else None,
            "chronic_conditions": patient_details["chronic_conditions"] if patient_details else None
        },
        "upcoming_appointment": upcoming_appt,
        "next_available_slot": next_available_slot,
        "metrics": {
            "total_appointments": total_appts,
            "completed_consultations": completed_appts,
            "uploaded_reports": total_reports,
            "unread_notifications": unread_notifications
        },
        "recent_activity": recent_activity,
        "notifications": notifications
    }

@router.get("/doctors")
def get_doctor_directory(
    department_id: Optional[int] = None,
    specialty: Optional[str] = None,
    branch: Optional[str] = None,
    city: Optional[str] = None,
    doctor_name: Optional[str] = None,
    consultation_type: Optional[str] = None, # 'In-Person' or 'Video'
    availability_status: Optional[str] = None, # 'available' or 'all'
    languages: Optional[str] = None,
    min_experience: Optional[int] = None
):
    sql = """
        SELECT d.*, u.full_name, u.email, u.avatar_url, u.phone,
               dep.name as department_name, dep.code as department_code,
               h.latitude, h.longitude, h.image_url as hospital_image,
               (SELECT COUNT(*) FROM appointments a WHERE a.doctor_id = d.id AND a.scheduled_date = DATE('now') AND a.status NOT IN ('cancelled')) as today_patient_count
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        JOIN departments dep ON d.department_id = dep.id
        LEFT JOIN hospitals h ON d.hospital_id = h.id
        WHERE u.is_active = 1
    """
    params = []

    if department_id:
        sql += " AND d.department_id = ?"
        params.append(department_id)

    if specialty:
        sql += " AND (LOWER(d.specialization) LIKE ? OR LOWER(dep.name) LIKE ?)"
        params.extend([f"%{specialty.lower()}%", f"%{specialty.lower()}%"])

    if city and city != "all":
        sql += " AND LOWER(d.city) = ?"
        params.append(city.lower())

    if branch:
        sql += " AND LOWER(d.branch) LIKE ?"
        params.append(f"%{branch.lower()}%")

    if doctor_name:
        sql += " AND LOWER(u.full_name) LIKE ?"
        params.append(f"%{doctor_name.lower()}%")

    if consultation_type:
        sql += " AND LOWER(d.consultation_modes) LIKE ?"
        params.append(f"%{consultation_type.lower()}%")

    if availability_status == "available":
        sql += " AND d.is_available = 1"

    if languages:
        sql += " AND LOWER(d.languages) LIKE ?"
        params.append(f"%{languages.lower()}%")

    if min_experience is not None:
        sql += " AND d.experience_years >= ?"
        params.append(min_experience)

    sql += " ORDER BY d.experience_years DESC, d.is_available DESC"

    doctors = query_all(sql, tuple(params))
    
    # Calculate next available slot and waiting time estimate for each doctor
    for doc in doctors:
        load = doc["today_patient_count"]
        doc["estimated_wait_time"] = 10 + (load * 6)
        doc["queue_status"] = "Low Queue" if load < 4 else ("Moderate Queue" if load < 8 else "High Queue")
        doc["next_available_slot"] = "10:30 AM" if doc["is_available"] else "Next Clinic Shift"

    return doctors

@router.get("/departments")
def get_departments():
    departments = query_all("""
        SELECT dep.*, COUNT(d.id) as doctor_count
        FROM departments dep
        LEFT JOIN doctors d ON dep.id = d.department_id
        WHERE dep.is_active = 1
        GROUP BY dep.id
        ORDER BY dep.name ASC
    """)
    return departments

@router.get("/appointments")
def get_patient_appointments(
    status_filter: Optional[str] = Query("all", pattern="^(all|upcoming|completed|cancelled)$"),
    current_user: dict = Depends(require_patient)
):
    patient_id = current_user["patient_id"]
    sql = """
        SELECT a.*, d.specialization, d.room_number, d.branch, d.consultation_fee,
               u.full_name as doctor_name, u.avatar_url as doctor_avatar, dep.name as department_name,
               (SELECT cn.diagnosis FROM consultation_notes cn WHERE cn.appointment_id = a.id) as diagnosis
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        JOIN departments dep ON a.department_id = dep.id
        WHERE a.patient_id = ?
    """
    params = [patient_id]

    if status_filter == "upcoming":
        sql += " AND a.status IN ('scheduled', 'confirmed', 'in_progress')"
    elif status_filter == "completed":
        sql += " AND a.status = 'completed'"
    elif status_filter == "cancelled":
        sql += " AND a.status IN ('cancelled', 'no_show')"

    sql += " ORDER BY a.scheduled_date DESC, a.scheduled_time DESC"
    return query_all(sql, tuple(params))

@router.get("/appointments/{appointment_id}")
def get_appointment_details(appointment_id: int, current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    appt = query_one(
        """SELECT a.*, d.specialization, d.room_number, d.branch, d.consultation_fee, d.consultation_modes,
                  u.full_name as doctor_name, u.avatar_url as doctor_avatar, u.phone as doctor_phone,
                  dep.name as department_name, dep.floor_location
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           JOIN departments dep ON a.department_id = dep.id
           WHERE a.id = ? AND a.patient_id = ?""",
        (appointment_id, patient_id)
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found or unauthorized.")

    # Clinical notes if available
    notes = query_one("SELECT * FROM consultation_notes WHERE appointment_id = ?", (appointment_id,))
    prescription = query_one("SELECT * FROM prescriptions WHERE appointment_id = ?", (appointment_id,))
    if prescription and prescription["medications_json"]:
        prescription["medications"] = json.loads(prescription["medications_json"])

    history = query_all("SELECT * FROM appointment_history WHERE appointment_id = ? ORDER BY timestamp DESC", (appointment_id,))

    return {
        "appointment": appt,
        "consultation_notes": notes,
        "prescription": prescription,
        "status_history": history
    }

@router.post("/appointments", status_code=status.HTTP_201_CREATED)
def book_appointment(req: AppointmentCreateRequest, request: Request, current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]

    # Verify doctor
    doctor = query_one(
        "SELECT d.*, u.full_name FROM doctors d JOIN users u ON d.user_id = u.id WHERE d.id = ? AND d.is_available = 1",
        (req.doctor_id,)
    )
    if not doctor:
        raise HTTPException(status_code=400, detail="Selected doctor is not available for booking.")

    # Conflict check
    conflict = query_one(
        "SELECT id FROM appointments WHERE doctor_id = ? AND scheduled_date = ? AND scheduled_time = ? AND status NOT IN ('cancelled')",
        (req.doctor_id, req.scheduled_date, req.scheduled_time)
    )
    if conflict:
        raise HTTPException(status_code=409, detail="The selected time slot has already been reserved. Please select another slot.")

    # Generate appointment number e.g. AC-2026-XXXX
    rand_num = secrets.randbelow(9000) + 1000
    appt_num = f"AC-2026-{rand_num}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Calculate queue & wait time
    current_day_load = query_one(
        "SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id = ? AND scheduled_date = ? AND status NOT IN ('cancelled')",
        (req.doctor_id, req.scheduled_date)
    )["cnt"]
    wait_time = 10 + (current_day_load * 5)

    appt_id = execute_insert(
        """INSERT INTO appointments (appointment_number, patient_id, doctor_id, department_id, scheduled_date,
                                   scheduled_time, duration_minutes, consultation_type, status, priority,
                                   reason_for_visit, estimated_wait_time, meeting_link, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', ?, ?, ?, ?, ?, ?)""",
        (
            appt_num, patient_id, req.doctor_id, doctor["department_id"], req.scheduled_date,
            req.scheduled_time, req.duration_minutes, req.consultation_type, req.priority,
            req.reason_for_visit, wait_time, f"https://meet.careaura.health/room/{appt_num}",
            now_iso, now_iso
        )
    )

    # History entry
    execute_insert(
        """INSERT INTO appointment_history (appointment_id, previous_status, new_status, changed_by_user_id, notes, timestamp)
           VALUES (?, NULL, 'confirmed', ?, 'Appointment scheduled by patient via online platform.', ?)""",
        (appt_id, current_user["id"], now_iso)
    )

    # Notifications for patient and doctor
    execute_insert(
        """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
           VALUES (?, 'Appointment Confirmed', ?, 'appointment_confirmation', 0, '/appointments', ?)""",
        (
            current_user["id"],
            f"Appointment #{appt_num} confirmed with {doctor['full_name']} on {req.scheduled_date} at {req.scheduled_time}.",
            now_iso
        )
    )
    execute_insert(
        """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
           VALUES (?, 'New Patient Scheduled', ?, 'appointment_confirmation', 0, '/appointments', ?)""",
        (
            doctor["user_id"],
            f"New {req.consultation_type} appointment #{appt_num} scheduled for {req.scheduled_date} at {req.scheduled_time}.",
            now_iso
        )
    )

    log_audit(current_user["id"], "BOOK_APPOINTMENT", "APPOINTMENT", str(appt_id), {"appointment_number": appt_num}, request.client.host if request.client else "127.0.0.1")

    return {
        "status": "success",
        "message": "Appointment successfully confirmed.",
        "appointment_id": appt_id,
        "appointment_number": appt_num,
        "scheduled_date": req.scheduled_date,
        "scheduled_time": req.scheduled_time,
        "doctor_name": doctor["full_name"],
        "consultation_type": req.consultation_type,
        "estimated_wait_time": wait_time
    }

@router.put("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(appointment_id: int, req: AppointmentRescheduleRequest, request: Request, current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    appt = query_one("SELECT * FROM appointments WHERE id = ? AND patient_id = ?", (appointment_id, patient_id))
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if appt["status"] in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot reschedule an appointment that is already {appt['status']}.")

    # Conflict check
    conflict = query_one(
        "SELECT id FROM appointments WHERE doctor_id = ? AND scheduled_date = ? AND scheduled_time = ? AND id != ? AND status NOT IN ('cancelled')",
        (appt["doctor_id"], req.scheduled_date, req.scheduled_time, appointment_id)
    )
    if conflict:
        raise HTTPException(status_code=409, detail="Selected slot is already reserved. Please choose another time.")

    now_iso = datetime.now(timezone.utc).isoformat()
    old_time = f"{appt['scheduled_date']} {appt['scheduled_time']}"

    execute_update(
        "UPDATE appointments SET scheduled_date = ?, scheduled_time = ?, updated_at = ? WHERE id = ?",
        (req.scheduled_date, req.scheduled_time, now_iso, appointment_id)
    )

    execute_insert(
        """INSERT INTO appointment_history (appointment_id, previous_status, new_status, changed_by_user_id, notes, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            appointment_id, appt["status"], appt["status"], current_user["id"],
            f"Rescheduled from {old_time} to {req.scheduled_date} {req.scheduled_time}. Reason: {req.reason or 'Patient schedule change'}",
            now_iso
        )
    )

    execute_insert(
        """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
           VALUES (?, 'Appointment Rescheduled', ?, 'reschedule', 0, '/appointments', ?)""",
        (
            current_user["id"],
            f"Your appointment #{appt['appointment_number']} has been rescheduled to {req.scheduled_date} at {req.scheduled_time}.",
            now_iso
        )
    )

    log_audit(current_user["id"], "RESCHEDULE_APPOINTMENT", "APPOINTMENT", str(appointment_id), {"old_time": old_time, "new_date": req.scheduled_date, "new_time": req.scheduled_time}, request.client.host if request.client else "127.0.0.1")

    return {"status": "success", "message": "Appointment rescheduled successfully."}

@router.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int, req: AppointmentCancelRequest, request: Request, current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    appt = query_one("SELECT * FROM appointments WHERE id = ? AND patient_id = ?", (appointment_id, patient_id))
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if appt["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Appointment is already cancelled.")

    now_iso = datetime.now(timezone.utc).isoformat()
    execute_update(
        "UPDATE appointments SET status = 'cancelled', cancellation_reason = ?, updated_at = ? WHERE id = ?",
        (req.reason, now_iso, appointment_id)
    )

    execute_insert(
        """INSERT INTO appointment_history (appointment_id, previous_status, new_status, changed_by_user_id, notes, timestamp)
           VALUES (?, ?, 'cancelled', ?, ?, ?)""",
        (appointment_id, appt["status"], current_user["id"], f"Cancelled by patient: {req.reason}", now_iso)
    )

    execute_insert(
        """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
           VALUES (?, 'Appointment Cancelled', ?, 'cancellation', 0, '/appointments', ?)""",
        (
            current_user["id"],
            f"Your appointment #{appt['appointment_number']} has been cancelled.",
            now_iso
        )
    )

    log_audit(current_user["id"], "CANCEL_APPOINTMENT", "APPOINTMENT", str(appointment_id), {"reason": req.reason}, request.client.host if request.client else "127.0.0.1")

    # Smart Waitlist Auto-Reallocation
    waitlist_match = HospitalAIService.process_waitlist_on_cancellation(appointment_id)

    return {
        "status": "success",
        "message": "Appointment has been cancelled.",
        "waitlist_reallocated": waitlist_match is not None,
        "reallocated_patient": waitlist_match.get("patient_name") if waitlist_match else None
    }

@router.get("/timeline")
def get_patient_timeline(current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    timeline = HospitalAIService.get_unified_patient_timeline(patient_id)
    return {"timeline": timeline, "total": len(timeline)}

@router.get("/medical-history")
def get_medical_history(current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    records = query_all(
        """SELECT mr.*, u.full_name as doctor_name, dep.name as department_name
           FROM medical_records mr
           LEFT JOIN doctors d ON mr.doctor_id = d.id
           LEFT JOIN users u ON d.user_id = u.id
           LEFT JOIN departments dep ON d.department_id = dep.id
           WHERE mr.patient_id = ?
           ORDER BY mr.record_date DESC""",
        (patient_id,)
    )
    prescriptions = query_all(
        """SELECT p.*, u.full_name as doctor_name
           FROM prescriptions p
           JOIN doctors d ON p.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           WHERE p.patient_id = ?
           ORDER BY p.issued_date DESC""",
        (patient_id,)
    )
    for p in prescriptions:
        if p["medications_json"]:
            p["medications"] = json.loads(p["medications_json"])

    patient = query_one("SELECT allergies, chronic_conditions, blood_group, mrn FROM patients WHERE id = ?", (patient_id,))

    return {
        "allergies": patient["allergies"],
        "chronic_conditions": patient["chronic_conditions"],
        "blood_group": patient["blood_group"],
        "mrn": patient["mrn"],
        "clinical_records": records,
        "prescriptions": prescriptions
    }

@router.get("/health-reports")
def get_health_reports(
    report_type: Optional[str] = None,
    query_str: Optional[str] = None,
    current_user: dict = Depends(require_patient)
):
    patient_id = current_user["patient_id"]
    sql = "SELECT id, patient_id, title, report_type, hospital_facility, ordering_doctor, report_date, file_name, file_size, summary, created_at FROM health_reports WHERE patient_id = ?"
    params = [patient_id]

    if report_type and report_type != "all":
        sql += " AND report_type = ?"
        params.append(report_type)

    if query_str:
        sql += " AND (LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(ordering_doctor) LIKE ?)"
        term = f"%{query_str.lower()}%"
        params.extend([term, term, term])

    sql += " ORDER BY report_date DESC"
    return query_all(sql, tuple(params))

@router.get("/health-reports/{report_id}")
def get_health_report_detail(report_id: int, current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    rep = query_one("SELECT * FROM health_reports WHERE id = ? AND patient_id = ?", (report_id, patient_id))
    if not rep:
        raise HTTPException(status_code=404, detail="Diagnostic report not found.")
    return rep

@router.post("/ai-health-summary")
def generate_ai_health_summary(req: Optional[AIHealthSummaryRequest] = None, current_user: dict = Depends(require_patient)):
    patient_id = current_user["patient_id"]
    summary = HospitalAIService.generate_health_summary(patient_id)
    return summary

@router.get("/notifications")
def get_patient_notifications(current_user: dict = Depends(get_current_user)):
    notes = query_all("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 25", (current_user["id"],))
    return notes

@router.put("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    execute_update("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notification_id, current_user["id"]))
    return {"status": "success"}

@router.put("/notifications/mark-all-read")
def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    execute_update("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (current_user["id"],))
    return {"status": "success"}

@router.get("/hospitals")
def get_hospitals(
    city: Optional[str] = None,
    query_str: Optional[str] = None,
    emergency_only: Optional[bool] = False,
    current_user: dict = Depends(get_current_user)
):
    sql = "SELECT * FROM hospitals WHERE 1=1"
    params = []
    if city and city != "all":
        sql += " AND LOWER(city) = ?"
        params.append(city.lower())
    if emergency_only:
        sql += " AND LOWER(opening_hours) LIKE '%emergency%'"
    if query_str:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(locality) LIKE ? OR LOWER(city) LIKE ?)"
        term = f"%{query_str.lower()}%"
        params.extend([term, term, term])
    sql += " ORDER BY id ASC"
    hospitals = query_all(sql, tuple(params))
    
    # Pre-fetch doctor counts per hospital
    doc_counts = {r["hospital_id"]: r["cnt"] for r in query_all("SELECT hospital_id, count(*) as cnt FROM doctors WHERE is_available = 1 GROUP BY hospital_id")}
    
    for h in hospitals:
        h["phone"] = h.get("contact_phone", "+91 44 2490 1234")
        h["consultation_base_fee"] = h.get("starting_fee", 500.0)
        h["starting_fee"] = h.get("starting_fee", 500.0)
        h["rating"] = 4.9 if h["id"] % 2 == 0 else 4.8
        h["bed_capacity"] = 280 + (h["id"] * 15) % 200
        h["icu_beds"] = 35 + (h["id"] * 4) % 25
        h["emergency_24x7"] = 1
        h["ambulance_available"] = 1
        h["state"] = "India"
        h["available_doctors_count"] = doc_counts.get(h["id"], 2)
        h["appointment_availability"] = "Slots Available Today & Tomorrow"
        
        # Parse departments list
        depts = []
        if h.get("departments_json"):
            try:
                depts = json.loads(h["departments_json"])
            except Exception:
                depts = []
        if not depts:
            depts = ["General Medicine", "Cardiology", "Emergency Medicine", "Pediatrics"]
        h["departments"] = depts

        # Parse services list
        services = []
        if h.get("services_json"):
            try:
                services = json.loads(h["services_json"])
            except Exception:
                services = []
        if not services:
            services = ["24x7 Emergency", "ICU", "Diagnostic Imaging", "Modular OT"]
        h["services"] = services

        if not h.get("image_url"):
            h["image_url"] = "https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600"

    return hospitals

@router.get("/hospitals/{hospital_id}")
def get_hospital_details(hospital_id: int, current_user: dict = Depends(get_current_user)):
    hosp = query_one("SELECT * FROM hospitals WHERE id = ?", (hospital_id,))
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found.")
    doctors = query_all(
        """SELECT d.*, u.full_name as doctor_name, u.avatar_url, dep.name as department_name, dep.code as department_code
           FROM doctors d
           JOIN users u ON d.user_id = u.id
           JOIN departments dep ON d.department_id = dep.id
           WHERE d.hospital_id = ? AND u.is_active = 1
           ORDER BY d.experience_years DESC""",
        (hospital_id,)
    )
    
    depts = []
    if hosp.get("departments_json"):
        try:
            depts = json.loads(hosp["departments_json"])
        except Exception:
            pass
    if not depts:
        depts = list({d["department_name"] for d in doctors}) or ["General Medicine", "Cardiology"]
    
    services = []
    if hosp.get("services_json"):
        try:
            services = json.loads(hosp["services_json"])
        except Exception:
            pass

    return {
        "hospital": {
            **dict(hosp),
            "departments": depts,
            "services": services,
            "phone": hosp.get("contact_phone", "+91 44 2490 1234"),
            "starting_fee": hosp.get("starting_fee", 500.0),
            "available_doctors_count": len(doctors),
            "appointment_availability": "Slots Available Today & Tomorrow"
        },
        "doctors": doctors
    }




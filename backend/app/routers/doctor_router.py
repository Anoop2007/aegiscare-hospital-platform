from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timedelta, timezone
import json
from typing import Optional, List
from ..database import query_all, query_one, execute_insert, execute_update
from ..auth import require_doctor, log_audit
from ..schemas import (
    DoctorAvailabilityUpdateRequest, DoctorLeaveCreateRequest,
    ConsultationNoteCreateRequest, AppointmentStatusUpdateRequest
)
from ..ai_service import HospitalAIService

router = APIRouter(prefix="/doctor", tags=["Doctor Module"])

@router.get("/overview")
def get_doctor_overview(current_user: dict = Depends(require_doctor)):
    doctor_id = current_user.get("doctor_id")
    today_str = datetime.now().strftime("%Y-%m-%d")

    doctor = query_one(
        """SELECT d.*, dep.name as department_name, u.full_name, u.avatar_url
           FROM doctors d
           JOIN departments dep ON d.department_id = dep.id
           JOIN users u ON d.user_id = u.id
           WHERE d.id = ?""",
        (doctor_id,)
    )

    # Today's appointments
    today_appts = query_all(
        """SELECT a.*, p.mrn, p.blood_group, p.allergies, u.full_name as patient_name, u.avatar_url as patient_avatar, u.phone as patient_phone
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN users u ON p.user_id = u.id
           WHERE a.doctor_id = ? AND a.scheduled_date = ?
           ORDER BY a.scheduled_time ASC""",
        (doctor_id, today_str)
    )

    # Count waiting, in-progress, and completed
    patients_waiting = sum(1 for a in today_appts if a["status"] in ("scheduled", "confirmed"))
    in_progress_count = sum(1 for a in today_appts if a["status"] == "in_progress")
    completed_today = sum(1 for a in today_appts if a["status"] == "completed")
    no_shows_today = sum(1 for a in today_appts if a["status"] == "no_show")

    # Upcoming future appointments (next 7 days)
    upcoming_appts = query_all(
        """SELECT a.*, p.mrn, u.full_name as patient_name
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN users u ON p.user_id = u.id
           WHERE a.doctor_id = ? AND a.scheduled_date > ? AND a.status IN ('scheduled', 'confirmed')
           ORDER BY a.scheduled_date ASC, a.scheduled_time ASC LIMIT 10""",
        (doctor_id, today_str)
    )

    # Workload percentage
    max_cap = doctor["max_daily_patients"] or 20
    workload_pct = min(round((len(today_appts) / max_cap) * 100, 1), 100.0)

    # Attach live queue calculations to today's appointments
    for a in today_appts:
        q = HospitalAIService.calculate_patient_queue_status(a["id"])
        a["queue_position"] = q.get("queue_position", 1)
        a["patients_ahead"] = q.get("patients_ahead", 0)
        a["estimated_wait_time_minutes"] = q.get("estimated_wait_time_minutes", 10)
        a["consultation_status"] = q.get("consultation_status", a["status"])

    # Workload balancing insights
    workload_insights = HospitalAIService.get_workload_balancing_insights()

    # Notifications
    notifications = query_all(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (current_user["id"],)
    )

    return {
        "doctor_profile": doctor,
        "is_available": bool(doctor["is_available"]),
        "today_stats": {
            "total_today": len(today_appts),
            "patients_waiting": patients_waiting,
            "in_progress": in_progress_count,
            "completed": completed_today,
            "no_shows": no_shows_today,
            "workload_percentage": workload_pct,
            "max_daily_capacity": max_cap
        },
        "today_appointments": today_appts,
        "upcoming_appointments": upcoming_appts,
        "workload_insights": workload_insights,
        "notifications": notifications
    }

@router.get("/workload-balancing")
def get_workload_balancing(current_user: dict = Depends(require_doctor)):
    return HospitalAIService.get_workload_balancing_insights()

@router.get("/availability")
def get_doctor_availability(current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    schedules = query_all(
        "SELECT * FROM doctor_availability WHERE doctor_id = ? ORDER BY day_of_week ASC",
        (doctor_id,)
    )
    leaves = query_all(
        "SELECT * FROM doctor_leaves_blocks WHERE doctor_id = ? ORDER BY start_datetime DESC",
        (doctor_id,)
    )
    doc = query_one("SELECT is_available, consultation_modes FROM doctors WHERE id = ?", (doctor_id,))
    return {
        "is_available": bool(doc["is_available"]),
        "consultation_modes": doc["consultation_modes"],
        "weekly_schedules": schedules,
        "leaves_and_blocks": leaves
    }

@router.put("/availability")
def update_doctor_availability(req: DoctorAvailabilityUpdateRequest, request: Request, current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    # Replace existing schedule configs
    execute_update("DELETE FROM doctor_availability WHERE doctor_id = ?", (doctor_id,))
    for sc in req.schedules:
        execute_insert(
            """INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes,
                                              break_start, break_end, emergency_slots_enabled, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doctor_id, sc.day_of_week, sc.start_time, sc.end_time, sc.slot_duration_minutes,
                sc.break_start, sc.break_end, 1 if sc.emergency_slots_enabled else 0, 1 if sc.is_active else 0
            )
        )
    log_audit(current_user["id"], "UPDATE_AVAILABILITY", "DOCTOR", str(doctor_id), {}, request.client.host if request.client else "127.0.0.1")
    return {"status": "success", "message": "Clinical schedule updated successfully."}

@router.post("/leaves")
def create_doctor_leave(req: DoctorLeaveCreateRequest, request: Request, current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    l_id = execute_insert(
        """INSERT INTO doctor_leaves_blocks (doctor_id, start_datetime, end_datetime, reason, block_type)
           VALUES (?, ?, ?, ?, ?)""",
        (doctor_id, req.start_datetime, req.end_datetime, req.reason, req.block_type)
    )
    log_audit(current_user["id"], "CREATE_LEAVE_BLOCK", "DOCTOR", str(doctor_id), {"start": req.start_datetime, "end": req.end_datetime, "reason": req.reason}, request.client.host if request.client else "127.0.0.1")
    return {"status": "success", "message": "Leave / Unavailability block recorded.", "leave_id": l_id}

@router.delete("/leaves/{leave_id}")
def delete_doctor_leave(leave_id: int, current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    execute_update("DELETE FROM doctor_leaves_blocks WHERE id = ? AND doctor_id = ?", (leave_id, doctor_id))
    return {"status": "success", "message": "Leave block removed."}

@router.put("/toggle-availability")
def toggle_availability(request: Request, current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    doc = query_one("SELECT is_available FROM doctors WHERE id = ?", (doctor_id,))
    new_state = 0 if doc["is_available"] else 1
    execute_update("UPDATE doctors SET is_available = ? WHERE id = ?", (new_state, doctor_id))
    log_audit(current_user["id"], "TOGGLE_AVAILABILITY", "DOCTOR", str(doctor_id), {"is_available": new_state}, request.client.host if request.client else "127.0.0.1")
    return {"status": "success", "is_available": bool(new_state), "message": f"Doctor availability set to {'Active' if new_state else 'Off-Duty'}."}

@router.get("/appointments")
def get_doctor_appointments(current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    appts = query_all(
        """SELECT a.*, p.mrn, p.blood_group, p.allergies, p.chronic_conditions,
                  u.full_name as patient_name, u.avatar_url as patient_avatar, u.phone as patient_phone,
                  (SELECT cn.diagnosis FROM consultation_notes cn WHERE cn.appointment_id = a.id) as diagnosis
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN users u ON p.user_id = u.id
           WHERE a.doctor_id = ?
           ORDER BY a.scheduled_date DESC, a.scheduled_time ASC""",
        (doctor_id,)
    )
    return appts

@router.put("/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: int, req: AppointmentStatusUpdateRequest, request: Request, current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    appt = query_one("SELECT * FROM appointments WHERE id = ? AND doctor_id = ?", (appointment_id, doctor_id))
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found or unauthorized.")

    valid_statuses = ["confirmed", "in_progress", "completed", "cancelled", "no_show"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    now_iso = datetime.now(timezone.utc).isoformat()
    execute_update("UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?", (req.status, now_iso, appointment_id))

    execute_insert(
        """INSERT INTO appointment_history (appointment_id, previous_status, new_status, changed_by_user_id, notes, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (appointment_id, appt["status"], req.status, current_user["id"], req.notes or f"Status updated to {req.status} by clinician.", now_iso)
    )

    # Notify patient of status shift
    patient = query_one("SELECT user_id FROM patients WHERE id = ?", (appt["patient_id"],))
    if patient:
        execute_insert(
            """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
               VALUES (?, 'Appointment Status Update', ?, 'appointment_confirmation', 0, '/appointments', ?)""",
            (
                patient["user_id"],
                f"Your appointment #{appt['appointment_number']} is now marked as {req.status.replace('_', ' ').capitalize()}.",
                now_iso
            )
        )

    log_audit(current_user["id"], "UPDATE_APPT_STATUS", "APPOINTMENT", str(appointment_id), {"previous": appt["status"], "new": req.status}, request.client.host if request.client else "127.0.0.1")
    return {"status": "success", "message": f"Appointment status updated to {req.status}."}

@router.get("/patient-profile/{patient_id}")
def get_authorized_patient_profile(patient_id: int, current_user: dict = Depends(require_doctor)):
    patient = query_one(
        """SELECT p.*, u.full_name, u.email, u.phone, u.avatar_url
           FROM patients p JOIN users u ON p.user_id = u.id WHERE p.id = ?""",
        (patient_id,)
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    past_appts = query_all(
        """SELECT a.*, dep.name as department_name, u.full_name as doctor_name
           FROM appointments a
           JOIN departments dep ON a.department_id = dep.id
           JOIN doctors d ON a.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           WHERE a.patient_id = ? ORDER BY a.scheduled_date DESC""",
        (patient_id,)
    )

    medical_records = query_all(
        "SELECT * FROM medical_records WHERE patient_id = ? ORDER BY record_date DESC",
        (patient_id,)
    )

    reports = query_all(
        "SELECT id, title, report_type, hospital_facility, ordering_doctor, report_date, file_name, file_size, summary FROM health_reports WHERE patient_id = ? ORDER BY report_date DESC",
        (patient_id,)
    )

    prescriptions = query_all(
        """SELECT p.*, u.full_name as doctor_name
           FROM prescriptions p
           JOIN doctors d ON p.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           WHERE p.patient_id = ? ORDER BY p.issued_date DESC""",
        (patient_id,)
    )
    for rx in prescriptions:
        if rx["medications_json"]:
            rx["medications"] = json.loads(rx["medications_json"])

    return {
        "patient": patient,
        "appointments": past_appts,
        "medical_records": medical_records,
        "health_reports": reports,
        "prescriptions": prescriptions
    }

@router.post("/consultation-notes", status_code=status.HTTP_201_CREATED)
def submit_consultation_notes(req: ConsultationNoteCreateRequest, request: Request, current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]
    appt = query_one("SELECT * FROM appointments WHERE id = ? AND doctor_id = ?", (req.appointment_id, doctor_id))
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found or unauthorized clinician.")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Save or update consultation note
    existing_note = query_one("SELECT id FROM consultation_notes WHERE appointment_id = ?", (req.appointment_id,))
    if existing_note:
        execute_update(
            """UPDATE consultation_notes
               SET symptoms = ?, clinical_notes = ?, diagnosis = ?, follow_up_date = ?, instructions = ?, updated_at = ?
               WHERE id = ?""",
            (req.symptoms, req.clinical_notes, req.diagnosis, req.follow_up_date, req.instructions, now_iso, existing_note["id"])
        )
        note_id = existing_note["id"]
    else:
        note_id = execute_insert(
            """INSERT INTO consultation_notes (appointment_id, doctor_id, patient_id, symptoms, clinical_notes,
                                             diagnosis, follow_up_date, instructions, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (req.appointment_id, doctor_id, appt["patient_id"], req.symptoms, req.clinical_notes, req.diagnosis, req.follow_up_date, req.instructions, now_iso, now_iso)
        )

    # Save prescription if provided
    rx_id = None
    if req.prescriptions:
        rx_json = json.dumps([p.dict() for p in req.prescriptions])
        rx_id = execute_insert(
            """INSERT INTO prescriptions (appointment_id, patient_id, doctor_id, medications_json, instructions, issued_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (req.appointment_id, appt["patient_id"], doctor_id, rx_json, req.instructions, datetime.now().strftime("%Y-%m-%d"))
        )

    # Record diagnosis into official medical_records table
    execute_insert(
        """INSERT INTO medical_records (patient_id, doctor_id, appointment_id, record_type, title, description, record_date, created_at)
           VALUES (?, ?, ?, 'Diagnosis', ?, ?, ?, ?)""",
        (appt["patient_id"], doctor_id, req.appointment_id, f"Diagnosis: {req.diagnosis}", req.clinical_notes, datetime.now().strftime("%Y-%m-%d"), now_iso)
    )

    # Mark appointment as completed
    execute_update("UPDATE appointments SET status = 'completed', updated_at = ? WHERE id = ?", (now_iso, req.appointment_id))

    execute_insert(
        """INSERT INTO appointment_history (appointment_id, previous_status, new_status, changed_by_user_id, notes, timestamp)
           VALUES (?, ?, 'completed', ?, 'Consultation concluded and clinical notes signed by physician.', ?)""",
        (req.appointment_id, appt["status"], current_user["id"], now_iso)
    )

    # Notify patient
    patient = query_one("SELECT user_id FROM patients WHERE id = ?", (appt["patient_id"],))
    if patient:
        execute_insert(
            """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
               VALUES (?, 'Consultation Notes Ready', ?, 'appointment_confirmation', 0, '/medical-history', ?)""",
            (patient["user_id"], f"Clinical notes and prescription for appointment #{appt['appointment_number']} have been finalized.", now_iso)
        )

    log_audit(current_user["id"], "SUBMIT_CONSULTATION_NOTES", "CONSULTATION", str(note_id), {"diagnosis": req.diagnosis, "rx_count": len(req.prescriptions or [])}, request.client.host if request.client else "127.0.0.1")

    return {
        "status": "success",
        "message": "Consultation documentation and prescription successfully filed.",
        "note_id": note_id,
        "prescription_id": rx_id
    }

@router.get("/workload-metrics")
def get_doctor_workload_metrics(current_user: dict = Depends(require_doctor)):
    doctor_id = current_user["doctor_id"]

    all_appts = query_all("SELECT * FROM appointments WHERE doctor_id = ?", (doctor_id,))
    total_appts = len(all_appts)
    completed = sum(1 for a in all_appts if a["status"] == "completed")
    no_shows = sum(1 for a in all_appts if a["status"] == "no_show")
    cancelled = sum(1 for a in all_appts if a["status"] == "cancelled")

    no_show_rate = round((no_shows / max(total_appts, 1)) * 100, 1)
    cancellation_rate = round((cancelled / max(total_appts, 1)) * 100, 1)

    # Appointments per hour distribution
    hour_distribution = {}
    for a in all_appts:
        h = a["scheduled_time"].split(":")[0] + ":00"
        hour_distribution[h] = hour_distribution.get(h, 0) + 1

    peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else "11:00"

    doc = query_one("SELECT max_daily_patients FROM doctors WHERE id = ?", (doctor_id,))
    max_cap = doc["max_daily_patients"] or 20
    today_count = query_one(
        "SELECT COUNT(*) as cnt FROM appointments WHERE doctor_id = ? AND scheduled_date = DATE('now') AND status NOT IN ('cancelled')",
        (doctor_id,)
    )["cnt"]
    utilization = round((today_count / max_cap) * 100, 1)

    return {
        "total_appointments_all_time": total_appts,
        "completed_count": completed,
        "no_show_rate_percent": no_show_rate,
        "cancellation_rate_percent": cancellation_rate,
        "average_consultation_duration_minutes": 26.5,
        "utilization_percentage": min(utilization, 100.0),
        "peak_consultation_hour": peak_hour,
        "hourly_distribution": hour_distribution
    }

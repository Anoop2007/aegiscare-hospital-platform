from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import secrets
from ..database import query_all, query_one, execute_insert, execute_update
from ..auth import get_current_user, log_audit
from ..schemas import (
    SmartDoctorRecommendationRequest, WaitlistJoinRequest,
    WaitlistClaimRequest, QueueStatusUpdateRequest
)
from ..ai_service import HospitalAIService

router = APIRouter(prefix="/appointments", tags=["Appointment Optimization"])

@router.get("/slots")
def get_doctor_slots(
    doctor_id: int,
    date_str: str, # 'YYYY-MM-DD'
    current_user: dict = Depends(get_current_user)
):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    weekday = target_date.weekday()

    avail = query_one(
        "SELECT * FROM doctor_availability WHERE doctor_id = ? AND day_of_week = ? AND is_active = 1",
        (doctor_id, weekday)
    )
    if not avail:
        return {
            "doctor_id": doctor_id,
            "date": date_str,
            "is_working_day": False,
            "slots": [],
            "message": "Doctor does not have scheduled clinic hours on this day."
        }

    leaves = query_all(
        "SELECT * FROM doctor_leaves_blocks WHERE doctor_id = ? AND ? BETWEEN DATE(start_datetime) AND DATE(end_datetime)",
        (doctor_id, date_str)
    )
    if leaves:
        return {
            "doctor_id": doctor_id,
            "date": date_str,
            "is_working_day": False,
            "slots": [],
            "message": f"Doctor is unavailable due to: {leaves[0]['reason']}"
        }

    booked = query_all(
        "SELECT scheduled_time, status, consultation_type FROM appointments WHERE doctor_id = ? AND scheduled_date = ? AND status NOT IN ('cancelled')",
        (doctor_id, date_str)
    )
    booked_map = {b["scheduled_time"]: b for b in booked}

    start_h, start_m = map(int, avail["start_time"].split(":"))
    end_h, end_m = map(int, avail["end_time"].split(":"))
    slot_dur = avail["slot_duration_minutes"] or 30

    break_start_h = int(avail["break_start"].split(":")[0]) if avail["break_start"] else -1

    current_dt = target_date.replace(hour=start_h, minute=start_m, second=0)
    end_dt = target_date.replace(hour=end_h, minute=end_m, second=0)

    slots = []
    while current_dt < end_dt:
        time_str = current_dt.strftime("%H:%M")
        is_break = (current_dt.hour == break_start_h)
        is_booked = time_str in booked_map

        slot_status = "booked" if is_booked else ("break" if is_break else "available")
        slots.append({
            "time": time_str,
            "status": slot_status,
            "is_available": (slot_status == "available"),
            "display_time": current_dt.strftime("%I:%M %p")
        })
        current_dt += timedelta(minutes=slot_dur)

    return {
        "doctor_id": doctor_id,
        "date": date_str,
        "is_working_day": True,
        "slot_duration_minutes": slot_dur,
        "emergency_slots_enabled": bool(avail["emergency_slots_enabled"]),
        "total_slots": len(slots),
        "available_slots_count": sum(1 for s in slots if s["is_available"]),
        "slots": slots
    }

@router.post("/ai-recommend")
def recommend_best_doctor_and_slot(req: SmartDoctorRecommendationRequest, current_user: dict = Depends(get_current_user)):
    pref_time = req.preferred_time_of_day or req.preferred_time_range or "any"
    recommendations = HospitalAIService.get_smart_doctor_recommendations(
        department_id=req.department_id,
        specialty=req.specialty,
        urgency=req.urgency,
        preferred_date=req.preferred_date,
        preferred_time_of_day=pref_time,
        preferred_doctor_id=req.preferred_doctor_id,
        allocation_strategy=req.allocation_strategy,
        consultation_type=req.consultation_type,
        reason_for_visit=req.reason_for_visit
    )
    return {
        "urgency_level": req.urgency,
        "consultation_type": req.consultation_type,
        "allocation_strategy": req.allocation_strategy,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
        "disclaimer": "Informational scheduling optimization based on operational hospital queue metrics and physician availability. This does not constitute medical triage or clinical diagnosis."
    }

@router.get("/{appointment_id}/queue-status")
def get_appointment_queue_status(appointment_id: int, current_user: dict = Depends(get_current_user)):
    status_data = HospitalAIService.calculate_patient_queue_status(appointment_id)
    return status_data

@router.put("/{appointment_id}/queue-status")
def update_appointment_queue_status(appointment_id: int, req: QueueStatusUpdateRequest, request: Request, current_user: dict = Depends(get_current_user)):
    now_iso = datetime.now(timezone.utc).isoformat()
    now_time = datetime.now().strftime("%H:%M")
    action = req.action or req.queue_status or ""

    if action in ("mark_delay", "delayed") or (req.delay_minutes and req.delay_minutes > 0):
        d_min = req.delay_minutes or 10
        execute_update(
            "UPDATE appointments SET delay_minutes = COALESCE(delay_minutes, 0) + ?, updated_at = ? WHERE id = ?",
            (d_min, now_iso, appointment_id)
        )
        msg = f"Recorded +{d_min}m delay. Patient queue wait-times updated."
    elif action in ("check_in", "checked_in"):
        execute_update(
            "UPDATE appointments SET check_in_time = ?, updated_at = ? WHERE id = ?",
            (now_time, now_iso, appointment_id)
        )
        msg = "Patient checked in successfully."
    elif action in ("start_consult", "in_progress"):
        execute_update(
            "UPDATE appointments SET status = 'in_progress', consultation_start_time = ?, updated_at = ? WHERE id = ?",
            (now_time, now_iso, appointment_id)
        )
        msg = "Consultation started and marked in-progress."
    elif action in ("complete", "completed"):
        execute_update(
            "UPDATE appointments SET status = 'completed', updated_at = ? WHERE id = ?",
            (now_iso, appointment_id)
        )
        msg = "Consultation completed."
    else:
        execute_update(
            "UPDATE appointments SET updated_at = ? WHERE id = ?",
            (now_iso, appointment_id)
        )
        msg = "Queue status updated."

    log_audit(current_user["id"], "UPDATE_QUEUE_STATUS", "APPOINTMENT", str(appointment_id), {"action": action, "delay": req.delay_minutes})
    return {"status": "success", "message": msg}

@router.post("/waitlist", status_code=status.HTTP_201_CREATED)
def join_waitlist(req: WaitlistJoinRequest, request: Request, current_user: dict = Depends(get_current_user)):
    patient_id = current_user.get("patient_id")
    if not patient_id:
        p = query_one("SELECT id FROM patients WHERE user_id = ?", (current_user["id"],))
        if not p:
            raise HTTPException(status_code=400, detail="Only registered patients can join the waitlist.")
        patient_id = p["id"]

    pref_date = req.preferred_date or datetime.now().strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()
    w_id = execute_insert(
        """INSERT INTO waitlist (patient_id, department_id, doctor_id, preferred_date, preferred_time_range,
                               allocation_strategy, priority, reason_for_visit, consultation_type, status,
                               created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
        (
            patient_id, req.department_id, req.doctor_id, pref_date, req.preferred_time_range,
            req.allocation_strategy, req.priority, req.reason_for_visit, req.consultation_type,
            now_iso, now_iso
        )
    )

    execute_insert(
        """INSERT INTO waitlist_history (waitlist_id, action, notes, timestamp)
           VALUES (?, 'joined', 'Patient registered for standby waitlist allocation.', ?)""",
        (w_id, now_iso)
    )

    priority_scores = {
        "emergency": 98,
        "urgent": 88,
        "priority": 72,
        "routine": 50
    }
    score = priority_scores.get(req.priority, 50)

    return {
        "status": "success",
        "message": "Successfully registered on the hospital standby waitlist.",
        "waitlist_id": w_id,
        "priority_score": score
    }

@router.get("/waitlist")
def get_waitlist(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    if role == "patient":
        patient_id = current_user.get("patient_id")
        sql = """
            SELECT w.*, dep.name as department_name, u.full_name as doctor_name
            FROM waitlist w
            JOIN departments dep ON w.department_id = dep.id
            LEFT JOIN doctors d ON w.doctor_id = d.id
            LEFT JOIN users u ON d.user_id = u.id
            WHERE w.patient_id = ?
            ORDER BY w.created_at DESC
        """
        return query_all(sql, (patient_id,))
    else:
        # Doctor or Admin: all active waitlist entries
        sql = """
            SELECT w.*, dep.name as department_name, u_doc.full_name as doctor_name,
                   u_pat.full_name as patient_name, p.mrn as patient_mrn
            FROM waitlist w
            JOIN departments dep ON w.department_id = dep.id
            JOIN patients p ON w.patient_id = p.id
            JOIN users u_pat ON p.user_id = u_pat.id
            LEFT JOIN doctors d ON w.doctor_id = d.id
            LEFT JOIN users u_doc ON d.user_id = u_doc.id
            ORDER BY w.created_at DESC LIMIT 50
        """
        return query_all(sql)

@router.post("/waitlist/{waitlist_id}/claim")
def claim_offered_waitlist_slot(waitlist_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    w = query_one("SELECT * FROM waitlist WHERE id = ?", (waitlist_id,))
    if not w:
        raise HTTPException(status_code=404, detail="Waitlist entry not found.")

    if w["status"] != "offered" or not w["offered_appointment_id"]:
        raise HTTPException(status_code=400, detail="No active slot has been offered for this waitlist entry yet.")

    appt = query_one("SELECT * FROM appointments WHERE id = ?", (w["offered_appointment_id"],))
    now_iso = datetime.now(timezone.utc).isoformat()

    # Create newly confirmed appointment for waitlisted patient
    rand_num = secrets.randbelow(9000) + 1000
    appt_num = f"AC-2026-{rand_num}"

    new_appt_id = execute_insert(
        """INSERT INTO appointments (appointment_number, patient_id, doctor_id, department_id, scheduled_date,
                                   scheduled_time, duration_minutes, consultation_type, status, priority,
                                   reason_for_visit, estimated_wait_time, meeting_link, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 30, ?, 'confirmed', ?, ?, 10, 'https://meet.aegiscare.health/room/' || ?, ?, ?)""",
        (
            appt_num, w["patient_id"], appt["doctor_id"], w["department_id"], appt["scheduled_date"],
            appt["scheduled_time"], w["consultation_type"], w["priority"], w["reason_for_visit"],
            appt_num, now_iso, now_iso
        )
    )

    execute_update("UPDATE waitlist SET status = 'claimed', updated_at = ? WHERE id = ?", (now_iso, waitlist_id))
    execute_insert(
        """INSERT INTO waitlist_history (waitlist_id, appointment_id, action, notes, timestamp)
           VALUES (?, ?, 'claimed', 'Patient accepted and confirmed reserved appointment slot.', ?)""",
        (waitlist_id, new_appt_id, now_iso)
    )

    log_audit(current_user["id"], "CLAIM_WAITLIST_SLOT", "WAITLIST", str(waitlist_id), {"new_appointment_number": appt_num})

    return {
        "status": "success",
        "message": "Waitlist slot claimed and appointment confirmed!",
        "appointment_id": new_appt_id,
        "appointment_number": appt_num,
        "scheduled_date": appt["scheduled_date"],
        "scheduled_time": appt["scheduled_time"]
    }

@router.delete("/waitlist/{waitlist_id}")
def cancel_waitlist(waitlist_id: int, current_user: dict = Depends(get_current_user)):
    now_iso = datetime.now(timezone.utc).isoformat()
    execute_update("UPDATE waitlist SET status = 'cancelled', updated_at = ? WHERE id = ?", (now_iso, waitlist_id))
    execute_insert(
        """INSERT INTO waitlist_history (waitlist_id, action, notes, timestamp)
           VALUES (?, 'cancelled', 'Waitlist standby request cancelled.', ?)""",
        (waitlist_id, now_iso)
    )
    return {"status": "success", "message": "Waitlist request removed."}

@router.get("/{appointment_id}/telehealth-session")
def get_telehealth_session(appointment_id: int, current_user: dict = Depends(get_current_user)):
    appt = query_one("""
        SELECT a.*, d.specialization, d.room_number,
               u_doc.full_name as doctor_name, u_doc.avatar_url as doctor_avatar,
               u_pat.full_name as patient_name, u_pat.avatar_url as patient_avatar,
               p.mrn as patient_mrn, dep.name as department_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u_doc ON d.user_id = u_doc.id
        JOIN patients p ON a.patient_id = p.id
        JOIN users u_pat ON p.user_id = u_pat.id
        JOIN departments dep ON a.department_id = dep.id
        WHERE a.id = ?
    """, (appointment_id,))
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    user_id = current_user["id"]
    role = current_user["role"]

    pat_user_id = query_one("SELECT user_id FROM patients WHERE id = ?", (appt["patient_id"],))["user_id"]
    doc_user_id = query_one("SELECT user_id FROM doctors WHERE id = ?", (appt["doctor_id"],))["user_id"]

    if role != "admin" and user_id not in (pat_user_id, doc_user_id):
        raise HTTPException(status_code=403, detail="Unauthorized access to this telehealth room.")

    return {
        "session_id": f"TEL-{appt['appointment_number']}",
        "room_name": f"Room {appt['appointment_number']}",
        "appointment": appt,
        "is_doctor": (role == "doctor"),
        "telehealth_status": "connected",
        "consultation_mode": appt["consultation_type"],
        "meeting_link": appt["meeting_link"]
    }

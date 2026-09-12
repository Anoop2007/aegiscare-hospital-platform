from datetime import datetime, timedelta, timezone
import json
from .database import get_db, query_one, query_all, execute_insert, execute_update
from .auth import hash_password
from .seed_indian_data import seed_indian_entities

def seed_enhancements_if_needed():
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 0. Seed all 22 Indian Departments, 12 Hospitals, and 28 Indian Doctors
    try:
        seed_indian_entities()
    except Exception as e:
        print(f"Warning during seed_indian_entities: {e}")

    # 1. Check if waitlist needs seeding
    w_count = query_one("SELECT count(*) as cnt FROM waitlist")
    if w_count and w_count["cnt"] == 0:
        docs = {d["specialization"]: d["id"] for d in query_all("SELECT id, specialization FROM doctors")}
        pats = {p["mrn"]: p["id"] for p in query_all("SELECT id, mrn FROM patients")}
        card_id = query_one("SELECT id FROM departments WHERE code = 'CARD'")
        neur_id = query_one("SELECT id FROM departments WHERE code = 'NEUR'")

        jane_id = pats.get("AC-MRN-90412")
        robert_id = pats.get("AC-MRN-88120")
        emily_id = pats.get("AC-MRN-77341")

        if emily_id and card_id:
            execute_insert(
                """INSERT INTO waitlist (patient_id, department_id, doctor_id, preferred_date, preferred_time_range,
                                       allocation_strategy, priority, reason_for_visit, consultation_type, status,
                                       created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'any', 'fastest_available', 'urgent', 'Urgent standby for arrhythmia assessment', 'In-Person', 'active', ?, ?)""",
                (emily_id, card_id["id"], docs.get('Interventional Cardiology & Heart Failure'), today_str, now_iso, now_iso)
            )
        if robert_id and card_id:
            execute_insert(
                """INSERT INTO waitlist (patient_id, department_id, doctor_id, preferred_date, preferred_time_range,
                                       allocation_strategy, priority, reason_for_visit, consultation_type, status,
                                       created_at, updated_at)
                   VALUES (?, ?, NULL, ?, 'morning', 'best_available', 'routine', 'Standby for morning cardiology evaluation', 'In-Person', 'active', ?, ?)""",
                (robert_id, card_id["id"], today_str, now_iso, now_iso)
            )
        if jane_id and neur_id:
            execute_insert(
                """INSERT INTO waitlist (patient_id, department_id, doctor_id, preferred_date, preferred_time_range,
                                       allocation_strategy, priority, reason_for_visit, consultation_type, status,
                                       created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'afternoon', 'preferred_doctor', 'routine', 'Standby for migraine follow-up consultation', 'Video', 'active', ?, ?)""",
                (jane_id, neur_id["id"], docs.get('Neurology & Neurovascular Disorders'), today_str, now_iso, now_iso)
            )
        print("Waitlist records successfully seeded.")

    # 2. Ensure today's appointments have live queue positions
    execute_update(
        """UPDATE appointments
           SET queue_position = 2, check_in_time = ?, estimated_wait_time = 14, delay_minutes = 4
           WHERE appointment_number = 'AC-2026-8941'""",
        ((datetime.now() - timedelta(minutes=15)).strftime("%H:%M"),)
    )
    execute_update(
        """UPDATE appointments
           SET queue_position = 1, check_in_time = ?, consultation_start_time = ?, estimated_wait_time = 0, delay_minutes = 0
           WHERE appointment_number = 'AC-2026-8801'""",
        ((datetime.now() - timedelta(minutes=30)).strftime("%H:%M"),
         (datetime.now() - timedelta(minutes=10)).strftime("%H:%M"))
    )

    # 3. Check historical appointments for AI forecasting
    past_count = query_one("SELECT count(*) as cnt FROM appointments WHERE scheduled_date < ?", (today_str,))
    if past_count and past_count["cnt"] < 10:
        print("Seeding multi-day historical data for operational AI forecasting engine...")
        depts = [d["id"] for d in query_all("SELECT id FROM departments")]
        docs = [d["id"] for d in query_all("SELECT id FROM doctors")]
        pats = [p["id"] for p in query_all("SELECT id FROM patients")]

        if depts and docs and pats:
            statuses = ["completed", "completed", "completed", "completed", "cancelled", "no_show"]
            times = ["09:00", "09:30", "10:30", "11:00", "11:30", "14:00", "14:30", "15:30", "16:00"]
            import random
            random.seed(42)

            for day_offset in range(1, 14):
                hist_date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                for i in range(3):
                    doc_idx = (day_offset + i) % len(docs)
                    pat_idx = (day_offset + i) % len(pats)
                    dept_idx = (day_offset + i) % len(depts)
                    stat = statuses[(day_offset * 2 + i) % len(statuses)]
                    t = times[(day_offset + i * 2) % len(times)]
                    appt_num = f"AC-HIST-{day_offset:02d}{i:02d}"

                    # Insert if doesn't exist
                    existing = query_one("SELECT id FROM appointments WHERE appointment_number = ?", (appt_num,))
                    if not existing:
                        execute_insert(
                            """INSERT INTO appointments (appointment_number, patient_id, doctor_id, department_id, scheduled_date,
                                                       scheduled_time, duration_minutes, consultation_type, status, priority,
                                                       reason_for_visit, estimated_wait_time, meeting_link, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, 30, 'In-Person', ?, 'routine', 'Historical outpatient clinical visit', 10,
                                       'https://meet.aegiscare.health/room/' || ?, ?, ?)""",
                            (appt_num, pats[pat_idx], docs[doc_idx], depts[dept_idx], hist_date, t, stat, appt_num, now_iso, now_iso)
                        )
            print("Historical appointments successfully populated for operational analytics.")

def seed_database():
    # Check if already seeded
    existing_admin = query_one("SELECT id FROM users WHERE email = 'admin@aegiscare.health'")
    if existing_admin:
        seed_enhancements_if_needed()
        return  # Base database already populated

    print("Seeding AegisCare Clinical Platform database with realistic healthcare data...")

    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # 1. Seed Departments
    departments_data = [
        ("Cardiology & Vascular Medicine", "CARD", "Comprehensive adult cardiac diagnostics, interventional catheterization, and rhythm management.", "Floor 3 - East Wing", "301"),
        ("Neurology & Stroke Center", "NEUR", "Advanced diagnostic imaging, neuromuscular disorders, and comprehensive stroke intervention.", "Floor 4 - West Wing", "402"),
        ("Orthopedics & Sports Medicine", "ORTH", "Joint replacement, arthroscopy, fracture management, and musculoskeletal rehabilitation.", "Floor 2 - South Wing", "205"),
        ("Pediatrics & Adolescent Care", "PED", "Neonatal care, pediatric subspecialties, immunization, and growth developmental clinics.", "Floor 2 - North Wing", "210"),
        ("Medical Oncology & Hematology", "ONC", "Targeted cancer therapies, clinical hematology, and ambulatory infusion services.", "Floor 5 - Center Wing", "508"),
        ("Internal & Preventive Medicine", "GEN", "Primary care, chronic disease management, and executive preventive health screenings.", "Floor 1 - Outpatient Pavilion", "115"),
    ]
    dept_ids = {}
    for name, code, desc, floor, ext in departments_data:
        d_id = execute_insert(
            """INSERT INTO departments (name, code, description, floor_location, contact_extension, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (name, code, desc, floor, ext, now_iso)
        )
        dept_ids[code] = d_id

    # 2. Seed Users & Profiles
    # Admin
    admin_pw = hash_password("AdminPass@2026")
    admin_uid = execute_insert(
        """INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, is_active, created_at)
           VALUES ('admin@aegiscare.health', ?, 'admin', 'Dr. Alistair Vance, MD (Chief Medical Officer)', '+1 (555) 019-4801', 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=150', 1, ?)""",
        (admin_pw, now_iso)
    )

    # Doctors
    doctors_info = [
        {
            "email": "dr.sharma@aegiscare.health",
            "password": hash_password("DoctorPass@2026"),
            "full_name": "Dr. Priya Sharma, MD, FACC",
            "phone": "+1 (555) 019-5021",
            "avatar": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150",
            "dept_code": "CARD",
            "spec": "Interventional Cardiology & Heart Failure",
            "license": "MD-CARD-78491",
            "exp": 14,
            "fee": 120.0,
            "lang": "English, Hindi, Spanish",
            "bio": "Fellow of the American College of Cardiology. Specializing in preventative cardiology, coronary angiography, and complex arrhythmia management.",
            "room": "Cardiology Suite 312",
            "modes": "In-Person,Video",
            "capacity": 20
        },
        {
            "email": "dr.chen@aegiscare.health",
            "password": hash_password("DoctorPass@2026"),
            "full_name": "Dr. Marcus Chen, MD, PhD",
            "phone": "+1 (555) 019-5022",
            "avatar": "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150",
            "dept_code": "NEUR",
            "spec": "Neurology & Neurovascular Disorders",
            "license": "MD-NEUR-65219",
            "exp": 12,
            "fee": 140.0,
            "lang": "English, Mandarin",
            "bio": "Specialized in migraine management, cerebrovascular prevention, epilepsy management, and neurological EEG evaluations.",
            "room": "Neurology Suite 405",
            "modes": "In-Person,Video",
            "capacity": 18
        },
        {
            "email": "dr.rodriguez@aegiscare.health",
            "password": hash_password("DoctorPass@2026"),
            "full_name": "Dr. Elena Rodriguez, MD",
            "phone": "+1 (555) 019-5023",
            "avatar": "https://images.unsplash.com/photo-1594824813589-79a02ce62eb8?w=150",
            "dept_code": "ORTH",
            "spec": "Orthopedic Surgery & Sports Medicine",
            "license": "MD-ORTH-88402",
            "exp": 10,
            "fee": 115.0,
            "lang": "English, Spanish",
            "bio": "Expert in arthroscopic joint reconstruction, sports injury rehabilitation, and minimally invasive knee and shoulder procedures.",
            "room": "Orthopedics Pavilion 208",
            "modes": "In-Person",
            "capacity": 22
        },
        {
            "email": "dr.patel@aegiscare.health",
            "password": hash_password("DoctorPass@2026"),
            "full_name": "Dr. Aisha Patel, MD, FAAP",
            "phone": "+1 (555) 019-5024",
            "avatar": "https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=150",
            "dept_code": "PED",
            "spec": "General & Adolescent Pediatrics",
            "license": "MD-PED-43901",
            "exp": 9,
            "fee": 90.0,
            "lang": "English, Gujarati",
            "bio": "Dedicated pediatrician focused on developmental milestones, childhood preventative medicine, and pediatric asthma management.",
            "room": "Pediatric Clinic 215",
            "modes": "In-Person,Video",
            "capacity": 25
        },
        {
            "email": "dr.adams@aegiscare.health",
            "password": hash_password("DoctorPass@2026"),
            "full_name": "Dr. Sarah Adams, MD",
            "phone": "+1 (555) 019-5025",
            "avatar": "https://images.unsplash.com/photo-1527613426441-4da17471b66d?w=150",
            "dept_code": "GEN",
            "spec": "Internal & Preventive Medicine",
            "license": "MD-GEN-55198",
            "exp": 8,
            "fee": 75.0,
            "lang": "English",
            "bio": "Providing patient-centered comprehensive primary care, metabolic syndrome treatment, and annual clinical wellness checkups.",
            "room": "Ambulatory Clinic 104",
            "modes": "In-Person,Video",
            "capacity": 24
        }
    ]

    doctor_ids = []
    for doc in doctors_info:
        u_id = execute_insert(
            """INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, is_active, created_at)
               VALUES (?, ?, 'doctor', ?, ?, ?, 1, ?)""",
            (doc["email"], doc["password"], doc["full_name"], doc["phone"], doc["avatar"], now_iso)
        )
        d_id = execute_insert(
            """INSERT INTO doctors (user_id, department_id, specialization, license_number, experience_years,
                                  consultation_fee, languages, bio, branch, is_available, consultation_modes, room_number, max_daily_patients)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Main Campus - Wing A', 1, ?, ?, ?)""",
            (u_id, dept_ids[doc["dept_code"]], doc["spec"], doc["license"], doc["exp"], doc["fee"], doc["lang"], doc["bio"], doc["modes"], doc["room"], doc["capacity"])
        )
        doctor_ids.append(d_id)

        # Set default weekly availability (Monday to Friday, 08:30 to 17:00 with lunch break)
        for day in range(5):  # Mon-Fri
            execute_insert(
                """INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes, break_start, break_end, emergency_slots_enabled, is_active)
                   VALUES (?, ?, '08:30', '17:00', 30, '12:30', '13:30', 1, 1)""",
                (d_id, day)
            )

    # 3. Seed Patients
    patients_info = [
        {
            "email": "patient.jane@aegiscare.health",
            "password": hash_password("PatientPass@2026"),
            "full_name": "Arjun Sharma",
            "phone": "+91 98401 23456",
            "avatar": None,
            "mrn": "CA-MRN-48912",
            "dob": "1992-05-14",
            "gender": "Male",
            "blood": "O+",
            "emergency": "Rajesh Sharma (Brother) - +91 98401 55210",
            "address": "Plot 42, 4th Cross Road, Adyar, Chennai, Tamil Nadu 600020",
            "allergies": "Penicillin, Dust Mites",
            "chronic": "Mild Seasonal Bronchitis"
        },
        {
            "email": "patient.robert@aegiscare.health",
            "password": hash_password("PatientPass@2026"),
            "full_name": "Robert Miller",
            "phone": "+1 (555) 345-6789",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            "mrn": "AC-MRN-88120",
            "dob": "1974-11-03",
            "gender": "Male",
            "blood": "A+",
            "emergency": "Laura Miller (Wife) - +1 (555) 345-6780",
            "address": "1204 Pine Valley Way, Apt 3B",
            "allergies": "Latex, Sulfa drugs",
            "chronic": "Type 2 Diabetes Mellitus"
        },
        {
            "email": "patient.emily@aegiscare.health",
            "password": hash_password("PatientPass@2026"),
            "full_name": "Emily Watson",
            "phone": "+1 (555) 456-7890",
            "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
            "mrn": "AC-MRN-77341",
            "dob": "1995-08-22",
            "gender": "Female",
            "blood": "B+",
            "emergency": "David Watson (Father) - +1 (555) 456-7891",
            "address": "88 Brookside Avenue",
            "allergies": "No known drug allergies (NKDA)",
            "chronic": "Chronic Migraine, Iron Deficiency Anemia"
        }
    ]

    patient_ids = []
    for pat in patients_info:
        u_id = execute_insert(
            """INSERT INTO users (email, password_hash, role, full_name, phone, avatar_url, is_active, created_at)
               VALUES (?, ?, 'patient', ?, ?, ?, 1, ?)""",
            (pat["email"], pat["password"], pat["full_name"], pat["phone"], pat["avatar"], now_iso)
        )
        p_id = execute_insert(
            """INSERT INTO patients (user_id, mrn, date_of_birth, gender, blood_group, emergency_contact, address, allergies, chronic_conditions, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (u_id, pat["mrn"], pat["dob"], pat["gender"], pat["blood"], pat["emergency"], pat["address"], pat["allergies"], pat["chronic"], now_iso)
        )
        patient_ids.append(p_id)

    jane_patient_id = patient_ids[0]
    robert_patient_id = patient_ids[1]
    emily_patient_id = patient_ids[2]

    dr_sharma_id = doctor_ids[0]
    dr_chen_id = doctor_ids[1]
    dr_rodriguez_id = doctor_ids[2]
    dr_adams_id = doctor_ids[4]

    # 4. Seed Appointments across Today, Past, and Upcoming
    appointments_seed = [
        # Today's appointments for Jane Doe
        {
            "num": "AC-2026-8941",
            "pat": jane_patient_id,
            "doc": dr_sharma_id,
            "dept": dept_ids["CARD"],
            "date": today_str,
            "time": "11:00",
            "type": "In-Person",
            "status": "confirmed",
            "priority": "routine",
            "reason": "Quarterly cardiology evaluation and blood pressure medication titration check.",
            "wait": 8
        },
        # Upcoming appointment for Jane Doe
        {
            "num": "AC-2026-9022",
            "pat": jane_patient_id,
            "doc": dr_adams_id,
            "dept": dept_ids["GEN"],
            "date": tomorrow_str,
            "time": "14:30",
            "type": "Video",
            "status": "scheduled",
            "priority": "routine",
            "reason": "Annual comprehensive metabolic health review and prescription renewal.",
            "wait": 5
        },
        # Completed past appointment for Jane Doe
        {
            "num": "AC-2026-7210",
            "pat": jane_patient_id,
            "doc": dr_sharma_id,
            "dept": dept_ids["CARD"],
            "date": last_week_str,
            "time": "10:00",
            "type": "In-Person",
            "status": "completed",
            "priority": "routine",
            "reason": "Follow-up for mild chest heaviness on exertion; 12-lead ECG review.",
            "wait": 12
        },
        # Appointments for Robert Miller
        {
            "num": "AC-2026-8801",
            "pat": robert_patient_id,
            "doc": dr_chen_id,
            "dept": dept_ids["NEUR"],
            "date": today_str,
            "time": "09:30",
            "type": "In-Person",
            "status": "in_progress",
            "priority": "urgent",
            "reason": "Recurrent focal numbness in left fingertips; neurological nerve assessment.",
            "wait": 15
        },
        {
            "num": "AC-2026-8802",
            "pat": robert_patient_id,
            "doc": dr_adams_id,
            "dept": dept_ids["GEN"],
            "date": today_str,
            "time": "15:00",
            "type": "In-Person",
            "status": "scheduled",
            "priority": "follow_up",
            "reason": "Diabetic HbA1c surveillance and foot exam.",
            "wait": 10
        },
        # Emily Watson appointments
        {
            "num": "AC-2026-7731",
            "pat": emily_patient_id,
            "doc": dr_chen_id,
            "dept": dept_ids["NEUR"],
            "date": today_str,
            "time": "11:30",
            "type": "Video",
            "status": "confirmed",
            "priority": "routine",
            "reason": "Intractable migraine follow-up and preventative medication adjustment.",
            "wait": 5
        },
        {
            "num": "AC-2026-7732",
            "pat": emily_patient_id,
            "doc": dr_rodriguez_id,
            "dept": dept_ids["ORTH"],
            "date": yesterday_str,
            "time": "14:00",
            "type": "In-Person",
            "status": "no_show",
            "priority": "routine",
            "reason": "Patellar tendinitis clinical examination.",
            "wait": 0
        }
    ]

    for appt in appointments_seed:
        a_id = execute_insert(
            """INSERT INTO appointments (appointment_number, patient_id, doctor_id, department_id, scheduled_date,
                                       scheduled_time, duration_minutes, consultation_type, status, priority,
                                       reason_for_visit, estimated_wait_time, meeting_link, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 30, ?, ?, ?, ?, ?, 'https://meet.aegiscare.health/room/' || ?, ?, ?)""",
            (appt["num"], appt["pat"], appt["doc"], appt["dept"], appt["date"], appt["time"], appt["type"],
             appt["status"], appt["priority"], appt["reason"], appt["wait"], appt["num"], now_iso, now_iso)
        )
        # Log history
        execute_insert(
            """INSERT INTO appointment_history (appointment_id, previous_status, new_status, notes, timestamp)
               VALUES (?, NULL, ?, 'Appointment initiated in AegisCare Central Scheduling System.', ?)""",
            (a_id, appt["status"], now_iso)
        )

    # 5. Seed Consultation Notes & Prescriptions for the Completed Appointment
    completed_appt = query_one("SELECT id FROM appointments WHERE appointment_number = 'AC-2026-7210'")
    if completed_appt:
        c_id = completed_appt["id"]
        execute_insert(
            """INSERT INTO consultation_notes (appointment_id, doctor_id, patient_id, symptoms, clinical_notes,
                                             diagnosis, follow_up_date, instructions, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                c_id,
                dr_sharma_id,
                jane_patient_id,
                "Exertional dyspnea, mild intermittent palpitations, BP 136/84 mmHg at triage.",
                "Cardiovascular exam reveals normal S1/S2 without murmurs or gallops. 12-lead ECG demonstrated normal sinus rhythm without acute ischemic ST-T changes. Bilateral carotid pulses brisk without bruits.",
                "Stage 1 Essential Hypertension with mild compensatory tachycardia. Rule out structural valvular pathology via echocardiogram.",
                (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "Adhere to low-sodium Dietary Approaches to Stop Hypertension (DASH diet). Maintain home blood pressure log twice weekly. Continue daily 30-minute moderate aerobic walks.",
                last_week_str,
                last_week_str
            )
        )

        rx_items = [
            {"medication_name": "Amlodipine Besylate", "dosage": "5 mg", "frequency": "Once daily in the morning", "duration": "90 days", "instructions": "Take with water with or without food."},
            {"medication_name": "Atorvastatin Calcium", "dosage": "20 mg", "frequency": "Once daily at bedtime", "duration": "90 days", "instructions": "Report any unexpected muscle soreness promptly."}
        ]
        execute_insert(
            """INSERT INTO prescriptions (appointment_id, patient_id, doctor_id, medications_json, instructions, issued_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (c_id, jane_patient_id, dr_sharma_id, json.dumps(rx_items), "Adhere to daily dosing. Do not discontinue without consulting physician.", last_week_str)
        )

    # 6. Seed Realistic Health Reports for Jane Doe
    sample_reports = [
        (
            jane_patient_id,
            "Comprehensive Metabolic Panel & Lipid Profile",
            "Blood Panel",
            "AegisCare Central Pathology Laboratory",
            "Dr. Priya Sharma, MD",
            last_week_str,
            "CMP_LIPID_2026_0911.pdf",
            "1.4 MB",
            "Total Cholesterol: 198 mg/dL (Desirable < 200); HDL: 54 mg/dL; LDL: 118 mg/dL (Borderline High); Triglycerides: 130 mg/dL; Fasting Blood Glucose: 92 mg/dL; Serum Creatinine: 0.88 mg/dL; eGFR: > 90 mL/min/1.73m² (Normal renal clearance).",
            """LABORATORY SPECIMEN REPORT:
Patient: Jane Doe | MRN: AC-MRN-90412 | Ordering Physician: Dr. Priya Sharma, MD
Collected: Fasting Venipuncture | Status: FINAL VERIFIED

[METABOLIC PANEL]
- Sodium: 140 mEq/L (Ref: 135-145) [NORMAL]
- Potassium: 4.2 mEq/L (Ref: 3.5-5.0) [NORMAL]
- Chloride: 102 mEq/L (Ref: 96-106) [NORMAL]
- Bicarbonate: 24 mEq/L (Ref: 22-29) [NORMAL]
- Blood Urea Nitrogen (BUN): 14 mg/dL (Ref: 7-20) [NORMAL]
- Creatinine: 0.88 mg/dL (Ref: 0.60-1.10) [NORMAL]
- Fasting Glucose: 92 mg/dL (Ref: 70-99) [NORMAL]

[LIPID FRACTIONATION]
- Total Cholesterol: 198 mg/dL (Desirable: <200) [BORDERLINE DESIRABLE]
- High-Density Lipoprotein (HDL): 54 mg/dL (Optimal: >50) [NORMAL]
- Low-Density Lipoprotein (LDL-C): 118 mg/dL (Optimal: <100) [MILD ELEVATION]
- Triglycerides: 130 mg/dL (Normal: <150) [NORMAL]

CLINICAL IMPRESSION:
Mild borderline LDL elevation. Renal, hepatic, and glycemic markers within reference bounds.
Verified by: Dr. Catherine Hayes, MD, Chief Pathologist."""
        ),
        (
            jane_patient_id,
            "12-Lead Diagnostic Electrocardiogram (ECG)",
            "Cardiology/ECG",
            "AegisCare Non-Invasive Cardiovascular Center",
            "Dr. Priya Sharma, MD",
            last_week_str,
            "ECG_12LEAD_7210.pdf",
            "840 KB",
            "Normal Sinus Rhythm at 72 bpm. PR Interval: 154 ms. QRS Duration: 86 ms. QTc: 418 ms. Axis: +48 degrees. No diagnostic ST segment elevation or pathological Q waves. No acute ischemic pattern identified.",
            """ELECTROCARDIOGRAM DIAGNOSTIC REPORT:
Facility: AegisCare Heart Institute | Department of Electrophysiology
Lead Configuration: Standard 12-Lead Limb & Precordial (Mason-Likar)

MEASURED PARAMETERS:
- Heart Rate: 72 bpm (Regular)
- Rhythm: Normal Sinus Rhythm (P Waves upright in I, II, aVF)
- PR Interval: 154 ms (Ref: 120-200 ms)
- QRS Duration: 86 ms (Ref: <100 ms)
- QT / QTc: 390 / 418 ms (Bazett formula, within normal limits)
- P-R-T Axes: 52° / 48° / 42°

FINDINGS:
1. Normal sinus rhythm with physiological respiratory variation.
2. Normal ventricular conduction without bundle branch block.
3. No pathological Q waves in inferior (II, III, aVF) or anterior (V1-V4) leads.
4. Stable ST segments; no signs of active myocardial ischemia or strain pattern.

OVERALL INTERPRETATION:
Normal resting 12-lead ECG. Compatible with age and baseline demographic profile.
Over-read by: Dr. Priya Sharma, MD, FACC."""
        ),
        (
            jane_patient_id,
            "Contrast-Enhanced Cranial MRI (Brain)",
            "Radiology/MRI",
            "AegisCare Advanced Diagnostic Imaging Center",
            "Dr. Marcus Chen, MD",
            (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "MRI_BRAIN_CONTRAST.pdf",
            "3.8 MB",
            "Multiplanar T1, T2, FLAIR, and DWI sequences demonstrate normal brain parenchyma. No acute intracranial hemorrhage, territorial infarction, or mass effect. Ventricles and sulci appropriate for age.",
            """DIAGNOSTIC RADIOLOGY REPORT:
Examination: High-Resolution MRI Brain with and without IV Gadolinium
Magnet Strength: 3.0 Tesla Multi-Channel Head Coil

TECHNIQUE:
Axial T1, T2, T2-FLAIR, Sagittal T1, Coronal 3D CISS, and Diffusion Weighted Imaging (DWI) with apparent diffusion coefficient (ADC) mapping. Post-contrast axial and coronal T1 sequences following IV administration of 10 mL gadobutrol.

IMPRESSION:
1. No evidence of acute or subacute territorial stroke, focal diffusion restriction, or intracranial hemorrhage.
2. Ventricular system, basal cisterns, and cerebral sulci maintain normal caliber for age without hydrocephalus.
3. Post-contrast sequences reveal symmetric parenchymal enhancement without abnormal ring-enhancing lesions or leptomeningeal thickening.
4. Paranasal sinuses and mastoid air cells are well-aerated.

CONCLUSION: Unremarkable 3.0T Cranial Magnetic Resonance Imaging.
Signed: Dr. Gregory Ross, MD, Diagnostic Neuroradiology."""
        )
    ]

    for p_id, title, r_type, fac, doc, date, fname, fsize, summary, content in sample_reports:
        execute_insert(
            """INSERT INTO health_reports (patient_id, title, report_type, hospital_facility, ordering_doctor,
                                         report_date, file_name, file_size, summary, file_content_or_preview, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (p_id, title, r_type, fac, doc, date, fname, fsize, summary, content, now_iso)
        )

    # 7. Seed Medical Records Chronology for Jane Doe
    records_seed = [
        (jane_patient_id, dr_sharma_id, "Diagnosis", "Essential Hypertension (Stage 1)", "Patient exhibits sustained systolic readings of 130-138 mmHg. Initiated lifestyle modification and first-line low-dose calcium channel blocker therapy.", last_week_str),
        (jane_patient_id, dr_sharma_id, "Clinical Summary", "Cardiovascular Risk Stratification", "10-year ASCVD calculated risk score: 3.2% (Low risk category). Fasting lipid panel reviewed with patient.", last_week_str),
        (jane_patient_id, None, "Allergy Record", "Severe Penicillin Allergy (Type 1 Hypersensitivity)", "Patient reports prior childhood emergency department admission with facial angioedema and wheezing after amoxicillin ingestion.", "2024-03-15"),
        (jane_patient_id, dr_adams_id, "Clinical Summary", "Comprehensive Annual Health Audit", "Routine wellness assessment: Vaccinations updated (Influenza & Tdap booster administered). Normal BMI and thyroid palpation.", "2025-10-14")
    ]
    for p_id, doc_id, rec_type, title, desc, r_date in records_seed:
        execute_insert(
            """INSERT INTO medical_records (patient_id, doctor_id, record_type, title, description, record_date, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (p_id, doc_id, rec_type, title, desc, r_date, now_iso)
        )

    # 8. Seed Initial Notifications
    notifications_seed = [
        (admin_uid, "System Initialization", "AegisCare Clinical Platform operational on hospital network. Relational databases and queue services active.", "announcement"),
        (admin_uid, "Roster Update", "5 clinical departments operating with verified doctor availability schedules.", "availability"),
        # Jane Doe user_id
        (query_one("SELECT user_id FROM patients WHERE id = ?", (jane_patient_id,))["user_id"],
         "Appointment Confirmed: Dr. Priya Sharma", "Your appointment #AC-2026-8941 for today at 11:00 AM (Cardiology Suite 312) has been confirmed.", "appointment_confirmation"),
        (query_one("SELECT user_id FROM patients WHERE id = ?", (jane_patient_id,))["user_id"],
         "Diagnostic Lab Results Released", "Your Comprehensive Metabolic Panel & Lipid Profile is now available in your Health Reports tab.", "report_upload"),
        (query_one("SELECT user_id FROM patients WHERE id = ?", (jane_patient_id,))["user_id"],
         "Pre-Consultation Clinical Reminder", "Please complete your home blood pressure readings and check in 15 minutes prior to your visit.", "reminder"),
        # Dr. Sharma user_id
        (query_one("SELECT user_id FROM doctors WHERE id = ?", (dr_sharma_id,))["user_id"],
         "Clinical Roster Notification", "You have 3 patient consultations scheduled for today's cardiology clinic shift.", "availability")
    ]
    for uid, title, msg, n_type in notifications_seed:
        execute_insert(
            """INSERT INTO notifications (user_id, title, message, notification_type, is_read, link_action, created_at)
               VALUES (?, ?, ?, ?, 0, '/appointments', ?)""",
            (uid, title, msg, n_type, now_iso)
        )

    # 9. Seed Initial Chat Conversation for Jane Doe
    jane_uid = query_one("SELECT user_id FROM patients WHERE id = ?", (jane_patient_id,))["user_id"]
    chat_conv_id = execute_insert(
        "INSERT INTO chat_conversations (user_id, title, created_at, updated_at) VALUES (?, 'Cardiology Preparation & Instructions', ?, ?)",
        (jane_uid, now_iso, now_iso)
    )
    execute_insert(
        """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp)
           VALUES (?, 'user', 'What should I bring for my cardiology consultation today with Dr. Sharma?', ?)""",
        (chat_conv_id, now_iso)
    )
    execute_insert(
        """INSERT INTO chat_messages (conversation_id, sender_role, message_text, timestamp)
           VALUES (?, 'assistant', 'For your cardiology consultation with Dr. Priya Sharma today at 11:00 AM, please bring:\n\n1. Valid photo identification and health insurance card.\n2. Your home blood pressure log if you have been recording readings.\n3. All current medication bottles or prescription strips (including over-the-counter supplements).\n4. Comfortable clothing suitable for blood pressure checks and brief cardiovascular examination.\n\nPlease arrive 15 minutes early at Cardiology Suite 312, Floor 3 - East Wing.', ?)""",
        (chat_conv_id, now_iso)
    )

    # 10. Seed Initial Audit Logs
    execute_insert(
        """INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details_json, timestamp)
           VALUES (?, 'SYSTEM_INIT', 'PLATFORM', 'SYSTEM', '{"event": "Clinical OS initialized with verified schemas"}', ?)""",
        (admin_uid, now_iso)
    )
    seed_enhancements_if_needed()
    print("AegisCare Clinical Platform database seeded successfully!")

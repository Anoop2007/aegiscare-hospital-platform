import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from .config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def query_one(sql: str, params: tuple = ()):
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

def query_all(sql: str, params: tuple = ()):
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def execute_insert(sql: str, params: tuple = ()):
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid

def execute_update(sql: str, params: tuple = ()):
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.rowcount

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('patient', 'doctor', 'admin')),
        full_name TEXT NOT NULL,
        phone TEXT,
        avatar_url TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        mrn TEXT UNIQUE NOT NULL,
        date_of_birth TEXT,
        gender TEXT,
        blood_group TEXT,
        emergency_contact TEXT,
        address TEXT,
        allergies TEXT,
        chronic_conditions TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        head_doctor_id INTEGER,
        floor_location TEXT,
        contact_extension TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        department_id INTEGER NOT NULL,
        specialization TEXT NOT NULL,
        license_number TEXT UNIQUE NOT NULL,
        experience_years INTEGER DEFAULT 5,
        consultation_fee REAL DEFAULT 75.0,
        languages TEXT DEFAULT 'English',
        bio TEXT,
        branch TEXT DEFAULT 'Main Campus - Wing A',
        is_available INTEGER DEFAULT 1,
        consultation_modes TEXT DEFAULT 'In-Person,Video',
        room_number TEXT,
        max_daily_patients INTEGER DEFAULT 20,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    );

    CREATE TABLE IF NOT EXISTS doctor_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL, -- 0=Mon, 6=Sun
        start_time TEXT NOT NULL, -- '09:00'
        end_time TEXT NOT NULL,   -- '17:00'
        slot_duration_minutes INTEGER DEFAULT 30,
        break_start TEXT,         -- '13:00'
        break_end TEXT,           -- '14:00'
        emergency_slots_enabled INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS doctor_leaves_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        reason TEXT,
        block_type TEXT DEFAULT 'leave', -- 'leave', 'surgery_block', 'emergency_call'
        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_number TEXT UNIQUE NOT NULL,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        scheduled_date TEXT NOT NULL,  -- 'YYYY-MM-DD'
        scheduled_time TEXT NOT NULL,  -- 'HH:MM'
        duration_minutes INTEGER DEFAULT 30,
        consultation_type TEXT NOT NULL DEFAULT 'In-Person', -- 'In-Person' or 'Video'
        status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
        priority TEXT NOT NULL DEFAULT 'routine' CHECK(priority IN ('routine', 'follow_up', 'priority', 'urgent', 'emergency')),
        reason_for_visit TEXT NOT NULL,
        cancellation_reason TEXT,
        estimated_wait_time INTEGER DEFAULT 10,
        meeting_link TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    );

    CREATE TABLE IF NOT EXISTS appointment_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL,
        previous_status TEXT,
        new_status TEXT NOT NULL,
        changed_by_user_id INTEGER,
        notes TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER,
        appointment_id INTEGER,
        record_type TEXT NOT NULL, -- 'Diagnosis', 'Prescription', 'Lab Report', 'Clinical Summary', 'Allergy'
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        clinical_data_json TEXT,
        record_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    CREATE TABLE IF NOT EXISTS health_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        report_type TEXT NOT NULL, -- 'Blood Panel', 'Cardiology/ECG', 'Radiology/MRI', 'Pathology', 'General Vitals'
        hospital_facility TEXT DEFAULT 'AegisCare Central Diagnostics Lab',
        ordering_doctor TEXT,
        report_date TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size TEXT NOT NULL,
        summary TEXT,
        file_content_or_preview TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );

    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        medications_json TEXT NOT NULL,
        instructions TEXT,
        issued_date TEXT NOT NULL,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id),
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );

    CREATE TABLE IF NOT EXISTS consultation_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER UNIQUE NOT NULL,
        doctor_id INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        symptoms TEXT NOT NULL,
        clinical_notes TEXT NOT NULL,
        diagnosis TEXT NOT NULL,
        follow_up_date TEXT,
        instructions TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id),
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );

    CREATE TABLE IF NOT EXISTS chat_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        sender_role TEXT NOT NULL CHECK(sender_role IN ('user', 'assistant')),
        message_text TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        metadata_json TEXT,
        FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL, -- 'appointment_confirmation', 'reminder', 'reschedule', 'cancellation', 'availability', 'report_upload', 'announcement'
        is_read INTEGER DEFAULT 0,
        link_action TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        resource_id TEXT,
        details_json TEXT,
        ip_address TEXT DEFAULT '127.0.0.1',
        timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS waitlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        doctor_id INTEGER,
        preferred_date TEXT NOT NULL,
        preferred_time_range TEXT DEFAULT 'any', -- 'morning', 'afternoon', 'evening', 'any'
        allocation_strategy TEXT DEFAULT 'best_available', -- 'best_available', 'fastest_available', 'preferred_doctor', 'preferred_time', 'balanced_workload'
        priority TEXT NOT NULL DEFAULT 'routine', -- 'routine', 'priority', 'urgent', 'emergency'
        reason_for_visit TEXT NOT NULL,
        consultation_type TEXT DEFAULT 'In-Person',
        status TEXT NOT NULL DEFAULT 'active', -- 'active', 'offered', 'claimed', 'cancelled', 'expired'
        offered_appointment_id INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    );

    CREATE TABLE IF NOT EXISTS waitlist_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        waitlist_id INTEGER NOT NULL,
        appointment_id INTEGER,
        action TEXT NOT NULL, -- 'joined', 'slot_offered', 'claimed', 'declined', 'cancelled'
        notes TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (waitlist_id) REFERENCES waitlist(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS ai_forecast_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_date TEXT NOT NULL,
        department_id INTEGER,
        predicted_demand INTEGER,
        predicted_cancellations INTEGER,
        predicted_noshows INTEGER,
        peak_hour_distribution_json TEXT,
        bottleneck_notes TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        locality TEXT NOT NULL,
        address TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        services_json TEXT,
        starting_fee REAL DEFAULT 500.0,
        opening_hours TEXT DEFAULT '24x7 Emergency • OPD 08:00 - 20:00',
        departments_json TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS otp_verifications (
        phone TEXT PRIMARY KEY,
        otp TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        verified INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    -- Indexes for high-performance scheduling queries
    CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, scheduled_date);
    CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
    CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
    CREATE INDEX IF NOT EXISTS idx_doctor_availability_doc ON doctor_availability(doctor_id, day_of_week);
    CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
    CREATE INDEX IF NOT EXISTS idx_reports_patient ON health_reports(patient_id);
    CREATE INDEX IF NOT EXISTS idx_records_patient ON medical_records(patient_id);
    CREATE INDEX IF NOT EXISTS idx_waitlist_dept_status ON waitlist(department_id, status);
    CREATE INDEX IF NOT EXISTS idx_hospitals_city ON hospitals(city);
    """
    with get_db() as conn:
        conn.executescript(schema)
        
        # Migration: Ensure new queue columns exist in appointments table
        cursor = conn.execute("PRAGMA table_info(appointments)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        
        cols_to_add = [
            ("check_in_time", "TEXT"),
            ("consultation_start_time", "TEXT"),
            ("actual_duration_minutes", "INTEGER"),
            ("queue_position", "INTEGER"),
            ("delay_minutes", "INTEGER DEFAULT 0")
        ]
        for col_name, col_def in cols_to_add:
            if col_name not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE appointments ADD COLUMN {col_name} {col_def}")
                except Exception as e:
                    print(f"Column migration warning for {col_name}: {e}")

        # Migration: Ensure doctor Indian hospital fields exist
        cursor = conn.execute("PRAGMA table_info(doctors)")
        existing_doc_cols = {row["name"] for row in cursor.fetchall()}
        doc_cols_to_add = [
            ("hospital_name", "TEXT DEFAULT 'CareSync Apex Super-Specialty Hospital'"),
            ("hospital_id", "INTEGER DEFAULT 1"),
            ("city", "TEXT DEFAULT 'Chennai'"),
            ("locality", "TEXT DEFAULT 'Adyar'")
        ]
        for col_name, col_def in doc_cols_to_add:
            if col_name not in existing_doc_cols:
                try:
                    conn.execute(f"ALTER TABLE doctors ADD COLUMN {col_name} {col_def}")
                except Exception as e:
                    print(f"Doctor migration warning for {col_name}: {e}")
        
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doctors_city ON doctors(city);")
        except Exception:
            pass

        # Migration: Ensure user and patient profile fields exist
        cursor = conn.execute("PRAGMA table_info(users)")
        existing_user_cols = {row["name"] for row in cursor.fetchall()}
        user_cols_to_add = [
            ("city", "TEXT DEFAULT 'Chennai'"),
            ("preferred_language", "TEXT DEFAULT 'English'")
        ]
        for col_name, col_def in user_cols_to_add:
            if col_name not in existing_user_cols:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                except Exception as e:
                    print(f"User migration warning for {col_name}: {e}")

        cursor = conn.execute("PRAGMA table_info(patients)")
        existing_pat_cols = {row["name"] for row in cursor.fetchall()}
        pat_cols_to_add = [
            ("city", "TEXT DEFAULT 'Chennai'"),
            ("preferred_language", "TEXT DEFAULT 'English'")
        ]
        for col_name, col_def in pat_cols_to_add:
            if col_name not in existing_pat_cols:
                try:
                    conn.execute(f"ALTER TABLE patients ADD COLUMN {col_name} {col_def}")
                except Exception:
                    pass

        cursor = conn.execute("PRAGMA table_info(hospitals)")
        existing_hosp_cols = {row["name"] for row in cursor.fetchall()}
        hosp_cols_to_add = [
            ("image_url", "TEXT DEFAULT 'https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600'"),
            ("departments_json", "TEXT DEFAULT '[]'")
        ]
        for col_name, col_def in hosp_cols_to_add:
            if col_name not in existing_hosp_cols:
                try:
                    conn.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_def}")
                except Exception as e:
                    print(f"Hospital migration warning for {col_name}: {e}")


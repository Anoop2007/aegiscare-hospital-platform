from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any

class SendOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10)

class VerifyOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10)
    otp: str = Field(..., min_length=4, max_length=6)

class GoogleLoginRequest(BaseModel):
    id_token: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    role: Optional[str] = "patient" # 'patient' or 'doctor'
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    preferred_language: Optional[str] = "English"
    city: Optional[str] = "Chennai"

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str = Field(..., min_length=6)

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    preferred_language: Optional[str] = None
    avatar_url: Optional[str] = None

class SmartDoctorRecommendationRequest(BaseModel):
    department_id: Optional[int] = None
    specialty: Optional[str] = None
    urgency: str = Field(default="routine")  # 'routine', 'priority', 'follow_up', 'urgent', 'emergency'
    preferred_date: Optional[str] = None     # 'YYYY-MM-DD'
    preferred_time_of_day: Optional[str] = "any" # 'morning', 'afternoon', 'evening', 'any'
    preferred_time_range: Optional[str] = "any"
    preferred_doctor_id: Optional[int] = None
    allocation_strategy: str = Field(default="best_available") # 'best_available', 'fastest_available', 'preferred_doctor', 'preferred_time', 'balanced_workload'
    consultation_type: str = Field(default="In-Person") # 'In-Person' or 'Video'
    reason_for_visit: str

class AppointmentCreateRequest(BaseModel):
    doctor_id: int
    scheduled_date: str # 'YYYY-MM-DD'
    scheduled_time: str # 'HH:MM'
    duration_minutes: int = 30
    consultation_type: str = "In-Person" # 'In-Person', 'Video'
    reason_for_visit: str
    priority: str = "routine" # 'routine', 'priority', 'follow_up', 'urgent', 'emergency'

class WaitlistJoinRequest(BaseModel):
    department_id: int
    doctor_id: Optional[int] = None
    preferred_date: Optional[str] = None
    preferred_time_range: str = "any" # 'morning', 'afternoon', 'evening', 'any'
    allocation_strategy: str = "best_available"
    priority: str = "routine" # 'routine', 'priority', 'urgent', 'emergency'
    reason_for_visit: str
    consultation_type: str = "In-Person"

class WaitlistClaimRequest(BaseModel):
    waitlist_id: int

class QueueStatusUpdateRequest(BaseModel):
    action: Optional[str] = None # 'check_in', 'start_consult', 'mark_delay', 'complete'
    queue_status: Optional[str] = None # 'checked_in', 'waiting', 'in_progress', 'completed', 'delayed'
    delay_minutes: Optional[int] = 0
    notes: Optional[str] = None

class AppointmentRescheduleRequest(BaseModel):
    scheduled_date: str
    scheduled_time: str
    reason: Optional[str] = None

class AppointmentCancelRequest(BaseModel):
    reason: str

class AppointmentStatusUpdateRequest(BaseModel):
    status: str # 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'
    notes: Optional[str] = None

class AvailabilitySlotConfig(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 30
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    emergency_slots_enabled: bool = True
    is_active: bool = True

class DoctorAvailabilityUpdateRequest(BaseModel):
    schedules: List[AvailabilitySlotConfig]

class DoctorLeaveCreateRequest(BaseModel):
    start_datetime: str
    end_datetime: str
    reason: str
    block_type: str = "leave" # 'leave', 'surgery_block', 'emergency_call'

class PrescriptionItem(BaseModel):
    medication_name: str
    dosage: str
    frequency: str # e.g. "Twice daily after food"
    duration: str  # e.g. "7 days"
    instructions: Optional[str] = None

class ConsultationNoteCreateRequest(BaseModel):
    appointment_id: int
    symptoms: str
    clinical_notes: str
    diagnosis: str
    follow_up_date: Optional[str] = None
    instructions: Optional[str] = None
    prescriptions: Optional[List[PrescriptionItem]] = None

class ChatMessageRequest(BaseModel):
    message: str

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = "Clinical Inquiry"
    initial_message: Optional[str] = None

class ConversationRenameRequest(BaseModel):
    title: str

class AnnouncementCreateRequest(BaseModel):
    title: str
    message: str
    priority: str = "info" # 'info', 'warning', 'critical'
    target_role: Optional[str] = "all" # 'all', 'patient', 'doctor'

class DoctorCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    phone: Optional[str] = None
    department_id: int
    specialization: str
    license_number: str
    experience_years: int = 5
    consultation_fee: float = 75.0
    languages: str = "English"
    bio: Optional[str] = None
    branch: str = "Main Campus - Wing A"
    consultation_modes: str = "In-Person,Video"
    room_number: Optional[str] = "Suite 201"
    max_daily_patients: int = 20

class DoctorUpdateRequest(BaseModel):
    department_id: Optional[int] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    languages: Optional[str] = None
    bio: Optional[str] = None
    branch: Optional[str] = None
    is_available: Optional[bool] = None
    consultation_modes: Optional[str] = None
    room_number: Optional[str] = None
    max_daily_patients: Optional[int] = None

class DepartmentCreateRequest(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    floor_location: Optional[str] = None
    contact_extension: Optional[str] = None
    head_doctor_id: Optional[int] = None

class AIHealthSummaryRequest(BaseModel):
    patient_id: Optional[int] = None # Defaults to current user if patient

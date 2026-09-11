# CareAura Health OS | Indian Hospital Resource & Availability Platform

A production-grade, full-stack hospital clinical management, doctor availability optimization, and appointment platform. CareAura Health OS streamlines patient flow, balances physician shift capacity, automates appointment allocation, provides structured electronic health record documentation, and leverages AI-assisted decision making for appointment matching and hospital discovery across premier Indian multi-specialty healthcare institutions.

---

## 🌟 Key Features

### 1. Patient Portal
- **Dashboard Overview**: Patient identity banner displaying Medical Record Number (MRN), verified blood group, upcoming appointment hero card with live status badges, clinical quick actions, and recent activity feed.
- **Doctor Discovery & Multi-Faceted Filtering**: Search across 22 clinical specialties, Indian metro cities, consultation modes (In-Person vs. Telehealth Video), availability status, and experience. Doctor cards showcase verified licenses, clinic rooms, fees in INR (₹), languages, live shift timings, and direct booking triggers.
- **GPS Distance & Nearest Hospital Detection**: "📍 Nearest to Me" feature calculates real geographic distance using the Haversine formula against hospital coordinates.
- **Smart Appointment Booking**: Step-by-step workflow with real-time doctor availability checks, morning/afternoon/evening slot selection pills, and conflict prevention.
- **AI-Assisted Doctor & Slot Recommendation**: Evaluates clinical urgency, department specialty alignment, queue length, waiting time estimation, and physician workload to return ranked recommendations.
- **Appointment Management**: Complete tracking of upcoming and completed visits, self-service rescheduling with slot conflict validation, and instant cancellation with recorded reasons.
- **Telehealth Virtual Consultation Room**: Live simulated video consultation with duration timer, encrypted telemetry simulation, physician camera stream, and digital prescription summary.
- **Electronic Medical Records**: Chronological clinical timeline containing diagnostic entries signed by physicians, active allergies, chronic conditions, and past treatments.
- **Diagnostic Health Reports**: Laboratory and radiology reports repository (Blood & Metabolic Panels, 12-Lead ECGs, 3.0T Cranial MRIs, Chest X-Rays) with rich document preview modal and PDF action.
- **AI Clinical Hospital Assistant**: Context-aware natural language assistant for guidance on appointments, doctor schedules, test preparations, and Indian hospital navigation with persistent multi-turn thread history.

### 2. Physician Workspace
- **Clinical Queue Management**: Real-time triage of today's scheduled consultations (Waiting, In-Progress, Completed, No-Show) with one-click consultation launching.
- **Availability Schedule & Roster**: Interactive weekly calendar grid to configure shift start/end times, slot durations (15/30/45/60 min), lunch/break blocks, and emergency buffer slots.
- **Leaves & Unavailability Blocks**: Record vacations, surgery operating room blocks, and emergency call periods.
- **Duty Status Quick Toggle**: Instantly switch between Active and Off-Duty availability.
- **Clinical Consultation Documentation**: Structured SOAP note entry (Subjective symptoms, Objective examination notes, Official Diagnosis field, Follow-up date picker, Patient instructions).
- **Electronic Prescription Pad**: Dynamic multi-item prescription issuer with drug name, dosage, frequency, duration, and special dietary/intake instructions.
- **Authorized Patient Clinical Chart**: Comprehensive view of patient history, allergies, chronic conditions, and previous diagnostic reports.
- **Workload Analytics**: Shift capacity utilization gauge, peak consultation hours, average consultation duration, and no-show rate.

### 3. Hospital Administration Console
- **Hospital Operations Command Center**: Real-time hospital metrics including total physicians, enrolled patients, today's appointment volume, completion rates, current waiting patients, and live doctor roster status.
- **Doctor Roster Management**: Onboard new medical doctors with credentials, departments, consultation fees, and working hours; toggle physician account activation.
- **Clinical Department Management**: Establish and configure hospital departments with floor locations, extensions, and head physician assignments.
- **Master Appointments Ledger**: Hospital-wide searchable and filterable appointment audit table.
- **Hospital Resource Analytics**: Visual charts powered by Chart.js for 7-day appointment demand trends, doctor capacity utilization comparison, and department volume distribution.
- **Broadcast Announcements**: Hospital-wide notification composer targeting all users, patients, or physicians with priority levels (Info, Warning, Critical).
- **Audit & Governance Logs**: ABDM & HIPAA-compliant audit trail recording user identity, action, resource target, IP address, and timestamp.

---

## 🔐 Preloaded Enterprise Accounts

Use the **Quick Role Switcher** in the top bar to switch between profiles with one click:

| Role | Name | Details | Access Route |
|---|---|---|---|
| **Patient** | Arjun Sharma | MRN: `CA-MRN-48912` • Male, 34 • Blood: O+ | Topbar "Patient (Arjun)" |
| **Doctor** | Dr. Priya Sharma, MD | Interventional Cardiology • CareAura Apollo Chennai | Topbar "Doctor" pill |
| **Admin** | Chief Medical Officer | Hospital Administration & Node Governance | Topbar "Admin" pill |

---

## 🚀 Installation & Local Development

### Prerequisites
- Python 3.10+ (Tested and verified on Python 3.14)
- Web browser (Chrome, Edge, Safari, Firefox, Brave)

### Installation
```bash
# 1. Clone or navigate to the repository directory:
cd aegiscare-hospital-platform

# 2. Install Python backend dependencies:
pip install -r requirements.txt

# 3. (Optional) Configure environment variables:
cp .env.example .env
```

### Running the Application
```bash
python run.py
```

The application will start on:
```
http://127.0.0.1:8000
```

### Running the Automated QA Verification Suite
```bash
python test_production_readiness.py
```
*(Runs 66 comprehensive automated test cases verifying health, auth, patient workflows, appointments, doctor portal, admin portal, AI assistant, and SQL injection resistance).*

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application, CORS, static mounts, SPA catchall
│   │   ├── config.py            # Environment configuration & JWT settings
│   │   ├── database.py          # SQLite schema, migrations, connection helper
│   │   ├── auth.py              # PBKDF2 hashing, JWT verification, RBAC guards
│   │   ├── schemas.py           # Pydantic request/response validation models
│   │   ├── ai_service.py        # Natural language query engine & card generation
│   │   └── routers/             # Modular API controllers (auth, patient, doctor, admin, etc.)
│   └── data/
│       └── aegiscare.db         # Relational SQLite database
├── frontend/
│   ├── index.html               # Single-page application markup & modals
│   ├── css/
│   │   └── style.css            # Mint-teal enterprise design system & responsive layout
│   ├── js/
│   │   ├── app.js               # Application coordinator, auth modal, intro animation
│   │   ├── patient.js           # Patient portal, doctors directory, booking, GPS distance
│   │   ├── doctor.js            # Doctor workspace, clinical queue, consultation notes
│   │   ├── admin.js             # Administration command center & hospital charts
│   │   ├── chatbot.js           # AI clinical assistant chat drawer
│   │   ├── api.js               # HTTP client with AbortController & retry logic
│   │   └── state.js             # Reactive application state store
│   └── assets/
│       └── brand-logo.svg       # CareAura brand logo
├── .gitignore                   # Excludes caches, databases, .env, and binary tools
├── .env.example                 # Environment configuration template
├── requirements.txt             # Python production dependencies
├── run.py                       # Server entrypoint
└── test_production_readiness.py # Comprehensive QA test suite
```

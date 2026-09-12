// CareSync Clinical OS Centralized API Client & Resilient Fallback Engine
const API_BASE = (() => {
  if (typeof window !== 'undefined' && window.location) {
    const params = new URLSearchParams(window.location.search);
    const queryApi = params.get('api');
    if (queryApi) {
      localStorage.setItem('careaura_backend_url', queryApi.replace(/\/+$/, ''));
    }
  }

  const storedBackend = typeof localStorage !== 'undefined' ? localStorage.getItem('careaura_backend_url') : null;
  if (storedBackend) {
    return storedBackend;
  }

  if (typeof window !== 'undefined' && (window.API_BASE_URL || window.AEGIS_API_URL || window.VITE_API_URL)) {
    return (window.API_BASE_URL || window.AEGIS_API_URL || window.VITE_API_URL).replace(/\/+$/, '');
  }

  // If running locally in development, point to local backend
  if (typeof window !== 'undefined' && window.location) {
    const hostname = window.location.hostname;
    const port = window.location.port;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      if (port && !['8000', '', '80', '443'].includes(port)) {
        return `${window.location.protocol}//${hostname}:8000/api`;
      }
      return '/api';
    }
  }

  // Production Render Live Backend API URL
  return 'https://aegiscare-hospital-platform-1.onrender.com/api';
})();

/* ================= COMPREHENSIVE CLINICAL FALLBACK STORE ================= */
const MockStore = {
  doctors: [
    { id: 1, full_name: "Dr. Priya Sharma, MD", department_id: 1, department_name: "Cardiology & Vascular", specialization: "Interventional Cardiology", consultation_fee: 950, experience_years: 14, rating: 4.9, is_available: true, consultation_modes: ["In-Person", "Video"], hospital_name: "Apollo Speciality Hospital, Chennai", city: "Chennai", room_number: "Suite 204", nmc_license: "NMC-TN-48912", avatar_url: "/assets/doctors/doc_1.jpg" },
    { id: 2, full_name: "Dr. Rajesh K. Varma, MS", department_id: 3, department_name: "Orthopedics & Sports", specialization: "Joint Replacement & Arthroscopy", consultation_fee: 850, experience_years: 18, rating: 4.8, is_available: true, consultation_modes: ["In-Person"], hospital_name: "Manipal Hospital, Bengaluru", city: "Bengaluru", room_number: "Suite 108", nmc_license: "NMC-KA-21940", avatar_url: "/assets/doctors/doc_2.jpg" },
    { id: 3, full_name: "Dr. Ananya Sen, MD, DM", department_id: 2, department_name: "Neurology & Stroke", specialization: "Comprehensive Stroke & Epilepsy Care", consultation_fee: 1100, experience_years: 12, rating: 4.9, is_available: false, consultation_modes: ["In-Person", "Video"], hospital_name: "Fortis Memorial Research Institute, Gurugram", city: "Delhi", room_number: "Suite 312", nmc_license: "NMC-DL-51209", avatar_url: "/assets/doctors/doc_3.jpg" },
    { id: 4, full_name: "Dr. Karthik Sundaram, MD", department_id: 4, department_name: "Pediatrics & Adolescent", specialization: "Pediatric Critical Care & Immunization", consultation_fee: 750, experience_years: 9, rating: 4.7, is_available: true, consultation_modes: ["In-Person", "Video"], hospital_name: "KIMS Hospital, Hyderabad", city: "Hyderabad", room_number: "Suite 102", nmc_license: "NMC-TS-38291", avatar_url: "/assets/doctors/doc_4.jpg" },
    { id: 5, full_name: "Dr. Meenakshi Sundar, MD, DM", department_id: 5, department_name: "Oncology & Hematology", specialization: "Medical Oncology & Precision Chemotherapy", consultation_fee: 1300, experience_years: 16, rating: 5.0, is_available: true, consultation_modes: ["In-Person", "Video"], hospital_name: "Tata Memorial Centre, Mumbai", city: "Mumbai", room_number: "Suite 405", nmc_license: "NMC-MH-19823", avatar_url: "/assets/doctors/doc_5.jpg" },
    { id: 6, full_name: "Dr. Vikram Sethi, MD", department_id: 6, department_name: "Internal Medicine", specialization: "Preventive Medicine & Diabetes Management", consultation_fee: 650, experience_years: 11, rating: 4.8, is_available: true, consultation_modes: ["In-Person"], hospital_name: "Max Super Speciality Hospital, Delhi", city: "Delhi", room_number: "Suite 115", nmc_license: "NMC-DL-44820", avatar_url: "/assets/doctors/doc_6.jpg" }
  ],
  departments: [
    { id: 1, name: "Cardiology & Vascular", code: "CARD", floor: "Floor 2 - East Wing", doctor_count: 6, extension: "201" },
    { id: 2, name: "Neurology & Stroke", code: "NEUR", floor: "Floor 3 - North Wing", doctor_count: 4, extension: "305" },
    { id: 3, name: "Orthopedics & Sports", code: "ORTHO", floor: "Floor 1 - West Wing", doctor_count: 5, extension: "112" },
    { id: 4, name: "Pediatrics & Adolescent", code: "PED", floor: "Floor 2 - Pediatric Block", doctor_count: 4, extension: "218" },
    { id: 5, name: "Oncology & Hematology", code: "ONCO", floor: "Floor 4 - Comprehensive Oncology Center", doctor_count: 3, extension: "401" },
    { id: 6, name: "Internal Medicine", code: "IM", floor: "Ground Floor - Outpatient Pavilion", doctor_count: 7, extension: "105" }
  ],
  hospitals: [
    { id: 1, code: "HOSP-CHE-101", name: "Apollo Speciality Hospital Greams Road", city: "Chennai", locality: "Thousand Lights", state: "Tamil Nadu", address: "21 Greams Lane, Thousand Lights, Chennai, Tamil Nadu 600006", accreditation: "NABH / JCI Accredited", total_doctors: 24, bed_capacity: 550, icu_beds: 65, consultation_base_fee: 750, emergency_24x7: true, departments: ["Cardiology", "Neurology", "Orthopedics", "Oncology"], consultation_fee: "₹750 - ₹1,500", rating: 4.9, image_url: "/assets/hospitals/hosp_chennai_1.jpg", latitude: 12.9800, longitude: 80.2200 },
    { id: 2, code: "HOSP-BLR-102", name: "Manipal Hospital Old Airport Road", city: "Bengaluru", locality: "Kodihalli", state: "Karnataka", address: "98 HAL Old Airport Rd, Kodihalli, Bengaluru, Karnataka 560017", accreditation: "NABH Accredited", total_doctors: 28, bed_capacity: 650, icu_beds: 80, consultation_base_fee: 850, emergency_24x7: true, departments: ["Orthopedics", "Cardiology", "Pediatrics", "Oncology"], consultation_fee: "₹850 - ₹1,400", rating: 4.8, image_url: "/assets/hospitals/hosp_bangalore_1.jpg", latitude: 12.9716, longitude: 77.0100 },
    { id: 3, code: "HOSP-HYD-103", name: "KIMS Hospital Secunderabad", city: "Hyderabad", locality: "Krishna Nagar", state: "Telangana", address: "1-8-31/1, Minister Rd, Krishna Nagar, Secunderabad 500003", accreditation: "NABH / NABL Accredited", total_doctors: 22, bed_capacity: 480, icu_beds: 45, consultation_base_fee: 600, emergency_24x7: true, departments: ["Pediatrics", "Cardiology", "Neurology"], consultation_fee: "₹600 - ₹1,200", rating: 4.8, image_url: "/assets/hospitals/hosp_hyderabad_1.jpg", latitude: 16.6400, longitude: 79.1500 },
    { id: 4, code: "HOSP-BOM-104", name: "Tata Memorial Hospital Parel", city: "Mumbai", locality: "Parel", state: "Maharashtra", address: "Dr. E Borges Road, Parel, Mumbai, Maharashtra 400012", accreditation: "NABH Accredited Apex Oncology Center", total_doctors: 35, bed_capacity: 820, icu_beds: 95, consultation_base_fee: 900, emergency_24x7: true, departments: ["Oncology", "Hematology", "Palliative Care"], consultation_fee: "₹900 - ₹1,800", rating: 4.9, image_url: "/assets/hospitals/hosp_pune_1.jpg", latitude: 19.0760, longitude: 72.8777 },
    { id: 5, code: "HOSP-VJA-105", name: "Manipal Hospital Vijayawada", city: "Vijayawada", locality: "Benz Circle", state: "Andhra Pradesh", address: "MG Road, Benz Circle, Vijayawada 520010", accreditation: "NABH Accredited", total_doctors: 20, bed_capacity: 400, icu_beds: 40, consultation_base_fee: 500, emergency_24x7: true, departments: ["Cardiology", "Orthopedics", "Pediatrics"], consultation_fee: "₹500 - ₹1,000", rating: 4.8, image_url: "/assets/hospitals/hosp_vijayawada_1.jpg", latitude: 16.7600, longitude: 80.6000 }
  ],
  appointments: [
    { id: 101, appointment_ref: "CA-APT-8941", doctor_name: "Dr. Priya Sharma, MD", department_name: "Cardiology & Vascular", scheduled_date: new Date().toISOString().split('T')[0], scheduled_time: "10:30 AM", consultation_mode: "In-Person", status: "confirmed", reason: "Quarterly hypertension evaluation and ECG review", doctor_id: 1, room_number: "Suite 204" },
    { id: 102, appointment_ref: "CA-APT-8820", doctor_name: "Dr. Rajesh K. Varma, MS", department_name: "Orthopedics & Sports", scheduled_date: "2026-09-18", scheduled_time: "02:00 PM", consultation_mode: "In-Person", status: "upcoming", reason: "Post-rehabilitation knee joint assessment", doctor_id: 2, room_number: "Suite 108" },
    { id: 103, appointment_ref: "CA-APT-8650", doctor_name: "Dr. Vikram Sethi, MD", department_name: "Internal Medicine", scheduled_date: "2026-08-25", scheduled_time: "11:00 AM", consultation_mode: "Video", status: "completed", reason: "HbA1c diabetes blood sugar adjustment", doctor_id: 6, room_number: "Suite 115" }
  ],
  medical_history: [
    { id: 1, recorded_date: "2026-08-25", doctor_name: "Dr. Vikram Sethi, MD", diagnosis: "Controlled Type 2 Diabetes Mellitus", notes: "HbA1c stable at 6.4%. Advised to continue moderate exercise and DASH diet.", vitals: { bp: "124/82 mmHg", pulse: "74 bpm", spo2: "99%", temp: "98.4 F" } },
    { id: 2, recorded_date: "2026-05-12", doctor_name: "Dr. Priya Sharma, MD", diagnosis: "Essential Stage-1 Hypertension", notes: "Blood pressure stabilized on Amlodipine 5mg OD. Normal sinus rhythm on resting ECG.", vitals: { bp: "128/84 mmHg", pulse: "76 bpm", spo2: "98%", temp: "98.6 F" } }
  ],
  health_reports: [
    { id: 1, title: "Comprehensive Metabolic & Lipid Panel", category: "Blood Panel", test_date: "2026-08-24", facility: "Apollo Diagnostics Central Lab", file_size: "1.4 MB", summary: "Total Cholesterol 178 mg/dL (Normal). Fasting Glucose 96 mg/dL (Normal). Creatinine 0.9 mg/dL (Normal)." },
    { id: 2, title: "12-Lead Resting Electrocardiogram (ECG)", category: "Cardiology/ECG", test_date: "2026-05-12", facility: "Apollo Heart Institute", file_size: "2.1 MB", summary: "Normal sinus rhythm at 72 bpm. PR interval 156 ms. No acute ST-T wave changes." }
  ],
  notifications: [
    { id: 1, title: "Appointment Reminder", message: "Your consultation with Dr. Priya Sharma is scheduled for today at 10:30 AM in Suite 204.", created_at: new Date().toISOString(), is_read: false },
    { id: 2, title: "Diagnostic Report Ready", message: "Your Comprehensive Metabolic Panel results have been verified by the central pathology laboratory.", created_at: new Date(Date.now() - 86400000).toISOString(), is_read: false },
    { id: 3, title: "Smart Standby Alert", message: "You are #1 on the priority standby waitlist for Cardiology morning openings.", created_at: new Date(Date.now() - 172800000).toISOString(), is_read: true }
  ],
  chat_conversations: [
    { id: "conv-1", title: "Hospital Services & Scheduling", created_at: new Date().toISOString(), messages: [
      { sender: "assistant", text: "Hello Arjun! I am your CareAura Clinical Assistant. I can help you find specialists, book consultations, review diagnostic reports, or check standby waitlist status. How can I assist you today?" }
    ]}
  ]
};

const api = {
  _abortControllers: new Map(),

  getBaseUrl() {
    return API_BASE;
  },

  getToken() {
    return localStorage.getItem('careaura_token') || localStorage.getItem('aegiscare_token') || 'demo-mock-token-2026';
  },
  setToken(token) {
    localStorage.setItem('careaura_token', token);
    localStorage.setItem('aegiscare_token', token);
  },
  clearToken() {
    localStorage.removeItem('careaura_token');
    localStorage.removeItem('aegiscare_token');
  },
  getCurrentUser() {
    const raw = localStorage.getItem('careaura_user') || localStorage.getItem('aegiscare_user');
    try {
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },
  setCurrentUser(user) {
    localStorage.setItem('careaura_user', JSON.stringify(user));
    localStorage.setItem('aegiscare_user', JSON.stringify(user));
  },
  clearCurrentUser() {
    localStorage.removeItem('careaura_user');
    localStorage.removeItem('aegiscare_user');
  },

  abortPrior(key) {
    if (this._abortControllers.has(key)) {
      try {
        this._abortControllers.get(key).abort();
      } catch (e) {}
      this._abortControllers.delete(key);
    }
    const controller = new AbortController();
    this._abortControllers.set(key, controller);
    return controller.signal;
  },

  /* ================= INTERNAL MOCK HANDLER ================= */
  async _handleMockFallback(endpoint, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const cleanUrl = endpoint.split('?')[0];

    // Artificial tiny latency for realistic UI state transitions
    await new Promise(r => setTimeout(r, 60));

    // Auth routes
    if (cleanUrl.startsWith('/auth/quick-login/')) {
      const role = cleanUrl.replace('/auth/quick-login/', '').toLowerCase();
      let user = {
        id: 1,
        full_name: "Arjun Sharma",
        email: "arjun.sharma@careaura.health",
        role: "patient",
        mrn: "CA-MRN-48912",
        phone: "+91 98401 55210",
        city: "Chennai",
        preferred_language: "English",
        avatar_url: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
      };
      if (role === 'doctor') {
        user = {
          id: 2,
          full_name: "Dr. Priya Sharma, MD",
          email: "dr.priya@careaura.health",
          role: "doctor",
          specialization: "Cardiology & Vascular",
          phone: "+91 98401 22334",
          city: "Chennai",
          avatar_url: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=150"
        };
      } else if (role === 'admin') {
        user = {
          id: 3,
          full_name: "Dr. Arvind Swaminathan (CMO)",
          email: "cmo.admin@careaura.health",
          role: "admin",
          phone: "+91 98401 11223",
          city: "Chennai",
          avatar_url: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"
        };
      }
      return { access_token: "mock-jwt-auth-session-key", user };
    }

    if (cleanUrl === '/auth/me') {
      const u = this.getCurrentUser() || {
        id: 1,
        full_name: "Arjun Sharma",
        email: "arjun.sharma@careaura.health",
        role: "patient",
        mrn: "CA-MRN-48912",
        phone: "+91 98401 55210",
        city: "Chennai",
        preferred_language: "English"
      };
      return {
        user: u,
        patient: {
          mrn: u.mrn || "CA-MRN-48912",
          date_of_birth: "1992-05-14",
          gender: "Male",
          blood_group: "O+",
          address: "Plot 42, 4th Cross Road, Adyar, Chennai 600020",
          emergency_contact: "Rajesh Sharma (Brother) - +91 98401 55210",
          allergies: "Penicillin, Dust Mites",
          chronic_conditions: "Mild Seasonal Bronchitis"
        }
      };
    }

    if (cleanUrl === '/auth/send-otp') {
      return { success: true, message: "Verification OTP sent successfully via secure SMS gateway" };
    }

    if (cleanUrl === '/auth/verify-otp' || cleanUrl === '/auth/login' || cleanUrl === '/auth/register' || cleanUrl === '/auth/google-login') {
      const body = typeof options.body === 'string' ? JSON.parse(options.body || '{}') : (options.body || {});
      const email = body.email || "patient.jane@aegiscare.health";
      const u = {
        id: 1,
        full_name: email.split('@')[0].replace('.', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        email: email,
        role: "patient",
        mrn: "CA-MRN-48912",
        phone: "+91 98401 55210",
        city: "Chennai",
        preferred_language: "English"
      };
      return { access_token: "mock-verified-session-token", user: u };
    }

    if (cleanUrl === '/auth/profile') {
      return { success: true, user: this.getCurrentUser() || {} };
    }

    // Patient routes
    if (cleanUrl === '/patient/departments') {
      return MockStore.departments;
    }

    if (cleanUrl === '/patient/doctors') {
      return MockStore.doctors;
    }

    if (cleanUrl.startsWith('/patient/doctors/')) {
      const id = parseInt(cleanUrl.split('/')[3]);
      return MockStore.doctors.find(d => d.id === id) || MockStore.doctors[0];
    }

    if (cleanUrl === '/patient/hospitals') {
      return MockStore.hospitals;
    }

    if (cleanUrl.startsWith('/patient/hospitals/')) {
      const id = parseInt(cleanUrl.split('/')[3]);
      const hosp = MockStore.hospitals.find(h => h.id === id) || MockStore.hospitals[0];
      return {
        ...hosp,
        departments: MockStore.departments,
        doctors: MockStore.doctors
      };
    }

    if (cleanUrl === '/patient/dashboard') {
      return {
        metrics: {
          total_appointments: MockStore.appointments.length + 3,
          completed_consultations: 4,
          uploaded_reports: MockStore.health_reports.length,
          unread_notifications: 3
        },
        patient: {
          id: 1,
          mrn: "CA-MRN-48912",
          blood_group: "O+",
          full_name: "Arjun Sharma"
        },
        live_queue: {
          in_queue: true,
          position: 2,
          estimated_wait_minutes: 15,
          doctor_name: "Dr. Priya Sharma, MD",
          room: "Suite 204",
          status: "waiting"
        },
        recent_activity: [
          { date: "Today, 09:15 AM", title: "Checked in at reception desk for Dr. Priya Sharma" },
          { date: "Yesterday", title: "Automated prescription refill notification generated" },
          { date: "08 Sep 2026", title: "Quarterly blood lipid profile verified by central lab" }
        ],
        offered_waitlist_slot: null
      };
    }

    if (cleanUrl === '/patient/appointments') {
      if (method === 'POST') {
        const body = JSON.parse(options.body || '{}');
        const doc = MockStore.doctors.find(d => d.id == body.doctor_id) || MockStore.doctors[0];
        const newAppt = {
          id: Date.now(),
          appointment_ref: `CA-APT-${Math.floor(1000 + Math.random() * 9000)}`,
          doctor_name: doc.full_name,
          department_name: doc.department_name,
          scheduled_date: body.scheduled_date || new Date().toISOString().split('T')[0],
          scheduled_time: body.scheduled_time || "11:30 AM",
          consultation_mode: body.consultation_mode || "In-Person",
          status: "confirmed",
          reason: body.reason || "Routine Health Consultation",
          doctor_id: doc.id,
          room_number: doc.room_number
        };
        MockStore.appointments.unshift(newAppt);
        return { success: true, appointment: newAppt };
      }
      return MockStore.appointments;
    }

    if (cleanUrl.startsWith('/patient/appointments/')) {
      const parts = cleanUrl.split('/');
      const apptId = parseInt(parts[3]);
      const appt = MockStore.appointments.find(a => a.id === apptId) || MockStore.appointments[0];

      if (cleanUrl.endsWith('/reschedule')) {
        const body = JSON.parse(options.body || '{}');
        if (appt) {
          appt.scheduled_date = body.new_date || appt.scheduled_date;
          appt.scheduled_time = body.new_time || appt.scheduled_time;
          appt.status = "rescheduled";
        }
        return { success: true, message: "Appointment rescheduled successfully" };
      }

      if (cleanUrl.endsWith('/cancel')) {
        if (appt) appt.status = "cancelled";
        return { success: true, message: "Appointment cancelled" };
      }

      return appt;
    }

    if (cleanUrl === '/patient/medical-history') {
      return MockStore.medical_history;
    }

    if (cleanUrl === '/patient/health-reports') {
      return MockStore.health_reports;
    }

    if (cleanUrl.startsWith('/patient/health-reports/')) {
      const id = parseInt(cleanUrl.split('/')[3]);
      return MockStore.health_reports.find(r => r.id === id) || MockStore.health_reports[0];
    }

    if (cleanUrl === '/patient/ai-health-summary') {
      return {
        summary_html: `
          <div style="line-height:1.6; font-size:0.88rem;">
            <p><strong>Clinical Longitudinal Health Digest (CareAura AI Engine):</strong></p>
            <p>Patient Arjun Sharma (MRN: CA-MRN-48912) maintains well-managed essential hypertension and controlled glycemia. Blood pressure values remain within target systolic range (&lt;130 mmHg) on daily Amlodipine regimen.</p>
            <ul>
              <li><strong>Cardiovascular:</strong> Normal Sinus Rhythm; baseline ECG within normal physiological limits.</li>
              <li><strong>Metabolic Profile:</strong> HbA1c at 6.4%, stable. Renal and hepatic markers within normal standard range.</li>
              <li><strong>Recommended Next Step:</strong> Adhere to low-sodium Mediterranean DASH diet and maintain routine bi-annual lab evaluations.</li>
            </ul>
          </div>
        `
      };
    }

    if (cleanUrl === '/patient/timeline') {
      return [
        { date: "2026-09-12", title: "CareAura Health OS Consultation", type: "consultation", doctor: "Dr. Priya Sharma", description: "Blood pressure check and clinical telemetry session" },
        { date: "2026-08-25", title: "Internal Medicine Follow-up", type: "consultation", doctor: "Dr. Vikram Sethi", description: "Metabolic review & diabetic monitoring" },
        { date: "2026-08-24", title: "Comprehensive Metabolic Panel", type: "lab_report", doctor: "Central Pathology", description: "Normal biochemical panels" },
        { date: "2026-05-12", title: "12-Lead Resting Electrocardiogram", type: "lab_report", doctor: "Cardiology Lab", description: "Normal sinus rhythm at 72 bpm" }
      ];
    }

    if (cleanUrl === '/patient/notifications') {
      return MockStore.notifications;
    }

    if (cleanUrl === '/patient/notifications/mark-all-read') {
      MockStore.notifications.forEach(n => n.is_read = true);
      return { success: true };
    }

    // Appointment Slots & AI Recommendations
    if (cleanUrl === '/appointments/slots') {
      return {
        date: new Date().toISOString().split('T')[0],
        morning_slots: ["09:00 AM", "09:30 AM", "10:30 AM", "11:00 AM", "11:45 AM"],
        afternoon_slots: ["02:00 PM", "02:45 PM", "03:30 PM", "04:15 PM", "05:00 PM"]
      };
    }

    if (cleanUrl === '/appointments/ai-recommend') {
      return {
        recommended_doctor_id: 1,
        recommended_doctor_name: "Dr. Priya Sharma, MD",
        department_name: "Cardiology & Vascular",
        recommended_slot: "10:30 AM (Morning Window)",
        rationale: "Optimized for minimal waiting queue (estimated 12 mins) and optimal match with reported cardiovascular symptoms."
      };
    }

    if (cleanUrl === '/appointments/waitlist') {
      if (method === 'POST') {
        return { success: true, message: "Registered on Priority Standby Waitlist" };
      }
      return [
        { id: 1, doctor_name: "Dr. Priya Sharma, MD", department_name: "Cardiology & Vascular", priority: "priority", desired_date: "2026-09-14", queue_position: 1, status: "active" }
      ];
    }

    if (cleanUrl.startsWith('/appointments/waitlist/')) {
      return { success: true, message: "Waitlist operation confirmed" };
    }

    if (cleanUrl.includes('/queue-status')) {
      return { success: true, status: "updated", queue_position: 1 };
    }

    // Doctor routes
    if (cleanUrl === '/doctor/overview') {
      return {
        today_stats: {
          patients_waiting: 3,
          in_progress: 1,
          completed: 7,
          no_shows: 0,
          workload_percentage: 72
        },
        is_available: true,
        patient_queue: [
          { id: 1, token_number: "A-01", patient_name: "Arjun Sharma", mrn: "CA-MRN-48912", time: "10:30 AM", status: "waiting", reason: "Blood pressure evaluation" },
          { id: 2, token_number: "A-02", patient_name: "Suresh Ramanathan", mrn: "CA-MRN-48915", time: "11:00 AM", status: "waiting", reason: "Palpitations follow-up" },
          { id: 3, token_number: "A-03", patient_name: "Lakshmi Narayanan", mrn: "CA-MRN-48921", time: "11:30 AM", status: "waiting", reason: "ECG check" }
        ],
        workload_recommendation: null
      };
    }

    if (cleanUrl === '/doctor/availability') {
      return {
        schedules: [
          { day: "Monday", is_active: true, start_time: "09:00", end_time: "17:00" },
          { day: "Tuesday", is_active: true, start_time: "09:00", end_time: "17:00" },
          { day: "Wednesday", is_active: true, start_time: "09:00", end_time: "17:00" },
          { day: "Thursday", is_active: true, start_time: "09:00", end_time: "17:00" },
          { day: "Friday", is_active: true, start_time: "09:00", end_time: "17:00" },
          { day: "Saturday", is_active: true, start_time: "09:00", end_time: "13:00" }
        ],
        leaves: []
      };
    }

    if (cleanUrl === '/doctor/toggle-availability') {
      return { success: true, is_available: true };
    }

    if (cleanUrl.startsWith('/doctor/appointments/')) {
      return { success: true, message: "Appointment status updated" };
    }

    if (cleanUrl === '/doctor/consultation-notes') {
      return { success: true, message: "Clinical note and prescription signed and saved" };
    }

    if (cleanUrl.startsWith('/doctor/patient-profile/')) {
      return {
        patient: { id: 1, full_name: "Arjun Sharma", mrn: "CA-MRN-48912", age: 34, gender: "Male", blood_group: "O+" },
        history: MockStore.medical_history,
        reports: MockStore.health_reports
      };
    }

    if (cleanUrl === '/doctor/workload-metrics') {
      return {
        daily_utilization: 75,
        avg_consultation_minutes: 14,
        total_patients_this_week: 42,
        patient_satisfaction_score: 4.9
      };
    }

    // Admin routes
    if (cleanUrl === '/admin/dashboard') {
      return {
        metrics: {
          total_doctors: 38,
          total_patients: 1240,
          today_total_appointments: 94,
          today_completed: 62,
          current_waiting_patients: 14,
          available_doctors: 29
        },
        doctor_roster: MockStore.doctors,
        recent_ledger: [
          { time: "10:12 AM", event: "Patient CA-MRN-48912 checked in at Cardiology Suite 204" },
          { time: "09:55 AM", event: "Consultation note filed for Patient CA-MRN-48890 by Dr. Priya Sharma" },
          { time: "09:30 AM", event: "Priority Standby Slot claimed by Patient CA-MRN-48901" }
        ],
        departments: MockStore.departments
      };
    }

    if (cleanUrl === '/admin/doctors') {
      if (method === 'POST') {
        const body = JSON.parse(options.body || '{}');
        const newDoc = {
          id: Date.now(),
          full_name: body.full_name || "Dr. New Specialist, MD",
          department_id: body.department_id || 1,
          department_name: "Cardiology",
          specialization: body.specialization || "General Medicine",
          consultation_fee: body.consultation_fee || 800,
          experience_years: body.experience_years || 5,
          rating: 5.0,
          is_available: true,
          consultation_modes: ["In-Person", "Video"],
          room_number: body.room_number || "Clinic Suite 101"
        };
        MockStore.doctors.push(newDoc);
        return { success: true, doctor: newDoc };
      }
      return MockStore.doctors;
    }

    if (cleanUrl === '/admin/departments') {
      return MockStore.departments;
    }

    if (cleanUrl === '/admin/patients') {
      return [
        { id: 1, full_name: "Arjun Sharma", mrn: "CA-MRN-48912", phone: "+91 98401 55210", city: "Chennai", registered_at: "2026-01-10" },
        { id: 2, full_name: "Suresh Ramanathan", mrn: "CA-MRN-48915", phone: "+91 98401 33211", city: "Chennai", registered_at: "2026-02-14" },
        { id: 3, full_name: "Lakshmi Narayanan", mrn: "CA-MRN-48921", phone: "+91 98401 77654", city: "Bengaluru", registered_at: "2026-03-01" }
      ];
    }

    if (cleanUrl === '/patient/hospitals' || cleanUrl === '/admin/hospitals') {
      return MockStore.hospitals;
    }

    if (cleanUrl === '/admin/ledger') {
      return [
        { id: 1, timestamp: new Date().toISOString(), type: "Check-in", description: "Patient CA-MRN-48912 checked in", status: "Success" },
        { id: 2, timestamp: new Date(Date.now() - 3600000).toISOString(), type: "Consultation", description: "Telehealth video session concluded", status: "Success" }
      ];
    }

    if (cleanUrl === '/admin/audit-logs' || cleanUrl === '/admin/audit') {
      return [
        { id: 1, timestamp: new Date().toISOString(), user: "Admin (CMO)", action: "Department Roster Sync", status: "Verified" }
      ];
    }

    if (cleanUrl === '/admin/announcements') {
      return { success: true, message: "Announcement broadcasted to hospital channels" };
    }

    // Chatbot routes
    if (cleanUrl === '/chatbot/conversations') {
      if (method === 'POST') {
        const newConv = {
          id: `conv-${Date.now()}`,
          title: "New Clinical Consultation",
          created_at: new Date().toISOString(),
          messages: [
            { sender: "assistant", text: "Hello! I am your CareAura Assistant. How can I help you today?" }
          ]
        };
        MockStore.chat_conversations.unshift(newConv);
        return { success: true, conversation: newConv };
      }
      return MockStore.chat_conversations;
    }

    if (cleanUrl.startsWith('/chatbot/conversations/')) {
      const parts = cleanUrl.split('/');
      const convId = parts[3];
      const conv = MockStore.chat_conversations.find(c => c.id === convId) || MockStore.chat_conversations[0];

      if (cleanUrl.endsWith('/messages') && method === 'POST') {
        const body = JSON.parse(options.body || '{}');
        const userMsg = body.message || '';
        const userMsgObj = { sender: 'user', text: userMsg };
        conv.messages.push(userMsgObj);

        // Generate intelligent AI clinical reply
        let replyText = "Thank you for reaching out. Your query has been logged in CareAura Health OS.";
        let cards = null;
        let cardType = null;

        const lower = userMsg.toLowerCase();
        if (lower.includes('doctor') || lower.includes('specialist') || lower.includes('cardio') || lower.includes('heart')) {
          replyText = "Here are top available specialists matching your clinical need:";
          cardType = "doctor_list";
          cards = MockStore.doctors.slice(0, 3).map(d => ({
            id: d.id,
            title: d.full_name,
            subtitle: `${d.specialization} • ${d.hospital_name}`,
            action: `PatientModule.openBookingModal(${d.id})`,
            action_text: "Book Appointment"
          }));
        } else if (lower.includes('appointment') || lower.includes('book') || lower.includes('slot')) {
          replyText = "You can immediately book a priority consultation with our verified multi-specialty roster:";
          cardType = "action";
          cards = [{
            title: "Book Consultation Slot",
            subtitle: "Select doctor, consultation type (Video or In-Person), and time window.",
            action: "PatientModule.openBookingModal()",
            action_text: "Open Booking Portal"
          }];
        } else if (lower.includes('report') || lower.includes('lab') || lower.includes('test')) {
          replyText = "Your diagnostic reports are accessible under the Health Reports tab. All tests are certified and linked to your MRN.";
        } else {
          replyText = "I can assist you with booking doctor appointments, checking standby queues, reviewing lab reports, or finding accredited Indian multi-specialty hospitals.";
        }

        const botMsgObj = { sender: 'assistant', text: replyText, card_type: cardType, cards: cards };
        conv.messages.push(botMsgObj);

        return {
          success: true,
          message: botMsgObj
        };
      }

      if (cleanUrl.endsWith('/rename') && method === 'PUT') {
        const body = JSON.parse(options.body || '{}');
        if (conv) conv.title = body.title || conv.title;
        return { success: true };
      }

      if (method === 'DELETE') {
        const idx = MockStore.chat_conversations.findIndex(c => c.id === convId);
        if (idx !== -1) MockStore.chat_conversations.splice(idx, 1);
        return { success: true };
      }

      return conv;
    }

    // Default safe fallback response
    return { success: true, message: "OK (Clinical Fallback)" };
  },

  async request(endpoint, options = {}, retries = 1) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, config);

      let data = {};
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        data = await res.json();
      } else {
        const text = await res.text();
        data = { message: text };
      }

      // If Netlify or server returned 404 (or static HTML page not found error)
      if (res.status === 404 || !res.ok) {
        if (contentType.includes('text/html') || res.status === 404 || res.status === 502 || res.status === 503) {
          console.info(`[CareAura OS] Fallback triggered for: ${endpoint} (status ${res.status})`);
          return await this._handleMockFallback(endpoint, options);
        }
      }

      if (res.status === 401) {
        if (!endpoint.startsWith('/auth/login') && !endpoint.startsWith('/auth/register') && !endpoint.startsWith('/auth/verify-otp') && !endpoint.startsWith('/auth/quick-login')) {
          console.warn("Session expired or unauthorized.");
          this.clearToken();
        }
      }

      if (!res.ok) {
        throw new Error(data.detail || data.message || `Server returned error (${res.status})`);
      }
      return data;
    } catch (err) {
      if (err.name === 'AbortError') {
        return { __aborted: true };
      }

      // If connection failed (e.g. backend offline, sleeping, or not running), use the clinical fallback
      const isNetworkErr = !err.status && (err.name === 'TypeError' || (err.message && (err.message.toLowerCase().includes('failed to fetch') || err.message.toLowerCase().includes('networkerror') || err.message.toLowerCase().includes('load failed'))));

      if (isNetworkErr || (err.message && err.message.includes('404'))) {
        console.info(`[CareAura OS] Network offline/unreachable. Serving resilient mock fallback for: ${endpoint}`);
        try {
          return await this._handleMockFallback(endpoint, options);
        } catch (fallbackErr) {
          console.error("Fallback error:", fallbackErr);
        }
      }

      // Retry once on idempotent GET if network glitch
      if (retries > 0 && (!options.method || options.method === 'GET')) {
        await new Promise(r => setTimeout(r, 250));
        return this.request(endpoint, options, retries - 1);
      }

      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  get(endpoint, params = {}, options = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        query.append(k, v);
      }
    });
    const qs = query.toString();
    const url = qs ? `${endpoint}?${qs}` : endpoint;
    return this.request(url, { method: 'GET', ...options });
  },

  post(endpoint, body = {}, options = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options
    });
  },

  put(endpoint, body = {}, options = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
      ...options
    });
  },

  delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options });
  }
};

import re

with open("frontend/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update title and description
content = content.replace(
    "<title>AegisCare Clinical Operating System | Hospital Resource Platform</title>",
    "<title>CareSync Clinical OS | Indian Hospital Resource & Availability Platform</title>"
)
content = content.replace(
    'content="AegisCare optimizes doctor availability, smart appointment scheduling, patient flow, and clinical resource allocation through digital technology."',
    'content="CareSync Clinical OS optimizes doctor availability, intelligent appointment scheduling, patient flow, and clinical resource allocation across Indian multi-specialty hospitals."'
)

# 2. Update brand name
content = content.replace(
    '<span class="brand-title">AegisCare</span>',
    '<span class="brand-title">CareSync</span>'
)

# 3. Add Intro Overlay & Auth Modal right after <body>
intro_and_auth_html = '''<body>
  <!-- Healthcare Pulse Intro Animation Overlay -->
  <div id="intro-overlay" class="intro-overlay" onclick="dismissIntro()">
    <div class="intro-content">
      <div class="intro-logo-box">
        <svg class="intro-pulse-svg" viewBox="0 0 100 40">
          <polyline points="0,20 30,20 38,5 45,35 52,15 58,25 64,20 100,20" />
        </svg>
      </div>
      <h1 class="intro-brand">CareSync Clinical OS</h1>
      <p class="intro-tagline">Intelligent Hospital Appointment & Doctor Availability Optimization Platform</p>
      <div class="intro-loader-bar"><div class="intro-loader-progress"></div></div>
      <span class="intro-skip-hint">Click anywhere to proceed</span>
    </div>
  </div>

  <!-- Authentication Hub Modal -->
  <div class="modal-overlay" id="auth-modal">
    <div class="modal-card" style="max-width: 480px;">
      <div class="modal-header" style="text-align:center; display:block;">
        <h3 class="modal-title" style="font-size:1.25rem;">CareSync Clinical OS</h3>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">Indian Healthcare Access & Resource Platform</p>
      </div>
      <div class="modal-body">
        <div class="auth-tabs">
          <button class="auth-tab-btn active" id="auth-tab-otp-btn" onclick="switchAuthTab('otp')">Mobile OTP</button>
          <button class="auth-tab-btn" id="auth-tab-email-btn" onclick="switchAuthTab('email')">Email Login</button>
          <button class="auth-tab-btn" id="auth-tab-reg-btn" onclick="switchAuthTab('reg')">Sign Up</button>
        </div>

        <!-- Tab 1: Mobile OTP -->
        <div id="auth-panel-otp">
          <div id="otp-step-1">
            <label class="form-label">Mobile Number (+91 India)</label>
            <div style="display:flex; gap:8px;">
              <span style="display:flex; align-items:center; padding:0 12px; background:#f1f5f9; border:1px solid var(--border-medium); border-radius:var(--radius-md); font-weight:600; font-size:0.88rem; color:#475569;">+91</span>
              <input type="tel" id="auth-otp-phone" class="form-control" placeholder="98401 23456" maxlength="10" />
            </div>
            <button class="btn btn-primary" style="width:100%; margin-top:14px;" onclick="sendMobileOTP()">Get Verification Code</button>
          </div>

          <div id="otp-step-2" style="display:none; text-align:center;">
            <p style="font-size:0.85rem; color:var(--text-secondary);">Enter 6-digit verification code sent to <strong id="otp-masked-phone">+91 98401 *****</strong></p>
            <div class="otp-box-row">
              <input type="text" class="otp-digit" maxlength="1" oninput="handleOtpInput(this, 0)" onkeydown="handleOtpKey(event, 0)" />
              <input type="text" class="otp-digit" maxlength="1" oninput="handleOtpInput(this, 1)" onkeydown="handleOtpKey(event, 1)" />
              <input type="text" class="otp-digit" maxlength="1" oninput="handleOtpInput(this, 2)" onkeydown="handleOtpKey(event, 2)" />
              <input type="text" class="otp-digit" maxlength="1" oninput="handleOtpInput(this, 3)" onkeydown="handleOtpKey(event, 3)" />
              <input type="text" class="otp-digit" maxlength="1" oninput="handleOtpInput(this, 4)" onkeydown="handleOtpKey(event, 4)" />
              <input type="text" class="otp-digit" maxlength="1" oninput="handleOtpInput(this, 5)" onkeydown="handleOtpKey(event, 5)" />
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; margin:12px 0;">
              <span id="otp-timer-text" style="color:var(--text-muted);">Resend code in <strong>30s</strong></span>
              <button id="otp-resend-btn" class="btn btn-secondary btn-sm" style="display:none;" onclick="sendMobileOTP()">Resend OTP</button>
              <button class="btn btn-secondary btn-sm" onclick="resetOtpStep()">Change Number</button>
            </div>
            <button class="btn btn-teal" style="width:100%;" onclick="verifyMobileOTP()">Verify & Continue</button>
          </div>
        </div>

        <!-- Tab 2: Email Login -->
        <div id="auth-panel-email" style="display:none;">
          <div class="form-group">
            <label class="form-label">Hospital Email ID</label>
            <input type="email" id="auth-email-input" class="form-control" placeholder="doctor@caresync.in or user@email.in" />
          </div>
          <div class="form-group">
            <div style="display:flex; justify-content:space-between;">
              <label class="form-label">Password</label>
              <a href="javascript:void(0)" style="font-size:0.75rem; color:var(--color-brand-primary);" onclick="showToast('Password reset link sent to registered email.', 'info')">Forgot?</a>
            </div>
            <div style="position:relative;">
              <input type="password" id="auth-password-input" class="form-control" placeholder="••••••••" />
              <button type="button" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); border:none; background:transparent; cursor:pointer; color:var(--text-muted);" onclick="togglePasswordVisibility('auth-password-input')">👁️</button>
            </div>
          </div>
          <button class="btn btn-primary" style="width:100%; margin-top:8px;" onclick="submitEmailLogin()">Sign In to Hospital Portal</button>
        </div>

        <!-- Tab 3: Sign Up -->
        <div id="auth-panel-reg" style="display:none;">
          <div class="form-group">
            <label class="form-label">I am registering as a:</label>
            <div style="display:flex; gap:10px;">
              <label style="flex:1; display:flex; align-items:center; gap:8px; padding:10px; border:1px solid var(--border-medium); border-radius:var(--radius-md); cursor:pointer;">
                <input type="radio" name="reg-role" value="patient" checked onchange="updateRegFields()" />
                <span style="font-weight:600; font-size:0.85rem;">Patient</span>
              </label>
              <label style="flex:1; display:flex; align-items:center; gap:8px; padding:10px; border:1px solid var(--border-medium); border-radius:var(--radius-md); cursor:pointer;">
                <input type="radio" name="reg-role" value="doctor" onchange="updateRegFields()" />
                <span style="font-weight:600; font-size:0.85rem;">Doctor / Consultant</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Full Name</label>
            <input type="text" id="reg-name-input" class="form-control" placeholder="e.g. Ramesh Krishnan" />
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div class="form-group">
              <label class="form-label">Email Address</label>
              <input type="email" id="reg-email-input" class="form-control" placeholder="ramesh@gmail.com" />
            </div>
            <div class="form-group">
              <label class="form-label">Mobile (+91)</label>
              <input type="tel" id="reg-phone-input" class="form-control" placeholder="98401 23456" maxlength="10" />
            </div>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
            <div class="form-group">
              <label class="form-label">Metro City</label>
              <select id="reg-city-select" class="form-control">
                <option value="Chennai">Chennai</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Bengaluru">Bengaluru</option>
                <option value="Hyderabad">Hyderabad</option>
                <option value="Vijayawada">Vijayawada</option>
                <option value="Pune">Pune</option>
                <option value="Delhi">Delhi</option>
                <option value="Kochi">Kochi</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Preferred Language</label>
              <select id="reg-lang-select" class="form-control">
                <option value="English">English</option>
                <option value="Hindi">Hindi</option>
                <option value="Tamil">Tamil</option>
                <option value="Telugu">Telugu</option>
                <option value="Kannada">Kannada</option>
                <option value="Malayalam">Malayalam</option>
              </select>
            </div>
          </div>
          <div id="reg-doctor-extra" style="display:none;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
              <div class="form-group">
                <label class="form-label">Clinical Specialization</label>
                <input type="text" id="reg-doc-spec" class="form-control" placeholder="e.g. Cardiologist" />
              </div>
              <div class="form-group">
                <label class="form-label">NMC License Number</label>
                <input type="text" id="reg-doc-lic" class="form-control" placeholder="NMC-TN-48912" />
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" id="reg-pw-input" class="form-control" placeholder="Minimum 6 characters" oninput="checkPasswordStrength(this.value)" />
            <div class="pw-meter-bar"><div id="reg-pw-meter" class="pw-meter-fill"></div></div>
          </div>
          <button class="btn btn-teal" style="width:100%; margin-top:8px;" onclick="submitRegistration()">Create Account</button>
        </div>

        <!-- Google Login Divider & Button -->
        <div class="auth-divider"><span>or continue with</span></div>
        <button class="btn-google" onclick="continueWithGoogle()">
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
          </svg>
          Google Sandbox Sign-In
        </button>
      </div>
      <div class="modal-footer" style="justify-content:center; padding:12px; background:#f8fafc;">
        <span style="font-size:0.75rem; color:var(--text-muted);">Quick Testing: Use role switcher pills at the top bar anytime.</span>
      </div>
    </div>
  </div>'''

content = content.replace("<body>", intro_and_auth_html, 1)

# 4. Replace entire sidebar content with complete 17 Doctor & 16 Admin views + Patient views
sidebar_content_old = content[content.find('<div class="sidebar-content">'):content.find('</div>\n\n      <div class="sidebar-footer">')]

sidebar_content_new = '''<div class="sidebar-content">
        <!-- Patient Navigation Group -->
        <div id="nav-group-patient">
          <div class="nav-group-title">Patient Portal</div>
          <ul class="nav-list">
            <li>
              <a class="nav-link active" data-view="patient-dashboard">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
                <span>Dashboard Overview</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-doctors">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                <span>Find Doctors</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-hospitals">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg>
                <span>Indian Hospitals</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-appointments">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg>
                <span>My Appointments</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-waitlist">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
                <span>Standby Waitlist</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-timeline">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
                <span>Clinical Timeline</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-history">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
                <span>Medical History</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="patient-reports">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <span>Health Reports</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="profile">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <span>My Profile</span>
              </a>
            </li>
            <li>
              <a class="nav-link" data-view="logout" onclick="handleLogout()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                <span>Sign Out</span>
              </a>
            </li>
          </ul>
        </div>

        <!-- Doctor Navigation Group (17 Views) -->
        <div id="nav-group-doctor" style="display: none;">
          <div class="nav-group-title">Physician Workspace</div>
          <ul class="nav-list">
            <li><a class="nav-link" data-view="doctor-dashboard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg><span>1. Clinical Queue</span></a></li>
            <li><a class="nav-link" data-view="doctor-appointments"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg><span>2. Appointments</span></a></li>
            <li><a class="nav-link" data-view="doctor-schedule"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>3. Today's Schedule</span></a></li>
            <li><a class="nav-link" data-view="doctor-calendar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="M8 2v4"/><path d="M16 2v4"/></svg><span>4. Consultation Calendar</span></a></li>
            <li><a class="nav-link" data-view="doctor-patients"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/></svg><span>5. My Patients</span></a></li>
            <li><a class="nav-link" data-view="doctor-patient-history"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg><span>6. Patient Records</span></a></li>
            <li><a class="nav-link" data-view="doctor-reports"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span>7. Diagnostic Reports</span></a></li>
            <li><a class="nav-link" data-view="doctor-notes"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg><span>8. Consultation Notes</span></a></li>
            <li><a class="nav-link" data-view="doctor-prescriptions"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg><span>9. Electronic Rx</span></a></li>
            <li><a class="nav-link" data-view="doctor-availability"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>10. Roster & Hours</span></a></li>
            <li><a class="nav-link" data-view="doctor-leave"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/></svg><span>11. Leave Management</span></a></li>
            <li><a class="nav-link" data-view="doctor-queue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg><span>12. Live Waiting Room</span></a></li>
            <li><a class="nav-link" data-view="doctor-notifications"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg><span>13. Clinical Alerts</span></a></li>
            <li><a class="nav-link" data-view="doctor-workload"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg><span>14. Workload Analytics</span></a></li>
            <li><a class="nav-link" data-view="profile"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>15. Physician Profile</span></a></li>
            <li><a class="nav-link" data-view="doctor-settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg><span>16. Clinic Settings</span></a></li>
            <li><a class="nav-link" data-view="logout" onclick="handleLogout()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg><span>17. Sign Out</span></a></li>
          </ul>
        </div>

        <!-- Admin Navigation Group (16 Views) -->
        <div id="nav-group-admin" style="display: none;">
          <div class="nav-group-title">Hospital Administration</div>
          <ul class="nav-list">
            <li><a class="nav-link" data-view="admin-dashboard"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg><span>1. Command Center</span></a></li>
            <li><a class="nav-link" data-view="admin-doctors"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg><span>2. Doctor Roster</span></a></li>
            <li><a class="nav-link" data-view="admin-patients"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg><span>3. Patients Registry</span></a></li>
            <li><a class="nav-link" data-view="admin-hospitals"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg><span>4. Hospital Facilities</span></a></li>
            <li><a class="nav-link" data-view="admin-departments"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 21h18"/><path d="M9 9h1"/><path d="M9 13h1"/><path d="M9 17h1"/></svg><span>5. Departments</span></a></li>
            <li><a class="nav-link" data-view="admin-ledger"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg><span>6. Ledger</span></a></li>
            <li><a class="nav-link" data-view="admin-availability"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>7. Doctor Rosters</span></a></li>
            <li><a class="nav-link" data-view="admin-scheduling"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/><path d="M8 2v4"/><path d="M16 2v4"/></svg><span>8. Shift Scheduling</span></a></li>
            <li><a class="nav-link" data-view="admin-waitlist"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg><span>9. Waitlist Automation</span></a></li>
            <li><a class="nav-link" data-view="admin-analytics"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg><span>10. Resource Analytics</span></a></li>
            <li><a class="nav-link" data-view="admin-insights"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg><span>11. AI Forecasting</span></a></li>
            <li><a class="nav-link" data-view="admin-reports"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span>12. Audit Reports</span></a></li>
            <li><a class="nav-link" data-view="admin-notifications"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg><span>13. Announcements</span></a></li>
            <li><a class="nav-link" data-view="admin-audit"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg><span>14. Governance Logs</span></a></li>
            <li><a class="nav-link" data-view="admin-settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg><span>15. Hospital Settings</span></a></li>
            <li><a class="nav-link" data-view="profile"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span>16. Profile / Sign Out</span></a></li>
          </ul>
        </div>'''

content = content.replace(sidebar_content_old, sidebar_content_new, 1)

# 5. Make user quick profile clickable
content = content.replace(
    '<div class="user-quick-profile">',
    '<div class="user-quick-profile" onclick="navigateToView(\'profile\')" style="cursor:pointer;" title="Click to view & edit your profile">'
)

# 6. Change Consultation Fee ($) to Consultation Fee (₹)
content = content.replace('Consultation Fee ($)', 'Consultation Fee (₹)')

# 7. Add new view sections before </main>
new_views_html = '''
        <!-- PATIENT HOSPITALS VIEW -->
        <section class="view-section" id="view-patient-hospitals">
          <div class="section-header-bar" style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:14px; margin-bottom:20px;">
            <div>
              <h2 style="font-size:1.3rem; font-weight:700;">Multi-Specialty Indian Hospitals</h2>
              <p style="color:var(--text-secondary); font-size:0.85rem;">Accredited healthcare centers, specialty institutes & 24x7 trauma wings</p>
            </div>
            <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
              <select id="hosp-city-filter" class="filter-select" onchange="PatientModule.filterHospitals()">
                <option value="all">All Cities</option>
                <option value="Chennai">Chennai</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Bengaluru">Bengaluru</option>
                <option value="Hyderabad">Hyderabad</option>
                <option value="Vijayawada">Vijayawada</option>
                <option value="Pune">Pune</option>
                <option value="Delhi">Delhi</option>
                <option value="Kochi">Kochi</option>
              </select>
              <input type="text" id="hosp-search-input" class="form-control" style="width:200px; padding:7px 12px; font-size:0.84rem;" placeholder="Search hospital or locality..." oninput="PatientModule.filterHospitals()" />
              <label style="display:flex; align-items:center; gap:6px; font-size:0.82rem; cursor:pointer; font-weight:500;">
                <input type="checkbox" id="hosp-emergency-toggle" onchange="PatientModule.filterHospitals()" />
                <span>24x7 Emergency</span>
              </label>
            </div>
          </div>
          <div id="patient-hospitals-grid" class="doctor-grid"></div>
        </section>

        <!-- DYNAMIC CLINICAL PROFILE VIEW -->
        <section class="view-section" id="view-profile">
          <div class="profile-container">
            <div class="profile-header-card">
              <img id="prof-avatar" src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150" alt="Avatar" class="profile-avatar-large" />
              <div class="profile-main-meta">
                <div class="profile-name-row">
                  <h2 id="prof-full-name">Jane Doe</h2>
                  <span id="prof-role-badge" class="status-badge badge-confirmed">PATIENT</span>
                </div>
                <div class="profile-sub-meta">
                  <span id="prof-identifier">MRN: AC-MRN-90412</span>
                  <span id="prof-email">jane.doe@example.in</span>
                  <span id="prof-city">📍 Chennai, Tamil Nadu</span>
                  <span id="prof-language">🗣️ English, Tamil</span>
                </div>
              </div>
              <div class="profile-actions">
                <button class="btn btn-primary btn-sm" onclick="openEditProfileModal()">✏️ Edit Profile</button>
              </div>
            </div>

            <!-- Dynamic Profile Details Grid -->
            <div class="profile-details-grid" id="prof-details-grid"></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: APPOINTMENTS -->
        <section class="view-section" id="view-doctor-appointments">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <div>
                <h3 class="card-title">Consultation Ledger & Patient Bookings</h3>
                <p style="font-size:0.8rem; color:var(--text-muted);">Manage scheduled, in-progress, completed, and rescheduled appointments</p>
              </div>
              <div style="display:flex; gap:8px;">
                <button class="btn btn-secondary btn-sm" onclick="DoctorModule.loadAppointments('all')">All</button>
                <button class="btn btn-secondary btn-sm" onclick="DoctorModule.loadAppointments('scheduled')">Scheduled</button>
                <button class="btn btn-secondary btn-sm" onclick="DoctorModule.loadAppointments('completed')">Completed</button>
              </div>
            </div>
            <div class="clinical-table-container">
              <table class="clinical-table">
                <thead><tr><th>Time & ID</th><th>Patient</th><th>Type</th><th>Status</th><th>Reason</th><th style="text-align:right;">Actions</th></tr></thead>
                <tbody id="doc-all-appts-body"></tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- DOCTOR VIEW: TODAY'S SCHEDULE -->
        <section class="view-section" id="view-doctor-schedule">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Today's Clinical Roster & Consultation Time Slots</h3>
            <div id="doc-schedule-timeline-container" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:12px;"></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: CALENDAR -->
        <section class="view-section" id="view-doctor-calendar">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <h3 class="card-title">Monthly Consultation Calendar</h3>
              <span style="font-size:0.85rem; color:var(--text-muted);">Clinic OPD Working Hours: Mon - Sat (09:00 - 17:00 IST)</span>
            </div>
            <div id="doc-calendar-grid" style="display:grid; grid-template-columns:repeat(7, 1fr); gap:8px; text-align:center;"></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: MY PATIENTS -->
        <section class="view-section" id="view-doctor-patients">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
              <h3 class="card-title">Registered Patients Directory</h3>
              <input type="text" placeholder="Search by name or MRN..." class="form-control" style="width:240px; font-size:0.84rem;" oninput="DoctorModule.filterPatients(this.value)" />
            </div>
            <div class="clinical-table-container">
              <table class="clinical-table">
                <thead><tr><th>Patient Name</th><th>MRN</th><th>City & Phone</th><th>Blood Group</th><th>Allergies</th><th style="text-align:right;">Chart</th></tr></thead>
                <tbody id="doc-patients-list-body"></tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- DOCTOR VIEW: PATIENT RECORDS & HISTORY -->
        <section class="view-section" id="view-doctor-patient-history">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Electronic Medical Records & Chart Review</h3>
            <div id="doc-patient-history-viewer"><p style="color:var(--text-muted); font-size:0.85rem;">Select any patient from the Clinical Queue or Patients directory to view electronic medical records.</p></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: DIAGNOSTIC REPORTS -->
        <section class="view-section" id="view-doctor-reports">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Diagnostic Lab & Radiology Reports</h3>
            <div class="clinical-table-container">
              <table class="clinical-table">
                <thead><tr><th>Report Title</th><th>Type</th><th>Patient</th><th>Facility</th><th>Date</th><th style="text-align:right;">Action</th></tr></thead>
                <tbody id="doc-reports-table-body"></tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- DOCTOR VIEW: CONSULTATION NOTES -->
        <section class="view-section" id="view-doctor-notes">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Clinical Consultation Notes Archive</h3>
            <div id="doc-notes-archive-container"></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: ELECTRONIC PRESCRIPTIONS -->
        <section class="view-section" id="view-doctor-prescriptions">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Issued Electronic Prescriptions (Rx)</h3>
            <div class="clinical-table-container">
              <table class="clinical-table">
                <thead><tr><th>Rx Date</th><th>Patient</th><th>Medications Documented</th><th>Instructions</th><th style="text-align:right;">Print / View</th></tr></thead>
                <tbody id="doc-prescriptions-table-body"></tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- DOCTOR VIEW: LEAVE MANAGEMENT -->
        <section class="view-section" id="view-doctor-leave">
          <div class="stat-grid" style="grid-template-columns:1fr 2fr; gap:20px;">
            <div class="clinical-card">
              <h3 class="card-title" style="margin-bottom:12px;">Request Clinic Leave</h3>
              <div class="form-group">
                <label class="form-label">Leave Type</label>
                <select class="form-control" id="doc-leave-type"><option value="Casual Leave">Casual Leave</option><option value="Medical Leave">Medical Leave</option><option value="Conference / Academic">Conference / Academic</option></select>
              </div>
              <div class="form-group"><label class="form-label">Start Date</label><input type="date" class="form-control" id="doc-leave-start" /></div>
              <div class="form-group"><label class="form-label">End Date</label><input type="date" class="form-control" id="doc-leave-end" /></div>
              <div class="form-group"><label class="form-label">Reason</label><textarea class="form-control" id="doc-leave-reason" placeholder="Details..."></textarea></div>
              <button class="btn btn-primary" onclick="DoctorModule.submitLeaveRequest()">Submit Request</button>
            </div>
            <div class="clinical-card">
              <h3 class="card-title" style="margin-bottom:12px;">Upcoming & Past Leave Records</h3>
              <div id="doc-leave-history-list"><p style="color:var(--text-muted); font-size:0.85rem;">No active leave requests submitted this month.</p></div>
            </div>
          </div>
        </section>

        <!-- DOCTOR VIEW: LIVE WAITING ROOM QUEUE -->
        <section class="view-section" id="view-doctor-queue">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <h3 class="card-title">Live Waiting Room Monitor</h3>
              <button class="btn btn-teal btn-sm" onclick="DoctorModule.loadQueue()">🔄 Refresh Queue</button>
            </div>
            <div id="doc-queue-expanded-container"></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: CLINICAL NOTIFICATIONS -->
        <section class="view-section" id="view-doctor-notifications">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Clinical Alerts & Roster Updates</h3>
            <div id="doc-notifications-list"></div>
          </div>
        </section>

        <!-- DOCTOR VIEW: CLINIC SETTINGS -->
        <section class="view-section" id="view-doctor-settings">
          <div class="clinical-card" style="max-width:680px;">
            <h3 class="card-title" style="margin-bottom:16px;">Physician Practice & OPD Settings</h3>
            <div class="form-group">
              <label class="form-label">Consultation Fee (₹ INR)</label>
              <input type="number" id="doc-setting-fee" class="form-control" value="800" />
            </div>
            <div class="form-group">
              <label class="form-label">Slot Consultation Duration (Minutes)</label>
              <select class="form-control" id="doc-setting-duration"><option value="15">15 mins</option><option value="20" selected>20 mins</option><option value="30">30 mins</option></select>
            </div>
            <div class="form-group">
              <label class="form-label">Languages Spoken</label>
              <input type="text" id="doc-setting-langs" class="form-control" value="English, Hindi, Tamil" />
            </div>
            <button class="btn btn-teal" onclick="DoctorModule.saveSettings()">Save OPD Preferences</button>
          </div>
        </section>

        <!-- ADMIN VIEW: PATIENTS REGISTRY -->
        <section class="view-section" id="view-admin-patients">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <h3 class="card-title">Hospital Master Patient Registry</h3>
              <input type="text" placeholder="Search MRN or name..." class="form-control" style="width:240px; font-size:0.84rem;" oninput="AdminModule.filterPatients(this.value)" />
            </div>
            <div class="clinical-table-container">
              <table class="clinical-table">
                <thead><tr><th>Patient MRN</th><th>Full Name</th><th>City</th><th>Language</th><th>Blood Group</th><th>Allergies</th></tr></thead>
                <tbody id="adm-patients-table-body"></tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- ADMIN VIEW: HOSPITAL FACILITIES -->
        <section class="view-section" id="view-admin-hospitals">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <h3 class="card-title">Hospital Facilities & Metro Units Directory</h3>
              <span style="font-size:0.82rem; color:var(--text-muted);">12 Partner Facilities Active Across Indian Metros</span>
            </div>
            <div class="clinical-table-container">
              <table class="clinical-table">
                <thead><tr><th>Facility</th><th>City & Locality</th><th>Bed Capacity</th><th>ICU Beds</th><th>24x7 Emergency</th><th>Base Fee (₹)</th><th>Rating</th></tr></thead>
                <tbody id="adm-hospitals-table-body"></tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- ADMIN VIEW: DOCTOR ROSTERS & AVAILABILITY -->
        <section class="view-section" id="view-admin-availability">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Physician Shift Availability & Working Rosters</h3>
            <div id="adm-availability-roster-body"></div>
          </div>
        </section>

        <!-- ADMIN VIEW: SHIFT SCHEDULING -->
        <section class="view-section" id="view-admin-scheduling">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Automated Shift Scheduling & Capacity Optimization</h3>
            <div id="adm-scheduling-container">
              <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:16px;">AI shift engine balances morning, evening, and on-call rotations based on historical patient arrival volume.</p>
              <button class="btn btn-teal btn-sm" onclick="AdminModule.runScheduleOptimization()">⚡ Run AI Roster Optimizer</button>
            </div>
          </div>
        </section>

        <!-- ADMIN VIEW: COMPLIANCE & AUDIT REPORTS -->
        <section class="view-section" id="view-admin-reports">
          <div class="clinical-card">
            <h3 class="card-title" style="margin-bottom:14px;">Hospital Operational & Clinical Governance Reports</h3>
            <div id="adm-reports-list" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:16px;"></div>
          </div>
        </section>

        <!-- ADMIN VIEW: ANNOUNCEMENTS -->
        <section class="view-section" id="view-admin-notifications">
          <div class="clinical-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
              <h3 class="card-title">Hospital Broadcast Announcements</h3>
              <button class="btn btn-primary btn-sm" onclick="document.getElementById('announcement-modal').classList.add('active')">+ Create Announcement</button>
            </div>
            <div id="adm-announcements-list"></div>
          </div>
        </section>

        <!-- ADMIN VIEW: SYSTEM SETTINGS -->
        <section class="view-section" id="view-admin-settings">
          <div class="clinical-card" style="max-width:680px;">
            <h3 class="card-title" style="margin-bottom:16px;">CareSync Clinical OS Platform Settings</h3>
            <div class="form-group"><label class="form-label">Hospital Operating System Region</label><input type="text" class="form-control" value="India (IST - UTC+5:30)" disabled /></div>
            <div class="form-group"><label class="form-label">Currency Standard</label><input type="text" class="form-control" value="₹ (Indian Rupee - INR)" disabled /></div>
            <div class="form-group"><label class="form-label">Standby Auto-Allocation Algorithm</label><select class="form-control"><option selected>Multi-Factor Clinical Suitability & Workload Balancing (Default)</option><option>Fastest Available Slot First</option><option>Continuity of Care First</option></select></div>
            <div class="form-group"><label class="form-label">Max Shift Capacity per Physician</label><input type="number" class="form-control" value="25" /></div>
            <button class="btn btn-teal" onclick="showToast('System configuration saved successfully.', 'success')">Save Global Settings</button>
          </div>
        </section>
'''

content = content.replace('</main>', new_views_html + '\n      </main>', 1)

# 8. Add Edit Profile Modal before closing </body>
edit_profile_modal_html = '''
  <!-- 12. Edit User Profile Modal -->
  <div class="modal-overlay" id="edit-profile-modal">
    <div class="modal-card" style="max-width:560px;">
      <div class="modal-header">
        <h3 class="modal-title">Edit Clinical Profile</h3>
        <button class="modal-close-btn" onclick="document.getElementById('edit-profile-modal').classList.remove('active')">&times;</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">Full Name</label>
          <input type="text" class="form-control" id="edit-prof-name" />
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
          <div class="form-group">
            <label class="form-label">Phone (+91)</label>
            <input type="tel" class="form-control" id="edit-prof-phone" maxlength="10" />
          </div>
          <div class="form-group">
            <label class="form-label">City</label>
            <select class="form-control" id="edit-prof-city">
              <option value="Chennai">Chennai</option>
              <option value="Mumbai">Mumbai</option>
              <option value="Bengaluru">Bengaluru</option>
              <option value="Hyderabad">Hyderabad</option>
              <option value="Vijayawada">Vijayawada</option>
              <option value="Pune">Pune</option>
              <option value="Delhi">Delhi</option>
              <option value="Kochi">Kochi</option>
            </select>
          </div>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
          <div class="form-group">
            <label class="form-label">Preferred Language</label>
            <select class="form-control" id="edit-prof-lang">
              <option value="English">English</option>
              <option value="Hindi">Hindi</option>
              <option value="Tamil">Tamil</option>
              <option value="Telugu">Telugu</option>
              <option value="Kannada">Kannada</option>
              <option value="Malayalam">Malayalam</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Avatar Image URL</label>
            <input type="text" class="form-control" id="edit-prof-avatar" placeholder="https://..." />
          </div>
        </div>
        <div class="form-group" id="edit-prof-pat-fields">
          <label class="form-label">Known Allergies (Comma separated)</label>
          <input type="text" class="form-control" id="edit-prof-allergies" placeholder="e.g. Penicillin, Sulfa drugs" />
          <label class="form-label" style="margin-top:8px;">Chronic Conditions (Comma separated)</label>
          <input type="text" class="form-control" id="edit-prof-chronic" placeholder="e.g. Hypertension, Type 2 Diabetes" />
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary modal-cancel-btn" onclick="document.getElementById('edit-profile-modal').classList.remove('active')">Cancel</button>
        <button class="btn btn-teal" onclick="saveUserProfile()">Save Profile Changes</button>
      </div>
    </div>
  </div>
'''

content = content.replace('<!-- Toast Container -->', edit_profile_modal_html + '\n  <!-- Toast Container -->', 1)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("index.html updated successfully!")

// CareAura Health OS Master Application Controller
let otpTimerInterval = null;
let currentOtpSeconds = 30;

document.addEventListener('DOMContentLoaded', async () => {
  AppState.init();

  // Restore existing session or default to patient Arjun Sharma
  const token = api.getToken();
  const cachedUser = api.getCurrentUser();

  if (token && cachedUser) {
    AppState.currentUser = cachedUser;
    updateUserInterface();
    // Background verify session
    api.get('/auth/me').then(meData => {
      if (meData && meData.id) {
        AppState.currentUser = meData;
        api.setCurrentUser(meData);
        updateUserInterface();
      }
    }).catch(err => {
      console.warn('Session verification note:', err.message);
    });
  } else {
    await switchRole('patient');
  }

  // Preload departments and doctors cache
  try {
    AppState.allDepartments = await api.get('/patient/departments');
    AppState.allDoctors = await api.get('/patient/doctors');
  } catch (err) {
    console.warn('Initial metadata preload:', err);
  }

  // Automatic intro animation transition after ~2s
  setTimeout(() => {
    dismissIntro();
  }, 2200);

  setupEventListeners();
  initRouting();

  window.addEventListener('popstate', () => {
    const r = resolveRouteFromUrl();
    const u = AppState.currentUser;
    const rl = u ? u.role : 'patient';
    const d = rl === 'doctor' ? 'doctor-dashboard' : (rl === 'admin' ? 'admin-dashboard' : 'patient-dashboard');
    if (r.type === 'view' && r.viewId) {
      navigateToView(r.viewId, false);
    } else {
      navigateToView(d, false);
    }
  });
});

/* ================= INTRO ANIMATION CONTROLLER ================= */
function dismissIntro() {
  const introEl = document.getElementById('intro-overlay');
  if (introEl && !introEl.classList.contains('dismissed')) {
    introEl.classList.add('dismissed');
    setTimeout(() => {
      introEl.style.display = 'none';
      // User requirement: authentication page appears immediately after animation on initial app open
      if (!sessionStorage.getItem('careaura_auth_passed')) {
        openAuthModal();
      }
    }, 650);
  }
}

/* ================= MOBILE SIDEBAR NAVIGATION ================= */
function toggleMobileSidebar() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.toggle('mobile-open');
}

document.addEventListener('click', (e) => {
  const sb = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('mobile-sidebar-toggle');
  if (sb && sb.classList.contains('mobile-open')) {
    if (!sb.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
      sb.classList.remove('mobile-open');
    }
  }
  if (e.target.closest('.nav-link') && window.innerWidth <= 900) {
    document.getElementById('sidebar')?.classList.remove('mobile-open');
  }
});

/* ================= AUTHENTICATION HUB ================= */
function openAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.classList.add('active');
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.classList.remove('active');
  sessionStorage.setItem('careaura_auth_passed', 'true');
  const view = AppState.currentView || 'patient-dashboard';
  navigateToView(view, false);
}

function switchAuthTab(tab) {
  document.querySelectorAll('.auth-tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`auth-tab-${tab}-btn`)?.classList.add('active');

  document.getElementById('auth-panel-otp').style.display = tab === 'otp' ? 'block' : 'none';
  document.getElementById('auth-panel-email').style.display = tab === 'email' ? 'block' : 'none';
  document.getElementById('auth-panel-reg').style.display = tab === 'reg' ? 'block' : 'none';
}

function togglePasswordVisibility(inputId) {
  const el = document.getElementById(inputId);
  if (el) el.type = el.type === 'password' ? 'text' : 'password';
}

function onPhoneInputChange(input) {
  input.value = input.value.replace(/\D/g, '').slice(0, 10);
  const errEl = document.getElementById('auth-phone-error');
  if (errEl) errEl.style.display = 'none';
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';
}

async function sendMobileOTP() {
  const phoneInput = document.getElementById('auth-otp-phone');
  const phone = phoneInput ? phoneInput.value.trim() : '';
  const errEl = document.getElementById('auth-phone-error');
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';

  // Strict 10-digit validation: accept only exactly 10 digits
  if (!/^\d{10}$/.test(phone)) {
    if (errEl) {
      errEl.textContent = 'Enter a valid 10-digit mobile number.';
      errEl.style.display = 'block';
    }
    showToast('Enter a valid 10-digit mobile number.', 'error');
    phoneInput?.focus();
    return;
  }
  if (errEl) errEl.style.display = 'none';

  const btn = document.getElementById('btn-get-otp');
  const origText = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Sending OTP...'; }

  try {
    const res = await api.post('/auth/send-otp', { phone: `+91${phone}` });
    showToast(res.message || 'OTP sent securely to your mobile number!', 'success');

    // Update masked phone
    const masked = `+91 ${phone.substring(0, 5)} *****`;
    const maskedEl = document.getElementById('otp-masked-phone');
    if (maskedEl) maskedEl.textContent = masked;

    // Switch to step 2 (OTP is never displayed on interface)
    document.getElementById('otp-step-1').style.display = 'none';
    document.getElementById('otp-step-2').style.display = 'block';

    // Clear digit inputs and focus first
    for (let i = 0; i < 6; i++) {
      const b = document.getElementById(`otp-d-${i}`);
      if (b) b.value = '';
    }
    document.getElementById('otp-d-0')?.focus();

    // Start 30s countdown
    startOtpCountdown();
  } catch (err) {
    if (alertEl) {
      alertEl.textContent = err.message || 'Failed to send OTP';
      alertEl.style.display = 'flex';
    }
    showToast('Failed to send OTP: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = origText; }
  }
}

function resetOtpStep() {
  if (otpTimerInterval) clearInterval(otpTimerInterval);
  document.getElementById('otp-step-2').style.display = 'none';
  document.getElementById('otp-step-1').style.display = 'block';
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';
  document.getElementById('auth-otp-phone')?.focus();
}

function startOtpCountdown() {
  if (otpTimerInterval) clearInterval(otpTimerInterval);
  currentOtpSeconds = 30;

  const timerText = document.getElementById('otp-timer-text');
  const resendBtn = document.getElementById('otp-resend-btn');
  if (resendBtn) resendBtn.style.display = 'none';

  otpTimerInterval = setInterval(() => {
    currentOtpSeconds--;
    if (timerText) {
      timerText.innerHTML = `Resend code in <strong>${currentOtpSeconds}s</strong>`;
    }
    if (currentOtpSeconds <= 0) {
      clearInterval(otpTimerInterval);
      if (timerText) timerText.textContent = 'Did not receive code?';
      if (resendBtn) resendBtn.style.display = 'inline-block';
    }
  }, 1000);
}

function handleOtpInput(input, index) {
  input.value = input.value.replace(/\D/g, '').slice(-1);
  if (input.value && index < 5) {
    document.getElementById(`otp-d-${index + 1}`)?.focus();
  }
}

function handleOtpKey(event, index) {
  if (event.key === 'Backspace') {
    if (!event.target.value && index > 0) {
      const prev = document.getElementById(`otp-d-${index - 1}`);
      if (prev) {
        prev.value = '';
        prev.focus();
      }
    }
  } else if (event.key === 'ArrowLeft' && index > 0) {
    document.getElementById(`otp-d-${index - 1}`)?.focus();
  } else if (event.key === 'ArrowRight' && index < 5) {
    document.getElementById(`otp-d-${index + 1}`)?.focus();
  } else if (event.key === 'Enter') {
    verifyMobileOTP();
  }
}

function handleOtpPaste(event) {
  event.preventDefault();
  const pasteData = (event.clipboardData || window.clipboardData).getData('text').trim();
  const clean = pasteData.replace(/\D/g, '').slice(0, 6);
  if (clean.length > 0) {
    const chars = clean.split('');
    for (let i = 0; i < 6; i++) {
      const box = document.getElementById(`otp-d-${i}`);
      if (box) box.value = chars[i] || '';
    }
    const focusIdx = Math.min(chars.length, 5);
    document.getElementById(`otp-d-${focusIdx}`)?.focus();
    if (clean.length === 6) {
      showToast('Pasted 6-digit OTP code', 'info');
    }
  }
}

async function verifyMobileOTP() {
  let digits = '';
  for (let i = 0; i < 6; i++) {
    digits += (document.getElementById(`otp-d-${i}`)?.value || '').trim();
  }
  const phone = document.getElementById('auth-otp-phone')?.value.trim();
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';

  if (!digits || digits.length !== 6 || !/^\d{6}$/.test(digits)) {
    showToast('Please enter all 6 digits of the OTP code.', 'error');
    return;
  }

  const btn = document.getElementById('btn-verify-otp');
  const origText = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Verifying...'; }

  try {
    const res = await api.post('/auth/verify-otp', {
      phone: `+91${phone}`,
      otp: digits
    });

    if (res.status === 'needs_registration') {
      showToast('Mobile verified! Please complete quick profile registration.', 'info');
      switchAuthTab('reg');
      const regPhone = document.getElementById('reg-phone-input');
      if (regPhone) regPhone.value = phone;
      return;
    }

    // Success login
    AppState.setUser(res.user, res.access_token);
    sessionStorage.setItem('careaura_auth_passed', 'true');
    updateUserInterface();
    closeAuthModal();
    navigateToView('patient-dashboard', false);
    showToast(`Welcome back, ${res.user.full_name}!`, 'success');
  } catch (err) {
    if (alertEl) {
      alertEl.textContent = err.message || 'OTP verification failed';
      alertEl.style.display = 'flex';
    }
    showToast('OTP verification failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = origText; }
  }
}

async function submitEmailLogin() {
  const email = document.getElementById('auth-email-input')?.value.trim();
  const password = document.getElementById('auth-password-input')?.value;
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';

  if (!email || !password) {
    showToast('Please enter both email and password.', 'error');
    return;
  }

  const btn = document.getElementById('btn-email-login');
  const origText = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Signing in...'; }

  try {
    const res = await api.post('/auth/login', { username: email, password });
    AppState.setUser(res.user, res.access_token);
    sessionStorage.setItem('careaura_auth_passed', 'true');
    updateUserInterface();
    closeAuthModal();
    navigateToView('patient-dashboard', false);
    showToast(`Signed in as ${res.user.full_name}`, 'success');
  } catch (err) {
    if (alertEl) {
      alertEl.textContent = err.message || 'Invalid email or password';
      alertEl.style.display = 'flex';
    }
    showToast('Login failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = origText; }
  }
}

async function continueWithGoogle() {
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';

  try {
    const res = await api.post('/auth/google-login', {
      google_token: 'google_sandbox_token_verified'
    });
    AppState.setUser(res.user, res.access_token);
    sessionStorage.setItem('careaura_auth_passed', 'true');
    updateUserInterface();
    closeAuthModal();
    navigateToView('patient-dashboard', false);
    showToast('Authenticated via Google OAuth sandbox session!', 'success');
  } catch (err) {
    if (alertEl) {
      alertEl.textContent = 'Google sign-in error: ' + err.message;
      alertEl.style.display = 'flex';
    }
    showToast('Google login error: ' + err.message, 'error');
  }
}

function updateRegFields() {
  const role = document.querySelector('input[name="reg-role"]:checked')?.value || 'patient';
  const docExtra = document.getElementById('reg-doctor-extra');
  if (docExtra) {
    docExtra.style.display = role === 'doctor' ? 'block' : 'none';
  }
}

function checkPasswordStrength(pw) {
  const meter = document.getElementById('reg-pw-meter');
  if (!meter) return;

  if (pw.length === 0) {
    meter.style.width = '0%';
  } else if (pw.length < 6) {
    meter.style.width = '30%';
    meter.style.backgroundColor = '#ef4444';
  } else if (pw.length < 9) {
    meter.style.width = '65%';
    meter.style.backgroundColor = '#f59e0b';
  } else {
    meter.style.width = '100%';
    meter.style.backgroundColor = '#10b981';
  }
}

async function submitRegistration() {
  const role = document.querySelector('input[name="reg-role"]:checked')?.value || 'patient';
  const name = document.getElementById('reg-name-input')?.value.trim();
  const email = document.getElementById('reg-email-input')?.value.trim();
  const phone = document.getElementById('reg-phone-input')?.value.trim();
  const city = document.getElementById('reg-city-select')?.value || 'Chennai';
  const lang = document.getElementById('reg-lang-select')?.value || 'English';
  const password = document.getElementById('reg-pw-input')?.value;
  const confirmPassword = document.getElementById('reg-confirm-pw-input')?.value;
  const alertEl = document.getElementById('auth-modal-error');
  if (alertEl) alertEl.style.display = 'none';

  if (!name || !email || !password) {
    showToast('Please fill in name, email, and password.', 'error');
    return;
  }

  if (password.length < 6) {
    showToast('Password must be at least 6 characters long.', 'error');
    return;
  }

  if (confirmPassword !== undefined && confirmPassword !== password) {
    showToast('Passwords do not match. Please verify.', 'error');
    return;
  }

  if (phone && !/^\d{10}$/.test(phone)) {
    showToast('Enter a valid 10-digit mobile number.', 'error');
    return;
  }

  const payload = {
    role,
    full_name: name,
    email,
    phone: phone ? `+91${phone}` : '+919840123456',
    city,
    preferred_language: lang,
    password
  };

  if (role === 'doctor') {
    payload.specialization = document.getElementById('reg-doc-spec')?.value.trim() || 'General Medicine';
    payload.license_number = document.getElementById('reg-doc-lic')?.value.trim() || 'NMC-TN-55201';
  }

  const btn = document.getElementById('btn-create-account');
  const origText = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Creating account...'; }

  try {
    const res = await api.post('/auth/register', payload);
    AppState.setUser(res.user, res.access_token);
    updateUserInterface();
    closeAuthModal();
    showToast(`Account created! Welcome, ${res.user.full_name}`, 'success');
  } catch (err) {
    if (alertEl) {
      alertEl.textContent = err.message || 'Registration failed';
      alertEl.style.display = 'flex';
    }
    showToast('Registration failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = origText; }
  }
}

function handleLogout() {
  api.clearToken();
  api.clearCurrentUser();
  AppState.currentUser = null;
  openAuthModal();
  showToast('You have been signed out safely.', 'info');
}

/* ================= WORKSPACE & ROLE MANAGEMENT ================= */
async function switchRole(role) {
  try {
    const res = await api.post(`/auth/quick-login/${role}`);
    AppState.setUser(res.user, res.access_token);
    updateUserInterface();
    showToast(`Switched workspace to: ${res.user.full_name} (${role.toUpperCase()})`, 'info');
  } catch (err) {
    showToast('Role switch failed: ' + err.message, 'error');
  }
}

function updateUserInterface() {
  const user = AppState.currentUser;
  if (!user) return;

  // Update topbar user details
  const nameEl = document.getElementById('topbar-user-name');
  const roleEl = document.getElementById('topbar-user-role');
  const avatarEl = document.getElementById('topbar-user-avatar');
  const avatarBadgeEl = document.getElementById('topbar-user-avatar-badge');

  if (nameEl) nameEl.textContent = user.full_name;
  if (roleEl) roleEl.textContent = `${user.role.toUpperCase()} ${user.mrn ? '• ' + user.mrn : ''}`;
  if (avatarEl) avatarEl.src = user.avatar_url || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150';
  if (avatarBadgeEl) {
    const initials = (user.full_name || 'US').split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
    avatarBadgeEl.textContent = initials;
  }

  // Update role switcher buttons
  document.querySelectorAll('.role-pill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.role === user.role);
  });

  // Toggle sidebar navigation groups based on role
  const patNav = document.getElementById('nav-group-patient');
  const docNav = document.getElementById('nav-group-doctor');
  const admNav = document.getElementById('nav-group-admin');

  if (patNav) patNav.style.display = user.role === 'patient' ? 'block' : 'none';
  if (docNav) docNav.style.display = user.role === 'doctor' ? 'block' : 'none';
  if (admNav) admNav.style.display = user.role === 'admin' ? 'block' : 'none';
}

/* ================= VIEW ROUTING & NAVIGATION ================= */
function getViewSlug(viewId) {
  const slugs = {
    'patient-dashboard': '/dashboard',
    'doctor-dashboard': '/dashboard',
    'admin-dashboard': '/dashboard',
    'patient-doctors': '/doctors',
    'patient-hospitals': '/hospitals',
    'patient-appointments': '/appointments',
    'profile': '/profile',
    'patient-waitlist': '/waitlist',
    'patient-timeline': '/timeline',
    'patient-history': '/history',
    'patient-reports': '/reports'
  };
  return slugs[viewId] || `/${viewId}`;
}

function resolveRouteFromUrl() {
  const path = window.location.pathname.replace(/^\/+|\/+$/g, '').toLowerCase();
  const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase();
  const rawKey = hash || path;
  const key = rawKey.split('/')[0];

  if (!key || key === 'dashboard' || key === 'index.html') {
    return { type: 'dashboard' };
  }
  if (key === 'login') {
    return { type: 'action', action: 'login' };
  }
  if (key === 'register' || key === 'signup') {
    return { type: 'action', action: 'register' };
  }
  if (key === 'clinical-assistant' || key === 'assistant' || key === 'chat') {
    return { type: 'action', action: 'clinical-assistant' };
  }

  const map = {
    'doctors': 'patient-doctors',
    'patient-doctors': 'patient-doctors',
    'hospitals': 'patient-hospitals',
    'patient-hospitals': 'patient-hospitals',
    'appointments': 'patient-appointments',
    'patient-appointments': 'patient-appointments',
    'profile': 'profile',
    'waitlist': 'patient-waitlist',
    'patient-waitlist': 'patient-waitlist',
    'timeline': 'patient-timeline',
    'patient-timeline': 'patient-timeline',
    'history': 'patient-history',
    'patient-history': 'patient-history',
    'reports': 'patient-reports',
    'patient-reports': 'patient-reports',
    'doctor-dashboard': 'doctor-dashboard',
    'doctor-appointments': 'doctor-appointments',
    'doctor-schedule': 'doctor-schedule',
    'doctor-calendar': 'doctor-calendar',
    'doctor-patients': 'doctor-patients',
    'doctor-patient-history': 'doctor-patient-history',
    'doctor-reports': 'doctor-reports',
    'doctor-notes': 'doctor-notes',
    'doctor-prescriptions': 'doctor-prescriptions',
    'doctor-availability': 'doctor-availability',
    'doctor-leave': 'doctor-leave',
    'doctor-queue': 'doctor-queue',
    'doctor-notifications': 'doctor-notifications',
    'doctor-workload': 'doctor-workload',
    'doctor-settings': 'doctor-settings',
    'admin-dashboard': 'admin-dashboard',
    'admin-doctors': 'admin-doctors',
    'admin-patients': 'admin-patients',
    'admin-hospitals': 'admin-hospitals',
    'admin-departments': 'admin-departments',
    'admin-ledger': 'admin-ledger',
    'admin-availability': 'admin-availability',
    'admin-scheduling': 'admin-scheduling',
    'admin-waitlist': 'admin-waitlist',
    'admin-analytics': 'admin-analytics',
    'admin-insights': 'admin-insights',
    'admin-reports': 'admin-reports',
    'admin-notifications': 'admin-notifications',
    'admin-audit': 'admin-audit',
    'admin-settings': 'admin-settings'
  };

  const viewId = map[key] || (document.getElementById(`view-${key}`) ? key : null);
  return { type: 'view', viewId };
}

function initRouting() {
  const route = resolveRouteFromUrl();
  const user = AppState.currentUser;
  const role = user ? user.role : 'patient';
  const defaultDashboard = role === 'doctor' ? 'doctor-dashboard' : (role === 'admin' ? 'admin-dashboard' : 'patient-dashboard');

  if (route.type === 'action') {
    navigateToView(defaultDashboard, false);
    if (route.action === 'login') {
      openAuthModal();
      switchAuthTab('email');
    } else if (route.action === 'register') {
      openAuthModal();
      switchAuthTab('reg');
    } else if (route.action === 'clinical-assistant') {
      setTimeout(() => {
        if (typeof ChatbotModule !== 'undefined' && ChatbotModule.open) ChatbotModule.open();
      }, 300);
    }
  } else if (route.type === 'view' && route.viewId) {
    navigateToView(route.viewId, false);
  } else {
    navigateToView(defaultDashboard, false);
  }
}

function navigateToView(viewId, pushHistory = true) {
  if (viewId === 'logout') {
    handleLogout();
    return;
  }

  AppState.currentView = viewId;

  // Update URL history if requested
  if (pushHistory && window.history && window.history.pushState) {
    const slug = getViewSlug(viewId);
    if (window.location.pathname !== slug) {
      window.history.pushState({ viewId }, '', slug);
    }
  }

  // Update navigation link active class
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.view === viewId);
  });

  // Show only active view section
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });

  const activeSec = document.getElementById(`view-${viewId}`);
  if (activeSec) {
    activeSec.classList.add('active');
  }

  // Update page title
  const titleEl = document.getElementById('topbar-page-title');
  const titles = {
    // Patient
    'patient-dashboard': 'Patient Portal Overview',
    'patient-doctors': 'Find Specialists & Consultation Slots',
    'patient-hospitals': 'Accredited Multi-Specialty Indian Hospitals',
    'patient-appointments': 'My Appointments & Consultations',
    'patient-waitlist': 'Priority Standby Waitlist Management',
    'patient-timeline': 'Unified Clinical Health Timeline',
    'patient-history': 'Electronic Health & Medical History',
    'patient-reports': 'Diagnostic Lab & Imaging Reports',
    'profile': 'Clinical User Profile & Health Identity',

    // Doctor (17 views)
    'doctor-dashboard': 'Clinical Queue & Today’s Consultations',
    'doctor-appointments': 'Consultation Ledger & Bookings',
    'doctor-schedule': 'Today’s Clinical Roster & Shift Slots',
    'doctor-calendar': 'Consultation Calendar & Availability',
    'doctor-patients': 'Registered Patients Directory',
    'doctor-patient-history': 'Electronic Medical Records & Chart Viewer',
    'doctor-reports': 'Diagnostic Lab & Imaging Reports',
    'doctor-notes': 'Clinical Consultation Notes Archive',
    'doctor-prescriptions': 'Electronic Prescriptions (Rx)',
    'doctor-availability': 'Physician Schedule & Shift Hours',
    'doctor-leave': 'Leave & Time-Off Management',
    'doctor-queue': 'Live Waiting Room Monitor',
    'doctor-notifications': 'Clinical Alerts & Hospital Updates',
    'doctor-workload': 'Workload Analytics & Performance',
    'doctor-settings': 'Clinic OPD & Consultation Settings',

    // Admin (16 views)
    'admin-dashboard': 'Hospital Operations Command Center',
    'admin-doctors': 'Doctor Roster Management',
    'admin-patients': 'Hospital Master Patient Registry',
    'admin-hospitals': 'Hospital Facilities & Metro Units',
    'admin-departments': 'Hospital Clinical Departments',
    'admin-ledger': 'Master Appointments Ledger',
    'admin-availability': 'Physician Shift Rosters & Hours',
    'admin-scheduling': 'Shift Scheduling & Capacity Optimization',
    'admin-waitlist': 'Standby Waitlist Auto-Allocation',
    'admin-analytics': 'Hospital Resource & Demand Analytics',
    'admin-insights': 'AI Operational Forecasting & Capacity Bottlenecks',
    'admin-reports': 'Clinical Governance & Audit Reports',
    'admin-notifications': 'Hospital Broadcast Announcements',
    'admin-audit': 'Audit Trail & Governance Logs',
    'admin-settings': 'CareSync Clinical OS Platform Settings'
  };

  if (titleEl) titleEl.textContent = titles[viewId] || 'CareSync Clinical OS';

  // Trigger relevant view load
  if (viewId === 'profile') loadProfileView();

  // Patient views
  if (viewId === 'patient-dashboard') PatientModule.loadDashboard();
  if (viewId === 'patient-doctors') PatientModule.loadDoctorDirectory();
  if (viewId === 'patient-hospitals') PatientModule.loadHospitals();
  if (viewId === 'patient-appointments') PatientModule.loadAppointmentsList('all');
  if (viewId === 'patient-waitlist') PatientModule.loadWaitlist();
  if (viewId === 'patient-timeline') PatientModule.loadUnifiedTimeline();
  if (viewId === 'patient-history') PatientModule.loadMedicalHistory();
  if (viewId === 'patient-reports') PatientModule.loadHealthReports();

  // Doctor views
  if (viewId === 'doctor-dashboard') DoctorModule.loadOverview();
  if (viewId === 'doctor-appointments') DoctorModule.loadAppointments();
  if (viewId === 'doctor-schedule') DoctorModule.loadSchedule();
  if (viewId === 'doctor-calendar') DoctorModule.loadCalendar();
  if (viewId === 'doctor-patients') DoctorModule.loadPatients();
  if (viewId === 'doctor-patient-history') DoctorModule.loadPatientHistory();
  if (viewId === 'doctor-reports') DoctorModule.loadReports();
  if (viewId === 'doctor-notes') DoctorModule.loadNotes();
  if (viewId === 'doctor-prescriptions') DoctorModule.loadPrescriptions();
  if (viewId === 'doctor-availability') DoctorModule.loadAvailabilitySchedule();
  if (viewId === 'doctor-leave') DoctorModule.loadLeaveManagement();
  if (viewId === 'doctor-queue') DoctorModule.loadQueue();
  if (viewId === 'doctor-notifications') DoctorModule.loadNotifications();
  if (viewId === 'doctor-workload') DoctorModule.loadWorkloadMetrics();
  if (viewId === 'doctor-settings') DoctorModule.loadSettings();

  // Admin views
  if (viewId === 'admin-dashboard') AdminModule.loadOverview();
  if (viewId === 'admin-doctors') AdminModule.loadDoctors();
  if (viewId === 'admin-patients') AdminModule.loadPatients();
  if (viewId === 'admin-hospitals') AdminModule.loadHospitals();
  if (viewId === 'admin-departments') AdminModule.loadDepartments();
  if (viewId === 'admin-ledger') AdminModule.loadAppointmentsLedger();
  if (viewId === 'admin-availability') AdminModule.loadDoctorAvailability();
  if (viewId === 'admin-scheduling') AdminModule.loadScheduling();
  if (viewId === 'admin-waitlist') AdminModule.loadWaitlist();
  if (viewId === 'admin-analytics') AdminModule.loadAnalytics();
  if (viewId === 'admin-insights') AdminModule.loadAIInsights();
  if (viewId === 'admin-reports') AdminModule.loadReports();
  if (viewId === 'admin-notifications') AdminModule.loadNotifications();
  if (viewId === 'admin-audit') AdminModule.loadAuditLogs();
  if (viewId === 'admin-settings') AdminModule.loadSettings();
}

/* ================= DYNAMIC USER PROFILE & AVATARS ================= */
function getInitialsAvatar(name, id = 0) {
  if (!name) return 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150';
  const clean = name.replace(/^Dr\.\s*/i, '').replace(/,\s*(MD|MS|MBBS|DM|MCh|DVD|DNB|DGO|DO|DPM|DVL|DCH|FACS|MDS|BPT|MPT|MEM).*$/i, '').trim();
  const parts = clean.split(/\s+/).filter(Boolean);
  let initials = 'DR';
  if (parts.length >= 2) {
    initials = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  } else if (parts.length === 1) {
    initials = parts[0].substring(0, 2).toUpperCase();
  }

  const colors = [
    '#0f766e', '#1d4ed8', '#7c3aed', '#b45309', '#047857',
    '#be185d', '#0369a1', '#4338ca', '#c2410c', '#0e7490',
    '#2563eb', '#059669', '#d97706', '#dc2626', '#4f46e5'
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const color = colors[Math.abs(hash + (id || 0)) % colors.length];

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
    <rect width="100" height="100" rx="50" fill="${color}"/>
    <text x="50" y="58" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="38" font-weight="700" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">${initials}</text>
  </svg>`;
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
}

async function loadProfileView() {
  try {
    const data = await api.get('/auth/me');
    const u = data.user || data;
    const p = data.patient || data.patient_profile;
    const d = data.doctor || data.doctor_profile;

    if (!u) {
      showToast('Please sign in to view your clinical profile.', 'info');
      return;
    }

    // Update Header
    document.getElementById('prof-full-name').textContent = u.full_name || 'Arjun Sharma';
    const avatarLetters = document.getElementById('prof-avatar-letters');
    if (avatarLetters) {
      const clean = (u.full_name || 'Arjun Sharma').replace(/^Dr\.\s*/i, '').trim();
      const parts = clean.split(/\s+/).filter(Boolean);
      let inits = 'AS';
      if (parts.length >= 2) inits = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      else if (parts.length === 1) inits = parts[0].substring(0, 2).toUpperCase();
      avatarLetters.textContent = inits;
    }
    document.getElementById('prof-role-badge').textContent = (u.role || 'patient').toUpperCase();
    document.getElementById('prof-email').textContent = u.email || 'arjun.sharma@careaura.in';
    document.getElementById('prof-city').textContent = `📍 ${u.city || 'Chennai'}, India`;
    document.getElementById('prof-language').textContent = `🗣️ ${u.preferred_language || 'English, Hindi, Tamil'}`;

    const idLabel = u.role === 'patient' 
      ? `Patient ID: ${p?.mrn || 'CA-MRN-48912'}` 
      : (u.role === 'doctor' ? `NMC License: ${d?.license_number || 'NMC-DOC-001'}` : 'System Admin ID: CA-ADM-01');
    document.getElementById('prof-identifier').textContent = idLabel;

    let ageStr = '34 Yrs';
    if (p && p.date_of_birth) {
      const birthYear = parseInt(p.date_of_birth.split('-')[0], 10);
      if (!isNaN(birthYear)) {
        ageStr = `${new Date().getFullYear() - birthYear} Yrs`;
      }
    }

    // Build Cards
    const grid = document.getElementById('prof-details-grid');
    if (!grid) return;

    let clinicalCardHtml = '';
    if (u.role === 'patient') {
      clinicalCardHtml = `
        <div class="profile-card">
          <div class="profile-card-title">🩺 Clinical Profile & Patient Vitals</div>
          <div class="profile-field-row"><span class="profile-label">Patient ID</span><span class="profile-value"><strong>${p?.mrn || 'CA-MRN-48912'}</strong></span></div>
          <div class="profile-field-row"><span class="profile-label">Date of Birth</span><span class="profile-value">${p?.date_of_birth || '1992-05-14'}</span></div>
          <div class="profile-field-row"><span class="profile-label">Age</span><span class="profile-value">${ageStr}</span></div>
          <div class="profile-field-row"><span class="profile-label">Gender</span><span class="profile-value">${p?.gender || 'Male'}</span></div>
          <div class="profile-field-row"><span class="profile-label">Blood Group</span><span class="profile-value" style="color:var(--danger); font-weight:700;">${p?.blood_group || 'O+'}</span></div>
          <div class="profile-field-row"><span class="profile-label">Residential Address</span><span class="profile-value">${escapeHtml(p?.address || 'Plot 42, 4th Cross Road, Adyar, Chennai, Tamil Nadu 600020')}</span></div>
          <div class="profile-field-row"><span class="profile-label">Emergency Contact</span><span class="profile-value">${p?.emergency_contact || 'Rajesh Sharma (Brother) - +91 98401 55210'}</span></div>
          <div class="profile-field-row"><span class="profile-label">Known Allergies</span><span class="profile-value">${escapeHtml(p?.allergies || 'Penicillin, Dust Mites')}</span></div>
          <div class="profile-field-row"><span class="profile-label">Existing Conditions</span><span class="profile-value">${escapeHtml(p?.chronic_conditions || 'Mild Seasonal Bronchitis')}</span></div>
        </div>
      `;
    } else if (u.role === 'doctor' && d) {
      clinicalCardHtml = `
        <div class="profile-card">
          <div class="profile-card-title">🩺 Physician Clinical Credentials</div>
          <div class="profile-field-row"><span class="profile-label">Department</span><span class="profile-value">${escapeHtml(d.department_name || 'Cardiology')}</span></div>
          <div class="profile-field-row"><span class="profile-label">Specialization</span><span class="profile-value">${escapeHtml(d.specialization)}</span></div>
          <div class="profile-field-row"><span class="profile-label">Hospital Center</span><span class="profile-value">${escapeHtml(d.hospital_name || 'Apollo Hospitals, Greams Road')}</span></div>
          <div class="profile-field-row"><span class="profile-label">Clinical Experience</span><span class="profile-value">${d.experience_years} Years</span></div>
          <div class="profile-field-row"><span class="profile-label">Consultation Fee</span><span class="profile-value" style="color:var(--success); font-weight:700;">₹${d.consultation_fee}</span></div>
          <div class="profile-field-row"><span class="profile-label">Languages</span><span class="profile-value">${escapeHtml(d.languages || 'English, Hindi')}</span></div>
          <div class="profile-field-row"><span class="profile-label">OPD Suite</span><span class="profile-value">${escapeHtml(d.room_number || 'Suite 301')}</span></div>
        </div>
      `;
    }

    grid.innerHTML = `
      <div class="profile-card">
        <div class="profile-card-title">👤 Contact & Regional Demographics</div>
        <div class="profile-field-row"><span class="profile-label">Full Name</span><span class="profile-value"><strong>${escapeHtml(u.full_name || 'User')}</strong></span></div>
        <div class="profile-field-row"><span class="profile-label">Mobile Number</span><span class="profile-value">${u.phone || '+91 98401 23456'}</span></div>
        <div class="profile-field-row"><span class="profile-label">Email ID</span><span class="profile-value">${u.email}</span></div>
        <div class="profile-field-row"><span class="profile-label">Metro City</span><span class="profile-value">${u.city || 'Chennai'}</span></div>
        <div class="profile-field-row"><span class="profile-label">Preferred Language</span><span class="profile-value">${u.preferred_language || 'English'}</span></div>
        <div class="profile-field-row"><span class="profile-label">Account Created</span><span class="profile-value">${u.created_at ? u.created_at.split('T')[0] : '2026-01-10'}</span></div>
      </div>
      ${clinicalCardHtml}
      <div class="profile-card">
        <div class="profile-card-title">🔒 Platform Access & Security</div>
        <div class="profile-field-row"><span class="profile-label">Role Access</span><span class="profile-value" style="text-transform:uppercase; font-weight:700;">${u.role}</span></div>
        <div class="profile-field-row"><span class="profile-label">Identity Status</span><span class="profile-value" style="color:var(--success); font-weight:600;">✓ Verified Clinical ID</span></div>
        <div class="profile-field-row"><span class="profile-label">Mobile OTP Verification</span><span class="profile-value" style="color:var(--success); font-weight:600;">✓ Active (+91)</span></div>
        <div class="profile-field-row"><span class="profile-label">Session Encryption</span><span class="profile-value">TLS 1.3 / AES-256</span></div>
      </div>
    `;
  } catch (err) {
    showToast('Failed to load profile details: ' + err.message, 'error');
  }
}

async function openEditProfileModal() {
  try {
    const data = await api.get('/auth/me');
    const u = data.user || data;
    const p = data.patient || data.patient_profile;

    document.getElementById('edit-prof-name').value = u.full_name || '';
    document.getElementById('edit-prof-phone').value = (u.phone || '').replace('+91', '').trim();
    document.getElementById('edit-prof-city').value = u.city || 'Chennai';
    document.getElementById('edit-prof-lang').value = u.preferred_language || 'English';
    document.getElementById('edit-prof-avatar').value = u.avatar_url || '';

    const patFields = document.getElementById('edit-prof-pat-fields');
    if (u.role === 'patient') {
      patFields.style.display = 'block';
      if (document.getElementById('edit-prof-dob')) document.getElementById('edit-prof-dob').value = p?.date_of_birth || '1992-05-14';
      if (document.getElementById('edit-prof-gender')) document.getElementById('edit-prof-gender').value = p?.gender || 'Male';
      if (document.getElementById('edit-prof-blood')) document.getElementById('edit-prof-blood').value = p?.blood_group || 'O+';
      if (document.getElementById('edit-prof-address')) document.getElementById('edit-prof-address').value = p?.address || 'Plot 42, 4th Cross Road, Adyar, Chennai, Tamil Nadu 600020';
      if (document.getElementById('edit-prof-emergency')) document.getElementById('edit-prof-emergency').value = p?.emergency_contact || 'Rajesh Sharma (Brother) - +91 98401 55210';
      if (document.getElementById('edit-prof-allergies')) document.getElementById('edit-prof-allergies').value = p?.allergies || 'Penicillin, Dust Mites';
      if (document.getElementById('edit-prof-chronic')) document.getElementById('edit-prof-chronic').value = p?.chronic_conditions || 'Mild Seasonal Bronchitis';
    } else {
      patFields.style.display = 'none';
    }

    document.getElementById('edit-profile-modal').classList.add('active');
  } catch (err) {
    showToast('Error opening edit profile: ' + err.message, 'error');
  }
}

async function saveUserProfile() {
  const name = document.getElementById('edit-prof-name').value.trim();
  const phone = document.getElementById('edit-prof-phone').value.trim();
  const city = document.getElementById('edit-prof-city').value;
  const lang = document.getElementById('edit-prof-lang').value;
  const avatar = document.getElementById('edit-prof-avatar').value.trim();
  
  const dob = document.getElementById('edit-prof-dob')?.value;
  const gender = document.getElementById('edit-prof-gender')?.value;
  const blood = document.getElementById('edit-prof-blood')?.value;
  const address = document.getElementById('edit-prof-address')?.value.trim();
  const emergency = document.getElementById('edit-prof-emergency')?.value.trim();
  const allergies = document.getElementById('edit-prof-allergies')?.value.trim();
  const chronic = document.getElementById('edit-prof-chronic')?.value.trim();

  const body = {
    full_name: name,
    phone: phone ? (phone.startsWith('+91') ? phone : `+91 ${phone}`) : undefined,
    city,
    preferred_language: lang,
    avatar_url: avatar || undefined,
    date_of_birth: dob,
    gender,
    blood_group: blood,
    address,
    emergency_contact: emergency,
    allergies,
    chronic_conditions: chronic
  };

  try {
    const res = await api.put('/auth/profile', body);
    const updatedUser = res.user || res;
    AppState.currentUser = updatedUser;
    api.setCurrentUser(updatedUser);
    updateUserInterface();
    document.getElementById('edit-profile-modal').classList.remove('active');
    showToast('Clinical profile successfully updated!', 'success');
    loadProfileView();
  } catch (err) {
    showToast('Failed to save profile: ' + err.message, 'error');
  }
}


/* ================= EVENT LISTENERS ================= */
function setupEventListeners() {
  // Navigation links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const viewId = link.dataset.view;
      if (viewId) navigateToView(viewId);
    });
  });

  // Role switcher pills
  document.querySelectorAll('.role-pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchRole(btn.dataset.role);
    });
  });

  // Modal close handlers
  document.querySelectorAll('.modal-close-btn, .modal-cancel-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    });
  });

  // Close modals when clicking backdrop
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // Doctor select change in booking modal
  const bookDocSelect = document.getElementById('book-doctor-select');
  if (bookDocSelect) {
    bookDocSelect.addEventListener('change', () => {
      PatientModule.fetchAvailableSlots();
    });
  }

  // Date input change in booking modal
  const bookDateInput = document.getElementById('book-date-input');
  if (bookDateInput) {
    bookDateInput.addEventListener('change', () => {
      PatientModule.fetchAvailableSlots();
    });
  }

  // Department filter in booking modal
  const bookDeptSelect = document.getElementById('book-dept-select');
  if (bookDeptSelect) {
    bookDeptSelect.addEventListener('change', () => {
      PatientModule.updateBookingDoctorSelect();
    });
  }

  // Notification button toggle
  const notifBtn = document.getElementById('topbar-notif-btn');
  const notifDropdown = document.getElementById('notification-dropdown');
  if (notifBtn && notifDropdown) {
    notifBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      notifDropdown.style.display = notifDropdown.style.display === 'none' ? 'block' : 'none';
      if (notifDropdown.style.display === 'block') {
        await loadNotificationDropdown();
      }
    });

    document.addEventListener('click', (e) => {
      if (notifDropdown && !notifDropdown.contains(e.target) && e.target !== notifBtn) {
        notifDropdown.style.display = 'none';
      }
    });
  }
}

async function loadNotificationDropdown() {
  const container = document.getElementById('notification-dropdown-list');
  if (!container) return;

  try {
    const notes = await api.get('/patient/notifications');
    if (!notes || notes.length === 0) {
      container.innerHTML = `<div style="padding:14px; text-align:center; color:var(--text-muted); font-size:0.8rem;">No active notifications.</div>`;
      return;
    }

    container.innerHTML = notes.map(n => `
      <div style="padding:10px 14px; border-bottom:1px solid var(--border-subtle); background:${n.is_read ? 'transparent' : 'var(--bg-surface-alt)'};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong style="font-size:0.82rem;">${escapeHtml(n.title)}</strong>
          <span style="font-size:0.68rem; color:var(--text-muted);">${n.created_at ? n.created_at.split('T')[0] : ''}</span>
        </div>
        <p style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">${escapeHtml(n.message)}</p>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div style="padding:10px; color:var(--danger); font-size:0.75rem;">Error loading notifications.</div>`;
  }
}


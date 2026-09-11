// Global State and UI Notification Helpers
const AppState = {
  currentUser: null,
  activeRole: 'patient', // 'patient', 'doctor', 'admin'
  currentView: 'patient-dashboard',
  selectedDoctorForBooking: null,
  allDoctors: [],
  allDepartments: [],
  notifications: [],

  init() {
    this.currentUser = api.getCurrentUser();
    if (this.currentUser) {
      this.activeRole = this.currentUser.role;
    }
  },

  setUser(user, token) {
    this.currentUser = user;
    this.activeRole = user.role;
    api.setCurrentUser(user);
    if (token) {
      api.setToken(token);
    }
  },

  logout() {
    this.currentUser = null;
    api.clearToken();
    api.clearCurrentUser();
    window.location.reload();
  }
};

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

// CareSync Clinical OS Centralized API Client
const API_BASE = (() => {
  if (typeof window !== 'undefined' && (window.API_BASE_URL || window.AEGIS_API_URL || window.VITE_API_URL)) {
    return (window.API_BASE_URL || window.AEGIS_API_URL || window.VITE_API_URL).replace(/\/+$/, '');
  }
  // If running on a standalone dev port like 3000/5173, point to backend on 8000
  if (typeof window !== 'undefined' && window.location && window.location.port && !['8000', '', '80', '443'].includes(window.location.port)) {
    return `${window.location.protocol}//${window.location.hostname}:8000/api`;
  }
  return '/api';
})();

const api = {
  _abortControllers: new Map(),

  getBaseUrl() {
    return API_BASE;
  },

  getToken() {
    return localStorage.getItem('careaura_token') || localStorage.getItem('aegiscare_token');
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

  // Cancel prior request for a given key (e.g. 'doctor-search')
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
      
      // Safe parsing
      let data = {};
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        data = await res.json();
      } else {
        const text = await res.text();
        data = { message: text };
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
        // Silently return aborted flag so caller knows not to show error
        return { __aborted: true };
      }
      // Retry once on idempotent GET if network glitch
      if (retries > 0 && (!options.method || options.method === 'GET')) {
        await new Promise(r => setTimeout(r, 250));
        return this.request(endpoint, options, retries - 1);
      }
      const isNetworkErr = !err.status && (err.name === 'TypeError' || (err.message && err.message.toLowerCase().includes('failed to fetch')));
      if (isNetworkErr) {
        err.message = 'Unable to connect to hospital server. Please check connection and click Retry.';
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


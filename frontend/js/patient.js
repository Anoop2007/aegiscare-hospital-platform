// Patient Portal Module
const PatientModule = {
  currentFilter: 'all',
  selectedSlotTime: null,
  activeBookingDoctor: null,
  activeTelehealthInterval: null,
  userLocation: null,

  calculateDistanceKm(lat1, lon1, lat2, lon2) {
    if (!lat1 || !lon1 || !lat2 || !lon2) return null;
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 10) / 10;
  },

  getUserLocationContext() {
    // Chennai Metro Reference Point: 13.0827°N, 80.2707°E (Chennai Central)
    const chennaiBase = { lat: 13.0827, lon: 80.2707 };
    if (!this.userLocation) return chennaiBase;
    const distFromChennai = this.calculateDistanceKm(this.userLocation.lat, this.userLocation.lon, chennaiBase.lat, chennaiBase.lon);
    if (distFromChennai !== null && distFromChennai <= 60) {
      return this.userLocation;
    }
    return chennaiBase;
  },

  getHospitalCoordinates(h) {
    const hid = h.id || 1;
    const city = (h.city || '').toLowerCase().trim();

    // Chennai: distinct stable coordinates categorized in 10-20km, 20-30km, 30-40km bands
    if (city === 'chennai' || !city) {
      const chennaiBands = [
        // 10-20 km
        { lat: 12.9800, lon: 80.2200 }, // ~12.7 km (Adyar / T Nagar)
        { lat: 12.9600, lon: 80.2100 }, // ~15.1 km (Guindy / Velachery)
        { lat: 12.9400, lon: 80.1900 }, // ~18.1 km (Anna Nagar West / Porur)
        // 20-30 km
        { lat: 12.9000, lon: 80.1700 }, // ~23.1 km (Tambaram / Pallavaram)
        { lat: 12.8700, lon: 80.1600 }, // ~26.5 km (Chromepet / Medavakkam)
        { lat: 12.8400, lon: 80.1500 }, // ~30.0 km (Sholinganallur / OMR IT)
        // 30-40 km
        { lat: 12.8100, lon: 80.1400 }, // ~33.5 km (Kelambakkam / Siruseri)
        { lat: 12.7800, lon: 80.1200 }, // ~37.4 km (Vandalur Campus)
        { lat: 12.7600, lon: 80.1100 }  // ~39.8 km (Mahabalipuram Link)
      ];
      return chennaiBands[(hid - 1) % chennaiBands.length];
    }

    // Bengaluru: approximately 354 km from Chennai
    if (city.includes('bengaluru') || city.includes('bangalore')) {
      const blrList = [
        { lat: 12.9716, lon: 77.0100 }, // ~353.5 km
        { lat: 12.9863, lon: 77.0000 }, // ~354.5 km
        { lat: 12.8943, lon: 77.0200 }, // ~352.8 km
        { lat: 12.9352, lon: 76.9950 }  // ~355.2 km
      ];
      return blrList[(hid - 1) % blrList.length];
    }

    // Vijayawada: approximately 410 km from Chennai
    if (city.includes('vijayawada')) {
      const vjaList = [
        { lat: 16.7600, lon: 80.6000 }, // ~410.4 km
        { lat: 16.7700, lon: 80.6200 }, // ~411.7 km
        { lat: 16.7500, lon: 80.5900 }  // ~409.2 km
      ];
      return vjaList[(hid - 1) % vjaList.length];
    }

    // Hyderabad: approximately 415 km from Chennai
    if (city.includes('hyderabad')) {
      const hydList = [
        { lat: 16.6400, lon: 79.1500 }, // ~414.1 km
        { lat: 16.6500, lon: 79.1400 }, // ~415.2 km
        { lat: 16.6600, lon: 79.1600 }  // ~416.5 km
      ];
      return hydList[(hid - 1) % hydList.length];
    }

    // Pune: approximately 910 km
    if (city.includes('pune')) {
      const puneList = [
        { lat: 18.5204, lon: 73.8567 }, // ~914.4 km
        { lat: 18.5074, lon: 73.8077 }  // ~918.2 km
      ];
      return puneList[(hid - 1) % puneList.length];
    }

    // Mumbai: approximately 1030 km
    if (city.includes('mumbai')) {
      const bomList = [
        { lat: 19.0760, lon: 72.8777 }, // ~1033.1 km
        { lat: 19.1311, lon: 72.8252 }, // ~1037.4 km
        { lat: 19.0048, lon: 72.8431 }  // ~1028.9 km
      ];
      return bomList[(hid - 1) % bomList.length];
    }

    // Kolkata: approximately 1360 km
    if (city.includes('kolkata')) {
      return { lat: 22.5726, lon: 88.3639 }; // ~1358.4 km
    }

    // Delhi: approximately 1750 km
    if (city.includes('delhi')) {
      const delList = [
        { lat: 28.6139, lon: 77.2090 }, // ~1755.8 km
        { lat: 28.5284, lon: 77.2132 }  // ~1746.5 km
      ];
      return delList[(hid - 1) % delList.length];
    }

    // Kochi
    if (city.includes('kochi')) {
      return { lat: 9.9312, lon: 76.2673 }; // ~565 km
    }

    // Default fallback anchor in Chennai
    return { lat: 12.9800, lon: 80.2200 };
  },

  getHospitalImage(h) {
    if (h.image_url && h.image_url.startsWith('/assets/hospitals/')) {
      return h.image_url;
    }
    const hid = h.id || 1;
    const city = (h.city || '').toLowerCase().trim();
    if (city.includes('chennai')) {
      const imgs = ['/assets/hospitals/hosp_chennai_1.jpg', '/assets/hospitals/hosp_chennai_2.jpg', '/assets/hospitals/hosp_chennai_3.jpg'];
      return imgs[(hid - 1) % imgs.length];
    }
    if (city.includes('bengaluru') || city.includes('bangalore')) {
      const imgs = ['/assets/hospitals/hosp_bangalore_1.jpg', '/assets/hospitals/hosp_bangalore_2.jpg'];
      return imgs[(hid - 1) % imgs.length];
    }
    if (city.includes('hyderabad')) {
      const imgs = ['/assets/hospitals/hosp_hyderabad_1.jpg', '/assets/hospitals/hosp_hyderabad_2.jpg'];
      return imgs[(hid - 1) % imgs.length];
    }
    if (city.includes('vijayawada')) {
      return '/assets/hospitals/hosp_vijayawada_1.jpg';
    }
    if (city.includes('pune')) {
      return '/assets/hospitals/hosp_pune_1.jpg';
    }
    if (city.includes('delhi')) {
      const imgs = ['/assets/hospitals/hosp_delhi_1.jpg', '/assets/hospitals/hosp_delhi_2.jpg', '/assets/hospitals/hosp_delhi_3.jpg'];
      return imgs[(hid - 1) % imgs.length];
    }
    if (city.includes('kochi')) {
      return '/assets/hospitals/hosp_kochi_1.jpg';
    }
    return '/assets/hospitals/hosp_chennai_1.jpg';
  },

  getDoctorCoordinates(doc) {
    const docId = doc.id || 1;
    const cityStr = (doc.city || (doc.hospital_name ? doc.hospital_name.split(',').pop() : '')).toLowerCase().trim();
    const campus = this.getHospitalCoordinates({ id: doc.hospital_id || docId, city: cityStr || 'chennai' });
    const microLat = (((docId * 7 + 3) % 11) - 5) * 0.0006;
    const microLon = (((docId * 11 + 5) % 11) - 5) * 0.0006;
    return {
      lat: campus.lat + microLat,
      lon: campus.lon + microLon
    };
  },

  getDoctorDistanceKm(doc) {
    if (doc._distanceKm !== undefined && doc._distanceKm !== null && doc._distanceKm > 0) {
      return doc._distanceKm;
    }
    const userLoc = this.getUserLocationContext();
    const coords = this.getDoctorCoordinates(doc);
    const d = this.calculateDistanceKm(userLoc.lat, userLoc.lon, coords.lat, coords.lon);
    return (d !== null && d > 0) ? d : 12.5;
  },

  getDoctorLiveTiming(doc) {
    const now = new Date();
    const currentH = now.getHours();
    const currentM = now.getMinutes();
    const currentVal = currentH + currentM / 60.0;

    const spec = (doc.specialization || '').toLowerCase();
    const dept = (doc.department_name || '').toLowerCase();
    if (spec.includes('emergency') || spec.includes('trauma') || dept.includes('emergency') || (doc.shift_timing && doc.shift_timing.includes('24x7'))) {
      return {
        isAvailableNow: true,
        badgeText: 'Available 24x7 (Emergency On-Duty)',
        shiftText: '24x7 Level-1 Emergency & Trauma Unit',
        badgeClass: 'badge-live-available'
      };
    }

    const docId = doc.id || 1;
    // 6 distinct realistic clinical shift variations across doctors
    const scheduleVariations = [
      [
        { start: 8.5, end: 13.0, label: '08:30 AM – 01:00 PM' },
        { start: 14.0, end: 17.5, label: '02:00 PM – 05:30 PM' }
      ],
      [
        { start: 10.0, end: 14.0, label: '10:00 AM – 02:00 PM' },
        { start: 17.5, end: 21.5, label: '05:30 PM – 09:30 PM' }
      ],
      [
        { start: 12.0, end: 16.0, label: '12:00 PM – 04:00 PM' },
        { start: 18.0, end: 22.0, label: '06:00 PM – 10:00 PM' }
      ],
      [
        { start: 7.5, end: 12.0, label: '07:30 AM – 12:00 PM' },
        { start: 16.5, end: 20.5, label: '04:30 PM – 08:30 PM' }
      ],
      [
        { start: 9.0, end: 14.5, label: '09:00 AM – 02:30 PM' },
        { start: 15.5, end: 19.5, label: '03:30 PM – 07:30 PM' }
      ],
      [
        { start: 11.0, end: 15.0, label: '11:00 AM – 03:00 PM' },
        { start: 17.0, end: 21.0, label: '05:00 PM – 09:00 PM' }
      ]
    ];

    const shifts = scheduleVariations[docId % scheduleVariations.length];

    for (const s of shifts) {
      if (currentVal >= s.start && currentVal < s.end) {
        return {
          isAvailableNow: true,
          badgeText: `Available Now (${s.label})`,
          shiftText: s.label,
          badgeClass: 'badge-live-available'
        };
      }
    }

    for (const s of shifts) {
      if (currentVal < s.start) {
        const startH = Math.floor(s.start);
        const startM = Math.round((s.start - startH) * 60);
        const timeStr = `${startH > 12 ? startH - 12 : startH}:${startM === 0 ? '00' : (startM < 10 ? '0' + startM : startM)} ${startH >= 12 ? 'PM' : 'AM'}`;
        return {
          isAvailableNow: false,
          badgeText: `Next Slot: ${timeStr} (${s.label})`,
          shiftText: s.label,
          badgeClass: 'badge-live-upcoming'
        };
      }
    }

    const tomorrowSlot = shifts[0].label.split('–')[0].trim();
    return {
      isAvailableNow: false,
      badgeText: `Resumes ${tomorrowSlot} Tomorrow (${shifts[0].label})`,
      shiftText: shifts[0].label,
      badgeClass: 'badge-live-ended'
    };
  },

  async sortByNearest(type = 'doctors') {
    const btnId = type === 'doctors' ? 'btn-doc-location-detect' : 'btn-hosp-location-detect';
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '📍 Acquiring Location...';
    }

    const processLocation = (coords) => {
      this.userLocation = coords;
      showToast(`GPS Location active: ${coords.lat.toFixed(3)}°N, ${coords.lon.toFixed(3)}°E (Nearest first)`, 'success');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '📍 Nearest to Me ✓';
        btn.classList.add('btn-active');
      }
      if (type === 'doctors') {
        this.loadDoctorDirectory(true);
      } else {
        this.filterHospitals(true);
      }
    };

    if (this.userLocation) {
      processLocation(this.userLocation);
      return;
    }

    if (!navigator.geolocation) {
      showToast('Geolocation not supported by browser. Using Regional Center coordinates.', 'warning');
      processLocation({ lat: 13.0067, lon: 80.2573 });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        processLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude });
      },
      (err) => {
        console.warn('Geolocation permission not granted:', err.message);
        showToast('Using regional clinic location (Chennai Metro).', 'info');
        processLocation({ lat: 13.0067, lon: 80.2573 });
      },
      { enableHighAccuracy: true, timeout: 6000, maximumAge: 60000 }
    );
  },

  async loadDashboard() {
    try {
      const data = await api.get('/patient/dashboard');
      this.renderOverview(data);
    } catch (err) {
      showToast('Failed to load patient dashboard: ' + err.message, 'error');
    }
  },

  renderOverview(data) {
    // Metrics
    document.getElementById('pat-total-appts').textContent = data.metrics.total_appointments;
    document.getElementById('pat-completed-appts').textContent = data.metrics.completed_consultations;
    document.getElementById('pat-total-reports').textContent = data.metrics.uploaded_reports;
    document.getElementById('pat-unread-notes').textContent = data.metrics.unread_notifications;

    // Patient info banner
    if (data.patient) {
      const mrnEl = document.getElementById('pat-banner-mrn');
      if (mrnEl) mrnEl.textContent = `MRN: ${data.patient.mrn} | Blood Group: ${data.patient.blood_group || 'N/A'}`;
    }

    // Standby Offer Alert Banner
    const offerContainer = document.getElementById('pat-standby-offer-container');
    if (offerContainer) {
      if (data.offered_waitlist_slot) {
        const o = data.offered_waitlist_slot;
        offerContainer.innerHTML = `
          <div class="offered-slot-alert">
            <div style="display:flex; align-items:center; gap:14px;">
              <span style="font-size:1.6rem;">⚡</span>
              <div>
                <div style="font-weight:700; color:#065f46; font-size:0.92rem;">Priority Standby Slot Available!</div>
                <div style="font-size:0.8rem; color:#047857;">
                  A slot opened up with <strong>${escapeHtml(o.doctor_name)}</strong> on <strong>${o.scheduled_date} at ${o.scheduled_time}</strong> (${escapeHtml(o.department_name)}).
                </div>
              </div>
            </div>
            <div style="display:flex; gap:8px;">
              <button class="btn btn-teal btn-sm" onclick="PatientModule.claimWaitlistSlot(${o.waitlist_id}, ${o.appointment_id})">Claim This Slot</button>
              <button class="btn btn-secondary btn-sm" onclick="PatientModule.declineWaitlistSlot(${o.waitlist_id})">Decline</button>
            </div>
          </div>
        `;
      } else {
        offerContainer.innerHTML = '';
      }
    }

    // Live Queue Tracker Widget
    const queueContainer = document.getElementById('pat-live-queue-container');
    if (queueContainer) {
      if (data.upcoming_appointment && data.upcoming_appointment.live_queue) {
        const q = data.upcoming_appointment.live_queue;
        const a = data.upcoming_appointment;
        queueContainer.innerHTML = `
          <div class="live-queue-card">
            <div style="display:flex; align-items:center; gap:16px;">
              <div class="queue-badge-circle">
                <span class="q-num">#${q.queue_position}</span>
                <span class="q-label">Position</span>
              </div>
              <div>
                <div style="font-size:0.75rem; color:#38bdf8; text-transform:uppercase; letter-spacing:0.05em; font-weight:700;">
                  Live Consultation Queue Tracker
                </div>
                <h3 style="font-size:1.15rem; color:#fff; margin:2px 0;">${escapeHtml(a.doctor_name)}</h3>
                <div style="font-size:0.82rem; color:#94a3b8;">
                  📍 ${escapeHtml(a.room_number || 'Consultation Suite')} • ${escapeHtml(a.department_name)}
                </div>
              </div>
            </div>
            <div style="display:flex; gap:20px;">
              <div class="queue-stat-metric">
                <span class="m-value">${q.patients_ahead}</span>
                <span class="m-label">Patients Ahead</span>
              </div>
              <div class="queue-stat-metric">
                <span class="m-value">~${q.estimated_wait_minutes}m</span>
                <span class="m-label">Est. Wait Time</span>
              </div>
              <div class="queue-stat-metric">
                <span class="m-value" style="font-size:0.95rem; color:${q.delay_minutes > 0 ? '#f59e0b' : '#34d399'};">
                  ${q.delay_minutes > 0 ? '+' + q.delay_minutes + 'm Delay' : 'On Schedule'}
                </span>
                <span class="m-label">Clinic Flow</span>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <span class="status-badge badge-${(q.patient_status || 'confirmed').toLowerCase()}" style="text-align:center;">
                ${q.status_message}
              </span>
              <button class="btn btn-secondary btn-sm" style="font-size:0.72rem; padding:4px 8px; color:#fff; background:rgba(255,255,255,0.1); border-color:rgba(255,255,255,0.2);" onclick="PatientModule.checkInPatient(${a.id})">
                ${a.check_in_time ? 'Checked In (' + a.check_in_time + ')' : '📍 Check In at Clinic'}
              </button>
            </div>
          </div>
        `;
      } else {
        queueContainer.innerHTML = '';
      }
    }

    // Hero upcoming appointment card
    const heroContainer = document.getElementById('pat-hero-appointment-container');
    if (data.upcoming_appointment) {
      const appt = data.upcoming_appointment;
      const isVideo = appt.consultation_type === 'Video';
      heroContainer.innerHTML = `
        <div class="hero-appointment-card">
          <div class="hero-info-left">
            <div class="hero-badge-row">
              <span class="hero-date-badge">${appt.scheduled_date} at ${appt.scheduled_time}</span>
              <span class="status-badge badge-${appt.status}">${appt.status}</span>
              <span class="status-badge ${isVideo ? 'badge-in-progress' : 'badge-scheduled'}">${appt.consultation_type}</span>
            </div>
            <div class="hero-doctor-name">${escapeHtml(appt.doctor_name)}</div>
            <div class="hero-doctor-spec">${escapeHtml(appt.department_name)} • ${escapeHtml(appt.specialization)}</div>
            <div class="hero-details-row">
              <span>📍 ${escapeHtml(appt.room_number || 'Main Wing')}</span>
              <span>⏱️ Est. Queue Wait: ~${appt.estimated_wait_time || 10} mins</span>
              <span>🆔 Ref: ${appt.appointment_number}</span>
            </div>
          </div>
          <div class="hero-action-right">
            ${isVideo ? `
              <button class="btn btn-teal" onclick="PatientModule.openTelehealthRoom(${appt.id})">
                📹 Join Telehealth Consultation
              </button>
            ` : `
              <button class="btn btn-primary" onclick="PatientModule.viewAppointmentDetails(${appt.id})">
                📋 View Clinical Details
              </button>
            `}
            <div style="display:flex; gap:8px;">
              <button class="btn btn-secondary btn-sm" onclick="PatientModule.openRescheduleModal(${appt.id}, '${appt.scheduled_date}', '${appt.scheduled_time}')">Reschedule</button>
              <button class="btn btn-outline-danger btn-sm" onclick="PatientModule.openCancelModal(${appt.id})">Cancel</button>
            </div>
          </div>
        </div>
      `;
    } else {
      heroContainer.innerHTML = `
        <div class="clinical-card" style="text-align: center; padding: 36px 20px; margin-bottom: 24px; border: 1px dashed var(--border-medium);">
          <div style="font-size: 2rem; margin-bottom: 8px;">🗓️</div>
          <h3 style="font-size: 1.15rem; margin-bottom: 6px;">No Upcoming Consultations Scheduled</h3>
          <p style="color: var(--text-muted); font-size: 0.88rem; max-width: 480px; margin: 0 auto 16px;">
            You currently have no active doctor appointments. Use our Smart Booking system or find an available specialist.
          </p>
          <button class="btn btn-primary" onclick="PatientModule.openBookingModal()">
            ⚡ Book New Consultation
          </button>
        </div>
      `;
    }

    // Recent activity list
    const activityList = document.getElementById('pat-recent-activity-list');
    if (activityList) {
      if (data.recent_activity && data.recent_activity.length > 0) {
        activityList.innerHTML = data.recent_activity.map(act => `
          <div style="display:flex; align-items:center; justify-content:space-between; padding: 12px 0; border-bottom: 1px solid var(--border-subtle);">
            <div>
              <div style="font-weight:600; font-size:0.88rem;">${escapeHtml(act.title)}</div>
              <div style="font-size:0.75rem; color:var(--text-muted);">${act.date} • Ref: ${escapeHtml(act.reference)}</div>
            </div>
            <span class="status-badge badge-${(act.status || 'scheduled').toLowerCase()}">${act.status}</span>
          </div>
        `).join('');
      } else {
        activityList.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem; padding: 12px 0;">No recent activity logged.</p>`;
      }
    }
  },

  async loadDoctorDirectory(sortByDist = false) {
    const deptId = document.getElementById('pat-filter-dept')?.value || '';
    const mode = document.getElementById('pat-filter-mode')?.value || '';
    const avail = document.getElementById('pat-filter-avail')?.value || '';
    const search = document.getElementById('pat-search-doctor')?.value || '';

    const grid = document.getElementById('pat-doctor-grid');
    if (grid) {
      grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:30px; color:var(--text-muted);"><p>Loading physicians...</p></div>';
    }

    try {
      const signal = api.abortPrior('patient-doctors');
      let doctors = await api.get('/patient/doctors', {
        department_id: deptId,
        consultation_type: mode,
        availability_status: avail,
        doctor_name: search
      }, { signal });

      if (doctors && doctors.__aborted) return;

      if (doctors && doctors.length > 0) {
        const userLoc = this.getUserLocationContext();
        doctors.forEach(doc => {
          const coords = this.getDoctorCoordinates(doc);
          const dist = this.calculateDistanceKm(
            userLoc.lat,
            userLoc.lon,
            coords.lat,
            coords.lon
          );
          doc._distanceKm = (dist !== null && dist > 0) ? dist : 12.5;
        });

        // Ensure distinct stable distance values across doctors
        const seenDistances = new Set();
        doctors.forEach(doc => {
          let dist = doc._distanceKm;
          while (seenDistances.has(dist)) {
            dist = parseFloat((dist + 0.3).toFixed(1));
          }
          seenDistances.add(dist);
          doc._distanceKm = dist;
        });

        if (sortByDist || this.userLocation) {
          doctors.sort((a, b) => (a._distanceKm || 9999) - (b._distanceKm || 9999));
        }
      }

      this.renderDoctorCards(doctors);
    } catch (err) {
      if (grid) {
        grid.innerHTML = `
          <div style="grid-column:1/-1; text-align:center; padding:36px 20px;">
            <p style="color:var(--danger); font-size:0.9rem; font-weight:500; margin-bottom:12px;">Failed to load physicians: ${escapeHtml(err.message)}</p>
            <button class="btn btn-secondary btn-sm" onclick="PatientModule.loadDoctorDirectory()">↻ Retry Physician Search</button>
          </div>
        `;
      }
    }
  },

  renderDoctorCards(doctors) {
    const grid = document.getElementById('pat-doctor-grid');
    if (!grid) return;

    if (!doctors || doctors.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color: var(--text-muted);">
          <p>No physicians match the current search filters. Please adjust your criteria.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = doctors.map(doc => {
      const timing = this.getDoctorLiveTiming(doc);
      const dist = this.getDoctorDistanceKm(doc);
      const docAvatar = `/assets/doctors/doc_${((doc.id || 1) - 1) % 6 + 1}.jpg`;

      return `
      <div class="doctor-card">
        <div>
          <div class="doc-header">
            <img src="${docAvatar}" onerror="this.onerror=null; this.src=getInitialsAvatar('${escapeHtml(doc.full_name)}', ${doc.id});" class="doc-avatar" alt="${escapeHtml(doc.full_name)}"/>
            <div class="doc-info">
              <h3>${escapeHtml(doc.full_name)}</h3>
              <div class="doc-dept">${escapeHtml(doc.department_name)}</div>
              <div class="doc-spec">${escapeHtml(doc.specialization)}</div>
            </div>
          </div>
          <div class="doc-chips">
            ${doc.hospital_name ? `<span class="doc-chip" style="background:#eff6ff; color:#1d4ed8;">🏥 ${escapeHtml(doc.hospital_name)}</span>` : ''}
            ${doc.city ? `<span class="doc-chip" style="background:#f0fdf4; color:#15803d;">🏙️ ${escapeHtml(doc.city)}</span>` : ''}
            <span class="doc-chip">⏱️ ${doc.experience_years} yrs exp</span>
            <span class="doc-chip">🗣️ ${escapeHtml(doc.languages || 'English, Hindi')}</span>
            <span class="doc-chip">📍 ${escapeHtml(doc.room_number || 'Suite 101')}</span>
            <span class="doc-chip live-timing-badge ${timing.badgeClass}">
              🕒 ${timing.badgeText}
            </span>
            <span class="doc-chip distance-badge" style="background:#fef3c7; color:#92400e; font-weight:600;">📍 ${dist} km away</span>
          </div>
          <div style="font-size:0.78rem; color:var(--text-secondary); margin-bottom: 12px; line-height: 1.4;">
            ${escapeHtml(doc.bio || 'Specialized clinical practitioner offering evidence-based medical consultations.')}
          </div>
        </div>
        <div class="doc-footer">
          <div class="doc-fee">
            ₹${doc.consultation_fee} <span>/ consult</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="PatientModule.selectDoctorForBooking(${doc.id}, '${escapeHtml(doc.full_name)}', '${escapeHtml(doc.department_name)}')">
            Book Slot
          </button>
        </div>
      </div>
    `;
    }).join('');
  },

  /* ================= HOSPITALS DIRECTORY ================= */
  async loadHospitals() {
    this.filterHospitals();
  },

  async filterHospitals(sortByDist = false) {
    if (sortByDist) {
      this.isNearMeHospitalsActive = true;
    }
    const city = document.getElementById('hosp-city-filter')?.value || 'all';
    const search = document.getElementById('hosp-search-input')?.value || '';
    const emergencyOnly = document.getElementById('hosp-emergency-toggle')?.checked || false;
    const radiusFilter = document.getElementById('hosp-radius-filter')?.value || 'all';

    const grid = document.getElementById('patient-hospitals-grid');
    if (grid) {
      grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:30px; color:var(--text-muted);"><p>Loading accredited hospital facilities...</p></div>';
    }

    try {
      const signal = api.abortPrior('patient-hospitals');
      const params = {};
      if (city !== 'all') params.city = city;
      if (search) params.query_str = search;
      if (emergencyOnly) params.emergency_only = true;

      let hospitals = await api.get('/patient/hospitals', params, { signal });
      if (hospitals && hospitals.__aborted) return;

      if (hospitals && !Array.isArray(hospitals) && Array.isArray(hospitals.hospitals)) {
        hospitals = hospitals.hospitals;
      }
      if ((!hospitals || hospitals.length === 0) && (!params.city || params.city === 'all') && !params.query_str && !params.emergency_only) {
        if (typeof MockStore !== 'undefined' && Array.isArray(MockStore.hospitals) && MockStore.hospitals.length > 0) {
          hospitals = MockStore.hospitals;
        }
      }

      if (hospitals && hospitals.length > 0) {
        const userLoc = this.getUserLocationContext();
        hospitals.forEach(h => {
          const coords = this.getHospitalCoordinates(h);
          const dist = this.calculateDistanceKm(
            userLoc.lat,
            userLoc.lon,
            coords.lat,
            coords.lon
          );
          h._distanceKm = (dist !== null) ? dist : 15.0;
        });

        // Proximity radius filter (10, 20, 30, 40 km)
        if (radiusFilter !== 'all') {
          const maxKm = parseFloat(radiusFilter);
          if (!isNaN(maxKm)) {
            hospitals = hospitals.filter(h => h._distanceKm !== null && h._distanceKm <= maxKm);
          }
        }

        // Distance sorting: when sortByDist is true OR near-me is active
        if (sortByDist || this.isNearMeHospitalsActive) {
          hospitals.sort((a, b) => (a._distanceKm || 9999) - (b._distanceKm || 9999));
        }
      }

      this.renderHospitalCards(hospitals);
    } catch (err) {
      if (grid) {
        grid.innerHTML = `
          <div style="grid-column:1/-1; text-align:center; padding:36px 20px;">
            <p style="color:var(--danger); font-size:0.9rem; font-weight:500; margin-bottom:12px;">Error loading hospitals: ${escapeHtml(err.message)}</p>
            <button class="btn btn-secondary btn-sm" onclick="PatientModule.filterHospitals()">↻ Retry Hospital Search</button>
          </div>
        `;
      }
    }
  },

  renderHospitalCards(hospitals) {
    const grid = document.getElementById('patient-hospitals-grid');
    if (!grid) return;

    if (!hospitals || hospitals.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align:center; padding: 40px; color: var(--text-muted);">
          <p>No hospital facilities match your criteria. Please expand your search.</p>
        </div>
      `;
      return;
    }

    grid.innerHTML = hospitals.map(h => {
      let depts = [];
      if (Array.isArray(h.departments)) depts = h.departments;
      else if (h.departments_json) {
        try { depts = JSON.parse(h.departments_json); } catch (e) { depts = []; }
      }
      if (!depts || depts.length === 0) depts = ['General Medicine', 'Cardiology', 'Emergency Medicine'];
      
      const displayedDepts = depts.slice(0, 3);
      const remainingDepts = depts.length - displayedDepts.length;
      const hospImg = this.getHospitalImage(h);

      return `
        <div class="hospital-card">
          <div class="hospital-card-img-wrap">
            <img src="${hospImg}" class="hospital-card-img" alt="${escapeHtml(h.name)}"/>
            <span class="hospital-card-badge">★ ${h.rating || '4.8'} • NABH Certified</span>
          </div>
          <div class="hospital-card-body">
            <div class="hospital-card-name">${escapeHtml(h.name)}</div>
            <div class="hospital-card-locality">
              📍 ${escapeHtml(h.locality)}, ${escapeHtml(h.city)}
              ${h._distanceKm !== undefined && h._distanceKm !== null ? `<span class="distance-badge" style="margin-left:6px;">📍 ${h._distanceKm} km away</span>` : ''}
            </div>
            <div class="hospital-card-address">🏢 ${escapeHtml(h.address)}</div>

            <div class="hospital-card-chips">
              ${displayedDepts.map(d => `<span class="doc-chip" style="background:#eff6ff; color:#1d4ed8;">${escapeHtml(d)}</span>`).join('')}
              ${remainingDepts > 0 ? `<span class="doc-chip" style="background:#f1f5f9; color:#475569;">+${remainingDepts} more</span>` : ''}
            </div>

            <div class="hospital-card-info-row">
              <span>🕒 ${escapeHtml(h.opening_hours || '24x7 Emergency • OPD 08:00 - 20:00')}</span>
            </div>
            <div class="hospital-card-info-row">
              <span>👨‍⚕️ <strong>${h.available_doctors_count || 4} Available Specialists</strong></span>
            </div>
            <div class="hospital-card-info-row" style="color:var(--success); font-weight:600;">
              <span>🟢 ${h.appointment_availability || 'Slots Available Today & Tomorrow'}</span>
            </div>

            <div class="hospital-card-footer">
              <div class="hospital-card-fee">
                Starting at<br/><strong>₹${h.starting_fee || h.consultation_base_fee || 500}</strong>
              </div>
              <div class="hospital-card-actions">
                <button class="btn btn-secondary btn-sm" onclick="PatientModule.openHospitalModal(${h.id})">
                  View Hospital
                </button>
                <button class="btn btn-teal btn-sm" onclick="PatientModule.bookAtHospital(${h.id}, '${escapeHtml(h.name)}', '${escapeHtml(h.city)}')">
                  Book Appointment
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  async openHospitalModal(hospitalId) {
    try {
      const data = await api.get(`/patient/hospitals/${hospitalId}`);
      const h = data.hospital;
      const docs = data.doctors || [];

      const imgEl = document.getElementById('hosp-modal-img');
      if (imgEl) imgEl.src = this.getHospitalImage(h);
      document.getElementById('hosp-modal-name').textContent = h.name;
      document.getElementById('hosp-modal-meta').textContent = `📍 ${h.locality}, ${h.city} • 📞 ${h.phone || h.contact_phone} • ${h.opening_hours || '24x7 Emergency'}`;
      document.getElementById('hosp-modal-address').textContent = h.address;
      document.getElementById('hosp-modal-fee').textContent = `OPD Consultation: Starts ₹${h.starting_fee || 500}`;

      const deptsList = Array.isArray(h.departments) ? h.departments : ['General Medicine', 'Cardiology', 'Emergency Medicine'];
      document.getElementById('hosp-modal-depts').innerHTML = deptsList.map(d => `<span class="doc-chip" style="background:#eff6ff; color:#1d4ed8;">${escapeHtml(d)}</span>`).join('');

      const docsListEl = document.getElementById('hosp-modal-doctors-list');
      if (docs.length === 0) {
        docsListEl.innerHTML = '<p style="color:var(--text-muted); padding:10px 0;">Clinical specialist directory updating for this facility.</p>';
      } else {
        docsListEl.innerHTML = docs.map(doc => {
          const docAvatar = `/assets/doctors/doc_${((doc.id || 1) - 1) % 6 + 1}.jpg`;
          return `
          <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; border:1px solid var(--border-subtle); border-radius:var(--radius-md); margin-bottom:8px;">
            <div style="display:flex; align-items:center; gap:10px;">
              <img src="${docAvatar}" onerror="this.onerror=null; this.src=getInitialsAvatar('${escapeHtml(doc.doctor_name || doc.full_name)}', ${doc.id});" style="width:40px; height:40px; border-radius:50%; object-fit:cover;" />
              <div>
                <strong style="font-size:0.88rem;">${escapeHtml(doc.doctor_name || doc.full_name)}</strong>
                <div style="font-size:0.75rem; color:var(--text-secondary);">${escapeHtml(doc.department_name)} • ${escapeHtml(doc.specialization)}</div>
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:0.85rem; font-weight:700; color:var(--color-brand-teal);">₹${doc.consultation_fee}</div>
              <button class="btn btn-teal btn-sm" style="font-size:0.72rem; padding:3px 8px; margin-top:2px;" onclick="document.getElementById('hospital-details-modal').classList.remove('active'); PatientModule.selectDoctorForBooking(${doc.id}, '${escapeHtml(doc.doctor_name || doc.full_name)}', '${escapeHtml(doc.department_name)}')">Book Slot</button>
            </div>
          </div>
        `;
        }).join('');
      }

      document.getElementById('hospital-details-modal').classList.add('active');
    } catch (err) {
      showToast('Failed to load hospital details: ' + err.message, 'error');
    }
  },

  bookAtHospital(hospitalId, hospitalName, city) {
    this.openBookingModal();
    showToast(`Booking consultation at ${hospitalName}, ${city}`, 'info');
  },



  async loadAppointmentsList(filter = 'all') {
    this.currentFilter = filter;
    const tableBody = document.getElementById('pat-appointments-table-body');
    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:30px; color:var(--text-muted);">Loading appointments...</td></tr>';
    }
    try {
      const appts = await api.get('/patient/appointments', { status_filter: filter });
      this.renderAppointmentsTable(appts);
    } catch (err) {
      if (tableBody) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="7" style="text-align:center; padding:30px; color:var(--danger);">
              <p style="margin-bottom:8px;">Failed to load appointments: ${escapeHtml(err.message)}</p>
              <button class="btn btn-secondary btn-sm" onclick="PatientModule.loadAppointmentsList('${filter}')">↻ Retry</button>
            </td>
          </tr>
        `;
      }
      showToast('Failed to load appointments: ' + err.message, 'error');
    }
  },

  renderAppointmentsTable(appts) {
    const tableBody = document.getElementById('pat-appointments-table-body');
    if (!tableBody) return;

    if (!appts || appts.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align:center; padding: 30px; color: var(--text-muted);">
            No appointments found in this category.
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = appts.map(a => `
      <tr>
        <td style="font-weight:700; font-family:var(--font-heading);">${a.appointment_number}</td>
        <td>
          <div style="font-weight:600;">${escapeHtml(a.doctor_name)}</div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(a.department_name)} • ${escapeHtml(a.specialization)}</div>
        </td>
        <td>
          <div>${a.scheduled_date}</div>
          <div style="font-size:0.75rem; color:var(--text-muted);">${a.scheduled_time} (${a.duration_minutes}m)</div>
        </td>
        <td>
          <span class="status-badge ${a.consultation_type === 'Video' ? 'badge-in-progress' : 'badge-scheduled'}">
            ${a.consultation_type}
          </span>
        </td>
        <td>
          <span class="status-badge badge-${a.status}">${a.status}</span>
        </td>
        <td style="max-width:200px; font-size:0.8rem; color:var(--text-secondary);" title="${escapeHtml(a.reason_for_visit)}">
          ${escapeHtml(a.reason_for_visit ? a.reason_for_visit.substring(0, 45) + '...' : '-')}
        </td>
        <td style="text-align:right;">
          <div style="display:inline-flex; gap:6px;">
            ${a.consultation_type === 'Video' && (a.status === 'confirmed' || a.status === 'in_progress') ? `
              <button class="btn btn-teal btn-sm" onclick="PatientModule.openTelehealthRoom(${a.id})">📹 Join</button>
            ` : ''}
            <button class="btn btn-secondary btn-sm" onclick="PatientModule.viewAppointmentDetails(${a.id})">Details</button>
            ${(a.status === 'scheduled' || a.status === 'confirmed') ? `
              <button class="btn btn-secondary btn-sm" onclick="PatientModule.openRescheduleModal(${a.id}, '${a.scheduled_date}', '${a.scheduled_time}')">Reschedule</button>
              <button class="btn btn-outline-danger btn-sm" onclick="PatientModule.openCancelModal(${a.id})">Cancel</button>
            ` : ''}
          </div>
        </td>
      </tr>
    `).join('');
  },

  async viewAppointmentDetails(apptId) {
    try {
      const data = await api.get(`/patient/appointments/${apptId}`);
      const a = data.appointment;
      const modal = document.getElementById('generic-detail-modal');
      const body = document.getElementById('generic-detail-modal-body');
      document.getElementById('generic-detail-modal-title').textContent = `Appointment #${a.appointment_number}`;

      let notesHtml = '';
      if (data.consultation_notes) {
        notesHtml = `
          <div style="margin-top:16px; padding:14px; background:var(--bg-surface-alt); border-radius:var(--radius-md);">
            <h4 style="font-size:0.92rem; margin-bottom:8px; color:var(--color-brand-primary);">Clinical Consultation Summary</h4>
            <p style="font-size:0.85rem; margin-bottom:6px;"><strong>Diagnosis:</strong> ${escapeHtml(data.consultation_notes.diagnosis)}</p>
            <p style="font-size:0.85rem; margin-bottom:6px;"><strong>Clinical Notes:</strong> ${escapeHtml(data.consultation_notes.clinical_notes)}</p>
            <p style="font-size:0.85rem; margin-bottom:6px;"><strong>Physician Instructions:</strong> ${escapeHtml(data.consultation_notes.instructions || 'Continue standard recovery care.')}</p>
          </div>
        `;
      }

      let rxHtml = '';
      if (data.prescription && data.prescription.medications) {
        rxHtml = `
          <div style="margin-top:16px; padding:14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:var(--radius-md);">
            <h4 style="font-size:0.92rem; margin-bottom:8px; color:#166534;">Authorized Electronic Prescription</h4>
            <div style="font-size:0.82rem;">
              ${data.prescription.medications.map(m => `
                <div style="margin-bottom:6px;">
                  <strong>• ${escapeHtml(m.medication_name)}</strong> (${escapeHtml(m.dosage)}) — ${escapeHtml(m.frequency)} for ${escapeHtml(m.duration)}
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }

      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <h3 style="font-size:1.15rem;">${escapeHtml(a.doctor_name)}</h3>
              <div style="color:var(--text-muted); font-size:0.85rem;">${escapeHtml(a.department_name)} • ${escapeHtml(a.specialization)}</div>
            </div>
            <span class="status-badge badge-${a.status}">${a.status}</span>
          </div>
          <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.85rem; margin-top:8px;">
            <div><strong>Date & Time:</strong> ${a.scheduled_date} at ${a.scheduled_time}</div>
            <div><strong>Mode:</strong> ${a.consultation_type}</div>
            <div><strong>Location:</strong> ${escapeHtml(a.room_number || 'Main Clinic')}</div>
            <div><strong>Fee:</strong> ₹${a.consultation_fee}</div>
          </div>
          <div style="margin-top:8px; font-size:0.85rem;">
            <strong>Reason for Visit:</strong>
            <p style="color:var(--text-secondary); margin-top:4px;">${escapeHtml(a.reason_for_visit)}</p>
          </div>
          ${notesHtml}
          ${rxHtml}
        </div>
      `;
      modal.classList.add('active');
    } catch (err) {
      showToast('Error fetching details: ' + err.message, 'error');
    }
  },

  openBookingModal(doctorId = null) {
    this.selectedSlotTime = null;
    const modal = document.getElementById('booking-modal');
    modal.classList.add('active');

    // Populate departments in booking modal
    const deptSelect = document.getElementById('book-dept-select');
    deptSelect.innerHTML = '<option value="">-- All Departments --</option>' + 
      AppState.allDepartments.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');

    // Populate doctors
    this.updateBookingDoctorSelect();

    // Default target date to today
    const dateInput = document.getElementById('book-date-input');
    dateInput.value = new Date().toISOString().split('T')[0];

    if (doctorId) {
      document.getElementById('book-doctor-select').value = doctorId;
      this.fetchAvailableSlots();
    }
  },

  selectDoctorForBooking(docId, docName, deptName) {
    this.openBookingModal(docId);
  },

  updateBookingDoctorSelect() {
    const deptId = document.getElementById('book-dept-select').value;
    const docSelect = document.getElementById('book-doctor-select');
    
    let filtered = AppState.allDoctors;
    if (deptId) {
      filtered = filtered.filter(d => d.department_id == deptId);
    }

    docSelect.innerHTML = '<option value="">-- Select Physician --</option>' +
      filtered.map(d => `<option value="${d.id}">${escapeHtml(d.full_name)} (${escapeHtml(d.specialization)})</option>`).join('');
  },

  selectStrategy(strategyKey, el) {
    document.getElementById('book-strategy-input').value = strategyKey;
    document.querySelectorAll('.strategy-pill').forEach(p => p.classList.remove('active'));
    if (el) el.classList.add('active');
    // Re-run optimization with the chosen strategy
    this.triggerAISmartRecommendation();
  },

  async triggerAISmartRecommendation() {
    const deptId = document.getElementById('book-dept-select').value || null;
    const urgency = document.getElementById('book-urgency-select').value || 'routine';
    const strategy = document.getElementById('book-strategy-input')?.value || 'best_available';
    const timeWindow = document.getElementById('book-timewindow-select')?.value || 'any';
    const mode = document.getElementById('book-mode-select').value || 'In-Person';
    const reason = document.getElementById('book-reason-input').value.trim() || 'General clinical consultation and review';
    const dateStr = document.getElementById('book-date-input').value;
    const prefDocId = document.getElementById('book-doctor-select').value || null;

    const banner = document.getElementById('ai-recommendation-banner');
    banner.style.display = 'block';
    banner.innerHTML = `<div style="padding:16px; text-align:center; color:var(--text-muted);">🤖 Evaluating 24 clinical parameters, queue loads, and physician availability...</div>`;

    try {
      const res = await api.post('/appointments/ai-recommend', {
        department_id: deptId ? parseInt(deptId) : null,
        urgency: urgency,
        allocation_strategy: strategy,
        preferred_time_range: timeWindow,
        preferred_doctor_id: prefDocId ? parseInt(prefDocId) : null,
        preferred_date: dateStr,
        consultation_type: mode,
        reason_for_visit: reason
      });

      if (res.recommendations && res.recommendations.length > 0) {
        const top = res.recommendations[0];
        const strategyLabels = {
          'best_available': '⭐ Multi-Factor AI Engine',
          'fastest_available': '⚡ Fastest Available Slot',
          'preferred_doctor': '👨‍⚕️ Doctor Continuity',
          'preferred_time': '⏰ Preferred Time Window',
          'balanced_workload': '⚖️ Balanced Hospital Load'
        };

        const explanationItems = (top.explanation_points || [top.recommendation_reason])
          .map(pt => `<div class="factor-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg><span>${escapeHtml(pt)}</span></div>`)
          .join('');

        const breakdown = top.breakdown || {};

        banner.innerHTML = `
          <div class="ai-recommend-card" style="border: 1.5px solid var(--color-brand-teal); border-radius: var(--radius-md); padding: 16px; background: #f0fdfa;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 8px;">
              <div>
                <span class="status-badge badge-confirmed" style="font-size:0.7rem; font-weight:700;">
                  ${strategyLabels[top.allocation_strategy || strategy] || 'AI Optimized'}
                </span>
                <h4 style="font-size:1.05rem; margin-top:4px; color:var(--text-primary);">
                  Recommended: ${escapeHtml(top.doctor_name)}
                </h4>
                <div style="font-size:0.8rem; color:var(--text-secondary);">
                  ${escapeHtml(top.department_name)} • ${escapeHtml(top.specialization)}
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-size:1.4rem; font-weight:800; color:var(--color-brand-teal); line-height:1;">
                  ${top.suitability_score}%
                </div>
                <div style="font-size:0.68rem; color:var(--text-muted); text-transform:uppercase;">Match Score</div>
              </div>
            </div>

            <p style="font-size:0.82rem; color:var(--text-secondary); margin-bottom: 10px;">
              ${escapeHtml(top.recommendation_reason)}
            </p>

            <div style="display:flex; gap:14px; font-size:0.78rem; background:rgba(255,255,255,0.7); padding:8px 12px; border-radius:var(--radius-sm); margin-bottom:10px;">
              <span>🗓️ Slot: <strong>${top.recommended_slot}</strong></span>
              <span>⏱️ Est. Wait: <strong>~${top.estimated_wait_time} mins</strong></span>
              <span>👥 Current Queue: <strong>${top.current_queue_length} patients</strong></span>
            </div>

            <!-- "Why this recommendation?" Expandable Card -->
            <div class="explanation-card">
              <div class="explanation-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                <span>💡 Why this recommendation? (Click to expand factor weights)</span>
                <span>▼</span>
              </div>
              <div class="explanation-body" style="display:none;">
                <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:6px;">
                  Engine evaluated 24 real-time operational parameters including physician credentials, shift capacity, queue wait times, and continuity of care:
                </div>
                <div class="factor-list">
                  ${explanationItems}
                </div>
                ${breakdown.clinical_suitability !== undefined ? `
                  <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:8px; margin-top:10px; padding-top:8px; border-top:1px dashed var(--border-subtle); text-align:center;">
                    <div>
                      <div style="font-weight:700; color:#0d9488;">${breakdown.clinical_suitability}/100</div>
                      <div style="font-size:0.68rem; color:var(--text-muted);">Specialty Fit</div>
                    </div>
                    <div>
                      <div style="font-weight:700; color:#0284c7;">${breakdown.workload_balancing}/100</div>
                      <div style="font-size:0.68rem; color:var(--text-muted);">Workload Index</div>
                    </div>
                    <div>
                      <div style="font-weight:700; color:#7c3aed;">${breakdown.queue_efficiency}/100</div>
                      <div style="font-size:0.68rem; color:var(--text-muted);">Queue Flow</div>
                    </div>
                    <div>
                      <div style="font-weight:700; color:#059669;">${breakdown.schedule_fit}/100</div>
                      <div style="font-size:0.68rem; color:var(--text-muted);">Schedule Fit</div>
                    </div>
                  </div>
                ` : ''}
                ${top.trade_offs ? `
                  <div class="tradeoff-banner">
                    ⚠️ <strong>Trade-off:</strong> ${escapeHtml(top.trade_offs)}
                  </div>
                ` : ''}
              </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
              <span style="font-size:0.7rem; color:#0f766e; font-style:italic;">
                ${escapeHtml(top.disclaimer)}
              </span>
              <button class="btn btn-teal btn-sm" onclick="PatientModule.applyAIRecommendation(${top.doctor_id}, '${top.recommended_slot}')">
                Apply Recommended Doctor & Slot
              </button>
            </div>
          </div>
        `;
      } else {
        banner.innerHTML = `<p style="padding:12px; color:var(--text-muted);">No specialized recommendation found for criteria. You may select a physician manually below.</p>`;
      }
    } catch (err) {
      banner.innerHTML = `<p style="color:var(--danger); padding:10px;">Recommendation engine notice: ${err.message}</p>`;
    }
  },

  applyAIRecommendation(doctorId, slotTime) {
    document.getElementById('book-doctor-select').value = doctorId;
    this.selectedSlotTime = slotTime;
    this.fetchAvailableSlots();
    showToast(`Applied AI recommendation: Slot at ${slotTime}`, 'success');
  },

  async checkInPatient(apptId) {
    try {
      const res = await api.put(`/appointments/${apptId}/queue-status`, { action: 'check_in' });
      showToast(res.message || 'Checked in successfully at clinic! Live queue updated.', 'success');
      this.loadDashboard();
    } catch (err) {
      showToast('Check-in error: ' + err.message, 'error');
    }
  },

  async fetchAvailableSlots() {
    const docId = document.getElementById('book-doctor-select').value;
    const dateStr = document.getElementById('book-date-input').value;
    const container = document.getElementById('slot-selection-container');

    if (!docId || !dateStr) {
      container.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">Select doctor and date to view consultation slots.</p>';
      return;
    }

    container.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">Checking live doctor availability...</p>';

    try {
      const data = await api.get('/appointments/slots', { doctor_id: docId, date_str: dateStr });
      if (!data.is_working_day) {
        container.innerHTML = `<p style="color:var(--danger); font-size:0.85rem;">⚠️ ${escapeHtml(data.message)}</p>`;
        return;
      }

      container.innerHTML = `
        <div class="form-label">Available Slots for ${data.date} (${data.available_slots_count} open):</div>
        <div class="slot-grid">
          ${data.slots.map(s => `
            <button type="button" class="slot-btn ${s.status} ${PatientModule.selectedSlotTime === s.time ? 'selected' : ''}"
              ${!s.is_available ? 'disabled' : ''}
              onclick="PatientModule.chooseSlot('${s.time}', this)">
              ${s.display_time}
            </button>
          `).join('')}
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<p style="color:var(--danger); font-size:0.85rem;">Failed to load slots: ${err.message}</p>`;
    }
  },

  chooseSlot(time, btn) {
    this.selectedSlotTime = time;
    document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
  },

  async submitBooking() {
    const docId = document.getElementById('book-doctor-select').value;
    const dateStr = document.getElementById('book-date-input').value;
    const mode = document.getElementById('book-mode-select').value;
    const urgency = document.getElementById('book-urgency-select').value;
    const reason = document.getElementById('book-reason-input').value.trim();

    if (!docId) {
      showToast('Please select a doctor.', 'error');
      return;
    }
    if (!dateStr) {
      showToast('Please choose an appointment date.', 'error');
      return;
    }
    if (!this.selectedSlotTime) {
      showToast('Please choose an available time slot.', 'error');
      return;
    }
    if (!reason) {
      showToast('Please enter the reason for visit.', 'error');
      return;
    }

    try {
      const res = await api.post('/patient/appointments', {
        doctor_id: parseInt(docId),
        scheduled_date: dateStr,
        scheduled_time: this.selectedSlotTime,
        consultation_type: mode,
        priority: urgency,
        reason_for_visit: reason
      });

      document.getElementById('booking-modal').classList.remove('active');
      showToast(`Appointment #${res.appointment_number} confirmed!`, 'success');
      this.loadDashboard();
      this.loadAppointmentsList();
    } catch (err) {
      showToast('Booking failed: ' + err.message, 'error');
    }
  },

  openRescheduleModal(apptId, currDate, currTime) {
    const modal = document.getElementById('reschedule-modal');
    document.getElementById('reschedule-appt-id').value = apptId;
    document.getElementById('reschedule-date-input').value = currDate;
    document.getElementById('reschedule-time-input').value = currTime;
    modal.classList.add('active');
  },

  async submitReschedule() {
    const apptId = document.getElementById('reschedule-appt-id').value;
    const newDate = document.getElementById('reschedule-date-input').value;
    const newTime = document.getElementById('reschedule-time-input').value;
    const reason = document.getElementById('reschedule-reason-input').value.trim();

    try {
      await api.put(`/patient/appointments/${apptId}/reschedule`, {
        scheduled_date: newDate,
        scheduled_time: newTime,
        reason: reason || 'Patient schedule change'
      });
      document.getElementById('reschedule-modal').classList.remove('active');
      showToast('Appointment successfully rescheduled.', 'success');
      this.loadDashboard();
      this.loadAppointmentsList();
    } catch (err) {
      showToast('Reschedule failed: ' + err.message, 'error');
    }
  },

  openCancelModal(apptId) {
    const modal = document.getElementById('cancel-modal');
    document.getElementById('cancel-appt-id').value = apptId;
    modal.classList.add('active');
  },

  async submitCancellation() {
    const apptId = document.getElementById('cancel-appt-id').value;
    const reason = document.getElementById('cancel-reason-input').value.trim();
    if (!reason) {
      showToast('Please specify a cancellation reason.', 'error');
      return;
    }

    try {
      await api.put(`/patient/appointments/${apptId}/cancel`, { reason });
      document.getElementById('cancel-modal').classList.remove('active');
      showToast('Appointment has been cancelled.', 'info');
      this.loadDashboard();
      this.loadAppointmentsList();
    } catch (err) {
      showToast('Cancellation failed: ' + err.message, 'error');
    }
  },

  async loadMedicalHistory() {
    try {
      const data = await api.get('/patient/medical-history');
      const container = document.getElementById('pat-medical-history-container');
      
      let chronicHtml = (data.chronic_conditions || 'None documented')
        .split(',')
        .map(c => `<span class="doc-chip" style="background:#fef3c7; color:#92400e; font-weight:600;">${escapeHtml(c.trim())}</span>`)
        .join(' ');

      let allergyHtml = (data.allergies || 'No known allergies')
        .split(',')
        .map(a => `<span class="doc-chip" style="background:#fee2e2; color:#b91c1c; font-weight:600;">⚠️ ${escapeHtml(a.trim())}</span>`)
        .join(' ');

      let recordsHtml = '';
      if (data.clinical_records && data.clinical_records.length > 0) {
        recordsHtml = data.clinical_records.map(r => `
          <div style="padding:16px; border:1px solid var(--border-subtle); border-radius:var(--radius-md); margin-bottom:12px; background:var(--bg-surface);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <span style="font-weight:700; font-size:0.95rem;">${escapeHtml(r.title)}</span>
              <span style="font-size:0.75rem; color:var(--text-muted);">${r.record_date}</span>
            </div>
            <div style="font-size:0.78rem; color:var(--color-brand-primary); margin-bottom:6px;">
              ${escapeHtml(r.record_type)} • Documented by ${escapeHtml(r.doctor_name || 'Hospital Staff')}
            </div>
            <p style="font-size:0.85rem; color:var(--text-secondary);">${escapeHtml(r.description)}</p>
          </div>
        `).join('');
      } else {
        recordsHtml = '<p style="color:var(--text-muted);">No clinical diagnosis records found.</p>';
      }

      container.innerHTML = `
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px;">
          <div class="clinical-card">
            <h4 style="font-size:0.95rem; margin-bottom:8px;">Documented Chronic Conditions</h4>
            <div>${chronicHtml}</div>
          </div>
          <div class="clinical-card">
            <h4 style="font-size:0.95rem; margin-bottom:8px;">Verified Allergies</h4>
            <div>${allergyHtml}</div>
          </div>
        </div>
        <div class="clinical-card">
          <div class="card-header-flex">
            <h3 class="card-title">Chronological Medical Records Ledger</h3>
            <button class="btn btn-teal btn-sm" onclick="PatientModule.generateAIHealthSummary()">
              ✨ Generate AI Health Summary
            </button>
          </div>
          <div>${recordsHtml}</div>
        </div>
      `;
    } catch (err) {
      showToast('Failed to load medical history: ' + err.message, 'error');
    }
  },

  async loadHealthReports() {
    const typeFilter = document.getElementById('pat-report-type-filter')?.value || 'all';
    const query = document.getElementById('pat-report-search')?.value || '';

    try {
      const reports = await api.get('/patient/health-reports', { report_type: typeFilter, query_str: query });
      const tableBody = document.getElementById('pat-reports-table-body');
      if (!tableBody) return;

      if (!reports || reports.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:var(--text-muted);">No laboratory or radiology reports found.</td></tr>`;
        return;
      }

      tableBody.innerHTML = reports.map(r => `
        <tr>
          <td style="font-weight:700;">${escapeHtml(r.title)}</td>
          <td><span class="status-badge badge-confirmed">${escapeHtml(r.report_type)}</span></td>
          <td>${r.report_date}</td>
          <td>${escapeHtml(r.hospital_facility)}</td>
          <td style="font-size:0.8rem; color:var(--text-muted);">${r.file_name} (${r.file_size})</td>
          <td style="text-align:right;">
            <button class="btn btn-primary btn-sm" onclick="PatientModule.openReportPreview(${r.id})">Preview</button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      showToast('Failed to load reports: ' + err.message, 'error');
    }
  },

  async openReportPreview(reportId) {
    try {
      const r = await api.get(`/patient/health-reports/${reportId}`);
      const modal = document.getElementById('generic-detail-modal');
      document.getElementById('generic-detail-modal-title').textContent = r.title;
      
      const body = document.getElementById('generic-detail-modal-body');
      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:var(--text-muted); border-bottom:1px solid var(--border-subtle); padding-bottom:8px;">
            <span>Facility: <strong>${escapeHtml(r.hospital_facility)}</strong></span>
            <span>Ordering Doctor: <strong>${escapeHtml(r.ordering_doctor || 'Hospital Staff')}</strong></span>
            <span>Date: <strong>${r.report_date}</strong></span>
          </div>
          <div style="background:#f8fafc; border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:16px; font-family:monospace; font-size:0.82rem; white-space:pre-wrap; max-height:360px; overflow-y:auto; line-height:1.5;">${escapeHtml(r.file_content_or_preview || r.summary)}</div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.75rem; color:var(--text-muted);">Verified Electronic Lab Record • Archival ID: ${r.file_name}</span>
            <button class="btn btn-secondary btn-sm" onclick="showToast('Electronic laboratory record archived.', 'success')">💾 Download Verified PDF</button>
          </div>
        </div>
      `;
      modal.classList.add('active');
    } catch (err) {
      showToast('Error opening report: ' + err.message, 'error');
    }
  },

  async generateAIHealthSummary() {
    const modal = document.getElementById('generic-detail-modal');
    document.getElementById('generic-detail-modal-title').textContent = 'AI Health Record Digest';
    const body = document.getElementById('generic-detail-modal-body');
    body.innerHTML = '<div style="text-align:center; padding:30px; color:var(--text-muted);">Synthesizing clinical timeline, allergies, lab findings, and medications...</div>';
    modal.classList.add('active');

    try {
      const summary = await api.post('/patient/ai-health-summary');

      let obsHtml = (summary.key_observations || []).map(o => `<li style="margin-bottom:6px;">${escapeHtml(o)}</li>`).join('');
      let timelineHtml = (summary.chronological_history || []).map(h => `
        <div style="padding:10px; border-left:3px solid var(--color-brand-primary); margin-bottom:8px; background:var(--bg-surface-alt); border-radius:0 var(--radius-sm) var(--radius-sm) 0;">
          <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:700;">
            <span>${escapeHtml(h.title)}</span>
            <span style="color:var(--text-muted);">${h.date}</span>
          </div>
          <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:2px;">${escapeHtml(h.detail)}</div>
          <div style="font-size:0.7rem; color:var(--color-brand-teal); margin-top:3px;">Source: ${escapeHtml(h.source)}</div>
        </div>
      `).join('');

      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:16px;">
          <div style="background:#f0fdfa; border:1px solid #99f6e4; padding:12px 16px; border-radius:var(--radius-md);">
            <div style="font-size:0.85rem; font-weight:700; color:#0f766e; margin-bottom:4px;">Patient: ${escapeHtml(summary.patient_name)} (MRN: ${summary.patient_mrn})</div>
            <div style="font-size:0.75rem; color:#115e59;">Total Records Aggregated: ${summary.total_records_analyzed} • Generated: ${summary.generated_at}</div>
          </div>

          <div>
            <h4 style="font-size:0.95rem; margin-bottom:8px;">Key Documented Clinical Observations</h4>
            <ul style="font-size:0.85rem; color:var(--text-secondary); padding-left:20px;">
              ${obsHtml}
            </ul>
          </div>

          <div>
            <h4 style="font-size:0.95rem; margin-bottom:8px;">Chronological Timeline (Latest Entries)</h4>
            <div>${timelineHtml}</div>
          </div>

          <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:var(--radius-md); padding:12px; font-size:0.75rem; color:#92400e; font-style:italic;">
            ${escapeHtml(summary.disclaimer)}
          </div>
        </div>
      `;
    } catch (err) {
      body.innerHTML = `<p style="color:var(--danger); padding:20px;">Summary failed: ${err.message}</p>`;
    }
  },

  openTelehealthRoom(apptId) {
    const modal = document.getElementById('telehealth-modal');
    modal.classList.add('active');

    let seconds = 0;
    const timerEl = document.getElementById('telehealth-timer');
    if (this.activeTelehealthInterval) clearInterval(this.activeTelehealthInterval);

    this.activeTelehealthInterval = setInterval(() => {
      seconds++;
      const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
      const secs = String(seconds % 60).padStart(2, '0');
      if (timerEl) timerEl.textContent = `${mins}:${secs}`;
    }, 1000);
  },

  closeTelehealthRoom() {
    const modal = document.getElementById('telehealth-modal');
    modal.classList.remove('active');
    if (this.activeTelehealthInterval) {
      clearInterval(this.activeTelehealthInterval);
      this.activeTelehealthInterval = null;
    }
    showToast('Telehealth consultation disconnected.', 'info');
  },

  /* ================= STANDBY WAITLIST MODULE ================= */
  async loadWaitlist() {
    try {
      const waitlist = await api.get('/appointments/waitlist');
      const container = document.getElementById('pat-waitlist-cards-container');
      if (!container) return;

      if (!waitlist || waitlist.length === 0) {
        container.innerHTML = `
          <div style="text-align:center; padding:36px; border:1px dashed var(--border-medium); border-radius:var(--radius-md);">
            <div style="font-size:2rem; margin-bottom:8px;">📋</div>
            <h4 style="margin-bottom:4px;">No Active Standby Requests</h4>
            <p style="color:var(--text-muted); font-size:0.85rem; max-width:420px; margin:0 auto 14px;">
              Join our priority standby waitlist to automatically receive earliest notification whenever another patient cancels.
            </p>
            <button class="btn btn-teal btn-sm" onclick="PatientModule.openJoinWaitlistModal()">+ Join Standby Waitlist</button>
          </div>
        `;
        return;
      }

      container.innerHTML = waitlist.map(w => `
        <div class="clinical-card" style="padding:18px; border-left: 4px solid ${w.status === 'offered' ? 'var(--color-brand-teal)' : 'var(--color-brand-primary)'};">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
            <div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span class="status-badge ${w.status === 'offered' ? 'badge-in-progress' : 'badge-scheduled'}">
                  ${w.status === 'offered' ? '⚡ Slot Offered!' : 'Active Standby'}
                </span>
                <span class="status-badge badge-${(w.priority || 'routine').toLowerCase()}">
                  ${w.priority.toUpperCase()}
                </span>
                <span style="font-size:0.75rem; color:var(--text-muted);">Priority Score: <strong>${w.priority_score}</strong></span>
              </div>
              <h4 style="font-size:1.05rem; margin-top:6px;">${escapeHtml(w.department_name)}</h4>
              <div style="font-size:0.82rem; color:var(--text-secondary);">
                Target Date: <strong>${w.preferred_date}</strong> • Window: <strong>${w.preferred_time_range}</strong>
                ${w.doctor_name ? ` • Preferred: <strong>${escapeHtml(w.doctor_name)}</strong>` : ''}
              </div>
            </div>
            <div style="text-align:right;">
              ${w.status === 'offered' && w.offered_appointment_id ? `
                <button class="btn btn-teal btn-sm" onclick="PatientModule.claimWaitlistSlot(${w.id}, ${w.offered_appointment_id})">
                  Claim Offered Slot
                </button>
              ` : `
                <button class="btn btn-outline-danger btn-sm" onclick="PatientModule.declineWaitlistSlot(${w.id})">
                  Cancel Standby
                </button>
              `}
            </div>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted); background:var(--bg-surface-alt); padding:8px 12px; border-radius:var(--radius-sm);">
            <strong>Reason:</strong> ${escapeHtml(w.reason_for_visit)}
          </div>
        </div>
      `).join('');
    } catch (err) {
      showToast('Failed to load waitlist: ' + err.message, 'error');
    }
  },

  openJoinWaitlistModal() {
    const deptSelect = document.getElementById('waitlist-dept-select');
    deptSelect.innerHTML = '<option value="">-- Select Department --</option>' +
      AppState.allDepartments.map(d => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');

    this.updateWaitlistDoctorSelect();
    document.getElementById('waitlist-date-input').value = new Date().toISOString().split('T')[0];
    document.getElementById('join-waitlist-modal').classList.add('active');
  },

  updateWaitlistDoctorSelect() {
    const deptId = document.getElementById('waitlist-dept-select')?.value;
    const docSelect = document.getElementById('waitlist-doc-select');
    if (!docSelect) return;

    let filtered = AppState.allDoctors;
    if (deptId) {
      filtered = filtered.filter(d => d.department_id == deptId);
    }
    docSelect.innerHTML = '<option value="">Any Available Specialist (Recommended)</option>' +
      filtered.map(d => `<option value="${d.id}">${escapeHtml(d.full_name)}</option>`).join('');
  },

  async submitJoinWaitlist() {
    const deptId = document.getElementById('waitlist-dept-select').value;
    const docId = document.getElementById('waitlist-doc-select').value;
    const priority = document.getElementById('waitlist-priority-select').value;
    const dateStr = document.getElementById('waitlist-date-input').value;
    const timeRange = document.getElementById('waitlist-timewindow-select').value;
    const reason = document.getElementById('waitlist-reason-input').value.trim();

    if (!deptId) {
      showToast('Please select a department for standby waitlist.', 'error');
      return;
    }
    if (!reason) {
      showToast('Please provide reason for standby consultation.', 'error');
      return;
    }

    try {
      const res = await api.post('/appointments/waitlist', {
        department_id: parseInt(deptId),
        doctor_id: docId ? parseInt(docId) : null,
        preferred_date: dateStr || new Date().toISOString().split('T')[0],
        preferred_time_range: timeRange,
        priority: priority,
        reason_for_visit: reason,
        consultation_type: 'In-Person',
        allocation_strategy: 'fastest_available'
      });

      document.getElementById('join-waitlist-modal').classList.remove('active');
      showToast(res.message || 'Successfully placed on priority standby waitlist!', 'success');
      this.loadWaitlist();
    } catch (err) {
      showToast('Waitlist join failed: ' + err.message, 'error');
    }
  },

  async claimWaitlistSlot(waitlistId, apptId) {
    try {
      const res = await api.post(`/appointments/waitlist/${waitlistId}/claim`, { appointment_id: apptId });
      showToast(res.message || 'Standby slot claimed and confirmed!', 'success');
      this.loadDashboard();
      this.loadWaitlist();
      this.loadAppointmentsList();
    } catch (err) {
      showToast('Slot claim failed: ' + err.message, 'error');
    }
  },

  async declineWaitlistSlot(waitlistId) {
    try {
      await api.delete(`/appointments/waitlist/${waitlistId}`);
      showToast('Standby request cancelled.', 'info');
      this.loadDashboard();
      this.loadWaitlist();
    } catch (err) {
      showToast('Cancellation error: ' + err.message, 'error');
    }
  },

  /* ================= UNIFIED CLINICAL TIMELINE MODULE ================= */
  timelineEvents: [],
  currentTimelineFilter: 'all',

  async loadUnifiedTimeline() {
    try {
      const data = await api.get('/patient/timeline');
      this.timelineEvents = data.timeline || [];
      this.renderUnifiedTimeline();
    } catch (err) {
      showToast('Failed to load clinical timeline: ' + err.message, 'error');
    }
  },

  filterTimeline(category) {
    this.currentTimelineFilter = category;
    this.renderUnifiedTimeline();
  },

  renderUnifiedTimeline() {
    const container = document.getElementById('pat-timeline-container');
    if (!container) return;

    let events = this.timelineEvents;
    if (this.currentTimelineFilter !== 'all') {
      events = events.filter(e => e.event_type === this.currentTimelineFilter);
    }

    if (!events || events.length === 0) {
      container.innerHTML = `<p style="padding:24px; color:var(--text-muted); text-align:center;">No timeline events recorded in this category.</p>`;
      return;
    }

    const typeIcons = {
      'appointment': '🗓️',
      'diagnosis': '🩺',
      'prescription': '💊',
      'report': '🔬'
    };

    container.innerHTML = events.map(e => `
      <div class="timeline-entry">
        <div class="timeline-dot dot-${e.event_type}"></div>
        <div class="timeline-card-box">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.1rem;">${typeIcons[e.event_type] || '📄'}</span>
              <div>
                <strong style="font-size:0.95rem;">${escapeHtml(e.title)}</strong>
                <div style="font-size:0.75rem; color:var(--color-brand-primary); font-weight:600;">
                  ${escapeHtml(e.category)} • ${escapeHtml(e.doctor_name || 'Hospital Staff')}
                </div>
              </div>
            </div>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:500;">${e.event_date}</span>
          </div>
          <p style="font-size:0.84rem; color:var(--text-secondary); margin-top:6px; line-height:1.4;">
            ${escapeHtml(e.description || '')}
          </p>
        </div>
      </div>
    `).join('');
  }
};

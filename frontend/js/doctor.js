// Doctor Clinical Module
const DoctorModule = {
  prescriptionItems: [],
  activeConsultationApptId: null,

  async loadOverview() {
    try {
      const data = await api.get('/doctor/overview');
      this.renderOverview(data);
    } catch (err) {
      showToast('Failed to load doctor overview: ' + err.message, 'error');
    }
  },

  renderOverview(data) {
    const stats = data.today_stats;
    document.getElementById('doc-stat-waiting').textContent = stats.patients_waiting;
    document.getElementById('doc-stat-inprogress').textContent = stats.in_progress;
    document.getElementById('doc-stat-completed').textContent = stats.completed;
    const noShowEl = document.getElementById('doc-stat-noshow');
    if (noShowEl) noShowEl.textContent = stats.no_shows;
    document.getElementById('doc-stat-workload').textContent = `${stats.workload_percentage}%`;

    // Toggle status button
    const toggleBtn = document.getElementById('doc-toggle-avail-btn');
    if (toggleBtn) {
      toggleBtn.className = data.is_available ? 'btn btn-teal btn-sm' : 'btn btn-secondary btn-sm';
      toggleBtn.textContent = data.is_available ? '● Available On-Duty' : '○ Marked Off-Duty';
    }

    // Workload balancing recommendation banner
    const insightContainer = document.getElementById('doc-workload-insight-container');
    if (insightContainer) {
      if (data.workload_insights && data.workload_insights.recommendations && data.workload_insights.recommendations.length > 0) {
        insightContainer.innerHTML = data.workload_insights.recommendations.map(rec => `
          <div class="bottleneck-card level-${rec.severity === 'high' ? 'high' : 'moderate'}">
            <span style="font-size:1.3rem;">⚖️</span>
            <div style="flex:1;">
              <div style="font-weight:700; font-size:0.88rem; color:${rec.severity === 'high' ? '#b91c1c' : '#92400e'};">
                Operational Workload Insight: ${rec.action.toUpperCase()}
              </div>
              <p style="font-size:0.8rem; color:var(--text-secondary); margin-top:2px;">
                ${escapeHtml(rec.reason)}
              </p>
            </div>
          </div>
        `).join('');
      } else {
        insightContainer.innerHTML = '';
      }
    }

    // Render today's patient queue table
    const queueBody = document.getElementById('doc-queue-table-body');
    if (queueBody) {
      if (!data.today_appointments || data.today_appointments.length === 0) {
        queueBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:var(--text-muted);">No clinic appointments scheduled for today.</td></tr>`;
      } else {
        queueBody.innerHTML = data.today_appointments.map(a => `
          <tr>
            <td style="font-weight:700;">
              <div>${a.scheduled_time}</div>
              ${a.queue_position ? `<span style="font-size:0.72rem; color:var(--color-brand-primary);">Queue #${a.queue_position}</span>` : ''}
            </td>
            <td>
              <div style="font-weight:600;">${escapeHtml(a.patient_name)}</div>
              <div style="font-size:0.75rem; color:var(--text-muted);">MRN: ${a.mrn} • Blood: ${a.blood_group || 'N/A'}</div>
              ${a.check_in_time ? `<span style="font-size:0.7rem; color:var(--success);">✓ Arrived ${a.check_in_time}</span>` : `<span style="font-size:0.7rem; color:var(--text-muted);">Not checked in</span>`}
            </td>
            <td><span class="status-badge ${a.consultation_type === 'Video' ? 'badge-in-progress' : 'badge-scheduled'}">${a.consultation_type}</span></td>
            <td>
              <span class="status-badge badge-${a.status}">${a.status}</span>
              ${a.delay_minutes ? `<div style="font-size:0.68rem; color:var(--warning); margin-top:2px;">+${a.delay_minutes}m delay</div>` : ''}
            </td>
            <td style="font-size:0.8rem; max-width:180px; color:var(--text-secondary);" title="${escapeHtml(a.reason_for_visit)}">
              ${escapeHtml(a.reason_for_visit ? a.reason_for_visit.substring(0, 38) + '...' : '-')}
            </td>
            <td style="text-align:right;">
              <div style="display:inline-flex; flex-wrap:wrap; gap:4px; justify-content:flex-end;">
                ${a.status !== 'in_progress' && a.status !== 'completed' ? `
                  <button class="btn btn-teal btn-sm" style="padding:3px 7px; font-size:0.72rem;" onclick="DoctorModule.callInPatient(${a.id})" title="Call in patient and start consultation">
                    Call Next
                  </button>
                  <button class="btn btn-secondary btn-sm" style="padding:3px 7px; font-size:0.72rem;" onclick="DoctorModule.markDelay(${a.id})" title="Notify patient of +10m clinic overrun">
                    +10m Delay
                  </button>
                ` : ''}
                <button class="btn btn-primary btn-sm" style="padding:3px 7px; font-size:0.72rem;" onclick="DoctorModule.openConsultationNotes(${a.id}, '${escapeHtml(a.patient_name)}', '${a.mrn}', '${escapeHtml(a.reason_for_visit)}')">
                  🩺 Notes & Rx
                </button>
                <button class="btn btn-secondary btn-sm" style="padding:3px 7px; font-size:0.72rem;" onclick="DoctorModule.openPatientProfile(${a.patient_id})">
                  Chart
                </button>
                <button class="btn btn-secondary btn-sm" style="padding:3px 7px; font-size:0.72rem;" onclick="DoctorModule.updateStatus(${a.id}, 'completed')">
                  Done
                </button>
                <button class="btn btn-outline-danger btn-sm" style="padding:3px 7px; font-size:0.72rem;" onclick="DoctorModule.updateStatus(${a.id}, 'no_show')">
                  No-Show
                </button>
              </div>
            </td>
          </tr>
        `).join('');
      }
    }
  },

  async callInPatient(apptId) {
    try {
      await api.put(`/appointments/${apptId}/queue-status`, { action: 'start_consult' });
      showToast('Patient called in. Consultation status set to in-progress.', 'success');
      this.loadOverview();
    } catch (err) {
      showToast('Call-in error: ' + err.message, 'error');
    }
  },

  async markDelay(apptId) {
    try {
      await api.put(`/appointments/${apptId}/queue-status`, { action: 'mark_delay', delay_minutes: 10 });
      showToast('Recorded +10m clinic delay. Patient queue wait-times automatically adjusted.', 'warning');
      this.loadOverview();
    } catch (err) {
      showToast('Delay update error: ' + err.message, 'error');
    }
  },

  async toggleAvailability() {
    try {
      const res = await api.put('/doctor/toggle-availability');
      showToast(res.message, 'success');
      this.loadOverview();
    } catch (err) {
      showToast('Toggle failed: ' + err.message, 'error');
    }
  },

  async updateStatus(apptId, newStatus) {
    try {
      await api.put(`/doctor/appointments/${apptId}/status`, { status: newStatus });
      showToast(`Appointment status updated to ${newStatus}.`, 'success');
      this.loadOverview();
    } catch (err) {
      showToast('Status update failed: ' + err.message, 'error');
    }
  },

  async loadAvailabilitySchedule() {
    try {
      const data = await api.get('/doctor/availability');
      const container = document.getElementById('doc-schedule-grid');
      if (!container) return;

      const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      const schedMap = {};
      (data.weekly_schedules || []).forEach(s => {
        schedMap[s.day_of_week] = s;
      });

      container.innerHTML = dayNames.map((name, idx) => {
        const s = schedMap[idx] || { start_time: '09:00', end_time: '17:00', slot_duration_minutes: 30, break_start: '13:00', break_end: '14:00', emergency_slots_enabled: 1, is_active: idx < 5 ? 1 : 0 };
        return `
          <div class="clinical-card" style="margin-bottom:12px; padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <strong style="font-size:0.95rem;">${name}</strong>
              <label style="display:flex; align-items:center; gap:6px; font-size:0.8rem; cursor:pointer;">
                <input type="checkbox" id="sched-active-${idx}" ${s.is_active ? 'checked' : ''}/> Active Clinic Day
              </label>
            </div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; font-size:0.82rem;">
              <div>
                <label>Start Shift</label>
                <input type="time" class="form-control" id="sched-start-${idx}" value="${s.start_time || '09:00'}"/>
              </div>
              <div>
                <label>End Shift</label>
                <input type="time" class="form-control" id="sched-end-${idx}" value="${s.end_time || '17:00'}"/>
              </div>
              <div>
                <label>Slot Duration</label>
                <select class="form-control" id="sched-dur-${idx}">
                  <option value="15" ${s.slot_duration_minutes === 15 ? 'selected' : ''}>15 mins</option>
                  <option value="30" ${s.slot_duration_minutes === 30 ? 'selected' : ''}>30 mins</option>
                  <option value="45" ${s.slot_duration_minutes === 45 ? 'selected' : ''}>45 mins</option>
                  <option value="60" ${s.slot_duration_minutes === 60 ? 'selected' : ''}>60 mins</option>
                </select>
              </div>
              <div>
                <label>Break Start</label>
                <input type="time" class="form-control" id="sched-break-start-${idx}" value="${s.break_start || '13:00'}"/>
              </div>
              <div>
                <label>Break End</label>
                <input type="time" class="form-control" id="sched-break-end-${idx}" value="${s.break_end || '14:00'}"/>
              </div>
            </div>
          </div>
        `;
      }).join('');

      // Leaves and blocks table
      const leavesBody = document.getElementById('doc-leaves-table-body');
      if (leavesBody) {
        if (!data.leaves_and_blocks || data.leaves_and_blocks.length === 0) {
          leavesBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:16px; color:var(--text-muted);">No current leaves or blocked periods recorded.</td></tr>`;
        } else {
          leavesBody.innerHTML = data.leaves_and_blocks.map(l => `
            <tr>
              <td>${l.start_datetime} to ${l.end_datetime}</td>
              <td><span class="status-badge badge-scheduled">${escapeHtml(l.block_type)}</span></td>
              <td>${escapeHtml(l.reason)}</td>
              <td style="text-align:right;">
                <button class="btn btn-outline-danger btn-sm" onclick="DoctorModule.deleteLeave(${l.id})">Remove</button>
              </td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      showToast('Error loading schedule: ' + err.message, 'error');
    }
  },

  async saveAvailabilitySchedule() {
    const schedules = [];
    for (let idx = 0; idx < 7; idx++) {
      const active = document.getElementById(`sched-active-${idx}`)?.checked || false;
      const start = document.getElementById(`sched-start-${idx}`)?.value || '09:00';
      const end = document.getElementById(`sched-end-${idx}`)?.value || '17:00';
      const dur = parseInt(document.getElementById(`sched-dur-${idx}`)?.value || '30');
      const bStart = document.getElementById(`sched-break-start-${idx}`)?.value || '13:00';
      const bEnd = document.getElementById(`sched-break-end-${idx}`)?.value || '14:00';

      schedules.push({
        day_of_week: idx,
        start_time: start,
        end_time: end,
        slot_duration_minutes: dur,
        break_start: bStart,
        break_end: bEnd,
        emergency_slots_enabled: true,
        is_active: active
      });
    }

    try {
      await api.put('/doctor/availability', { schedules });
      showToast('Weekly clinical availability schedule successfully saved.', 'success');
      this.loadAvailabilitySchedule();
    } catch (err) {
      showToast('Failed to save schedule: ' + err.message, 'error');
    }
  },

  openAddLeaveModal() {
    document.getElementById('leave-modal').classList.add('active');
  },

  async submitLeaveBlock() {
    const start = document.getElementById('leave-start-input').value;
    const end = document.getElementById('leave-end-input').value;
    const type = document.getElementById('leave-type-select').value;
    const reason = document.getElementById('leave-reason-input').value.trim();

    if (!start || !end || !reason) {
      showToast('Please fill in start date, end date, and reason.', 'error');
      return;
    }

    try {
      await api.post('/doctor/leaves', {
        start_datetime: start,
        end_datetime: end,
        block_type: type,
        reason: reason
      });
      document.getElementById('leave-modal').classList.remove('active');
      showToast('Leave / Unavailability block recorded.', 'success');
      this.loadAvailabilitySchedule();
    } catch (err) {
      showToast('Failed to record leave: ' + err.message, 'error');
    }
  },

  async deleteLeave(leaveId) {
    try {
      await api.delete(`/doctor/leaves/${leaveId}`);
      showToast('Leave block removed.', 'info');
      this.loadAvailabilitySchedule();
    } catch (err) {
      showToast('Delete failed: ' + err.message, 'error');
    }
  },

  openConsultationNotes(apptId, patientName, mrn, reason) {
    this.activeConsultationApptId = apptId;
    this.prescriptionItems = [];
    this.renderPrescriptionPad();

    document.getElementById('notes-modal-appt-id').value = apptId;
    document.getElementById('notes-patient-badge').textContent = `Patient: ${patientName} (MRN: ${mrn})`;
    document.getElementById('notes-symptoms-input').value = reason || '';
    document.getElementById('notes-clinical-input').value = '';
    document.getElementById('notes-diagnosis-input').value = '';
    document.getElementById('notes-instructions-input').value = '';
    
    const nextMonth = new Date();
    nextMonth.setDate(nextMonth.getDate() + 30);
    document.getElementById('notes-followup-input').value = nextMonth.toISOString().split('T')[0];

    document.getElementById('consultation-notes-modal').classList.add('active');
  },

  addPrescriptionItem() {
    const drug = document.getElementById('rx-drug-name')?.value?.trim() || '';
    const dosage = document.getElementById('rx-dosage')?.value?.trim() || '';
    const freq = document.getElementById('rx-frequency')?.value?.trim() || '';
    const dur = document.getElementById('rx-duration')?.value?.trim() || '';
    const instr = document.getElementById('rx-instructions')?.value?.trim() || '';

    if (!drug || !dosage) {
      showToast('Please specify at least drug name and dosage.', 'error');
      return;
    }

    this.prescriptionItems.push({
      medication_name: drug,
      dosage: dosage,
      frequency: freq || 'Once daily',
      duration: dur || '14 days',
      instructions: instr || 'Take with water after food'
    });

    // Clear inputs
    const drugEl = document.getElementById('rx-drug-name');
    if (drugEl) drugEl.value = '';
    const dosageEl = document.getElementById('rx-dosage');
    if (dosageEl) dosageEl.value = '';
    const instrEl = document.getElementById('rx-instructions');
    if (instrEl) instrEl.value = '';

    this.renderPrescriptionPad();
  },

  removePrescriptionItem(idx) {
    this.prescriptionItems.splice(idx, 1);
    this.renderPrescriptionPad();
  },

  renderPrescriptionPad() {
    const container = document.getElementById('rx-items-list');
    if (!container) return;

    if (this.prescriptionItems.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted); font-size:0.8rem; font-style:italic;">No medications added yet.</p>';
      return;
    }

    container.innerHTML = this.prescriptionItems.map((item, idx) => `
      <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-surface-alt); padding:8px 12px; border-radius:var(--radius-sm); margin-bottom:6px; font-size:0.82rem;">
        <div>
          <strong>${escapeHtml(item.medication_name)}</strong> (${escapeHtml(item.dosage)}) — ${escapeHtml(item.frequency)} for ${escapeHtml(item.duration)}
          <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(item.instructions || '')}</div>
        </div>
        <button type="button" class="btn btn-outline-danger btn-sm" onclick="DoctorModule.removePrescriptionItem(${idx})">✕</button>
      </div>
    `).join('');
  },

  async submitConsultationNotes() {
    const apptId = this.activeConsultationApptId;
    const symptoms = document.getElementById('notes-symptoms-input').value.trim();
    const notes = document.getElementById('notes-clinical-input').value.trim();
    const diagnosis = document.getElementById('notes-diagnosis-input').value.trim();
    const followup = document.getElementById('notes-followup-input').value;
    const instructions = document.getElementById('notes-instructions-input').value.trim();

    if (!diagnosis || !notes) {
      showToast('Clinical diagnosis and clinical examination notes are mandatory.', 'error');
      return;
    }

    try {
      await api.post('/doctor/consultation-notes', {
        appointment_id: parseInt(apptId),
        symptoms: symptoms || 'Consultation review',
        clinical_notes: notes,
        diagnosis: diagnosis,
        follow_up_date: followup || null,
        instructions: instructions || 'Follow healthy lifestyle guidelines.',
        prescriptions: this.prescriptionItems
      });

      document.getElementById('consultation-notes-modal').classList.remove('active');
      showToast('Consultation notes, diagnosis, and prescriptions signed successfully.', 'success');
      this.loadOverview();
    } catch (err) {
      showToast('Failed to save consultation: ' + err.message, 'error');
    }
  },

  async openPatientProfile(patientId) {
    try {
      const data = await api.get(`/doctor/patient-profile/${patientId}`);
      const p = data.patient;
      const modal = document.getElementById('generic-detail-modal');
      document.getElementById('generic-detail-modal-title').textContent = `Clinical Patient Chart: ${p.full_name} (${p.mrn})`;
      
      const body = document.getElementById('generic-detail-modal-body');
      
      let recordsList = (data.medical_records || []).map(r => `
        <div style="padding:10px; border-bottom:1px solid var(--border-subtle); font-size:0.82rem;">
          <div style="font-weight:700;">${escapeHtml(r.title)} <span style="font-weight:400; color:var(--text-muted);">(${r.record_date})</span></div>
          <div style="color:var(--text-secondary); margin-top:2px;">${escapeHtml(r.description)}</div>
        </div>
      `).join('') || '<p style="color:var(--text-muted); font-size:0.82rem;">No prior records.</p>';

      let reportsList = (data.health_reports || []).map(rep => `
        <div style="padding:8px 0; border-bottom:1px solid var(--border-subtle); font-size:0.82rem;">
          <strong>${escapeHtml(rep.title)}</strong> (${rep.report_date})
          <div style="color:var(--text-muted); font-size:0.75rem;">${escapeHtml(rep.summary || rep.hospital_facility)}</div>
        </div>
      `).join('') || '<p style="color:var(--text-muted); font-size:0.82rem;">No uploaded lab reports.</p>';

      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px; background:var(--bg-surface-alt); padding:12px; border-radius:var(--radius-md); font-size:0.82rem;">
            <div><strong>DOB:</strong> ${p.date_of_birth || 'N/A'}</div>
            <div><strong>Gender:</strong> ${p.gender || 'N/A'}</div>
            <div><strong>Blood Group:</strong> ${p.blood_group || 'N/A'}</div>
            <div><strong>Emergency:</strong> ${p.emergency_contact || 'N/A'}</div>
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
            <div style="background:#fee2e2; border:1px solid #fca5a5; padding:10px; border-radius:var(--radius-sm); font-size:0.82rem;">
              <strong style="color:#991b1b;">⚠️ Known Allergies:</strong>
              <div style="color:#7f1d1d; margin-top:4px;">${escapeHtml(p.allergies || 'None documented')}</div>
            </div>
            <div style="background:#fef3c7; border:1px solid #fde68a; padding:10px; border-radius:var(--radius-sm); font-size:0.82rem;">
              <strong style="color:#92400e;">Chronic Conditions:</strong>
              <div style="color:#78350f; margin-top:4px;">${escapeHtml(p.chronic_conditions || 'None documented')}</div>
            </div>
          </div>

          <div>
            <h4 style="font-size:0.92rem; margin-bottom:6px;">Diagnostic Reports</h4>
            <div style="max-height:140px; overflow-y:auto;">${reportsList}</div>
          </div>

          <div>
            <h4 style="font-size:0.92rem; margin-bottom:6px;">Historical Diagnoses & Clinical Notes</h4>
            <div style="max-height:160px; overflow-y:auto;">${recordsList}</div>
          </div>
        </div>
      `;

      modal.classList.add('active');
    } catch (err) {
      showToast('Error fetching patient chart: ' + err.message, 'error');
    }
  },

  async loadWorkloadMetrics() {
    try {
      const data = await api.get('/doctor/workload-metrics');
      document.getElementById('doc-metric-total').textContent = data.total_appointments_all_time;
      document.getElementById('doc-metric-utilization').textContent = `${data.utilization_percentage}%`;
      document.getElementById('doc-metric-noshow').textContent = `${data.no_show_rate_percent}%`;
      document.getElementById('doc-metric-peak').textContent = data.peak_consultation_hour;
    } catch (err) {
      showToast('Metrics error: ' + err.message, 'error');
    }
  },

  /* 2. Doctor Appointments */
  async loadAppointments(statusFilter = 'all') {
    const tbody = document.getElementById('doc-all-appts-body');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">Loading appointments ledger...</td></tr>';
    try {
      const data = await api.get('/doctor/overview');
      let appts = data.today_appointments || [];
      if (statusFilter !== 'all') {
        appts = appts.filter(a => a.status === statusFilter);
      }
      if (appts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:24px; color:var(--text-muted);">No appointments recorded in this category.</td></tr>';
        return;
      }
      tbody.innerHTML = appts.map(a => `
        <tr>
          <td>
            <strong>${a.scheduled_time}</strong>
            <div style="font-size:0.75rem; color:var(--text-muted);">${a.scheduled_date} • #${a.appointment_number || a.id}</div>
          </td>
          <td>
            <strong>${escapeHtml(a.patient_name)}</strong>
            <div style="font-size:0.75rem; color:var(--text-muted);">MRN: ${a.mrn || 'AC-MRN-90412'}</div>
          </td>
          <td><span class="status-badge ${a.consultation_type === 'Video' ? 'badge-in-progress' : 'badge-scheduled'}">${a.consultation_type}</span></td>
          <td><span class="status-badge badge-${a.status}">${a.status}</span></td>
          <td style="font-size:0.82rem; color:var(--text-secondary); max-width:200px;">${escapeHtml(a.reason_for_visit || 'Routine OPD')}</td>
          <td style="text-align:right;">
            <button class="btn btn-secondary btn-sm" onclick="DoctorModule.openPatientProfile(${a.patient_id})">Chart</button>
            <button class="btn btn-primary btn-sm" onclick="DoctorModule.openConsultationNotes(${a.id}, '${escapeHtml(a.patient_name)}', '${a.mrn}', '${escapeHtml(a.reason_for_visit)}')">Notes</button>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--danger); padding:20px;">Failed to load: ${err.message}</td></tr>`;
    }
  },

  /* 3. Today's Schedule */
  async loadSchedule() {
    const container = document.getElementById('doc-schedule-timeline-container');
    if (!container) return;
    const slots = [
      { time: '09:00 AM', status: 'completed', patient: 'Ramesh Kumar (Routine Follow-up)' },
      { time: '09:30 AM', status: 'completed', patient: 'Deepa Venkat (Echo Review)' },
      { time: '10:00 AM', status: 'in_progress', patient: 'Arjun Sharma (Chest Discomfort)' },
      { time: '10:30 AM', status: 'scheduled', patient: 'Arunachalam S (BP Check)' },
      { time: '11:00 AM', status: 'scheduled', patient: 'Meenakshi Sundaram (Post-op)' },
      { time: '11:30 AM', status: 'available', patient: 'Open OPD Slot' },
      { time: '12:00 PM', status: 'available', patient: 'Open OPD Slot' },
      { time: '02:00 PM', status: 'scheduled', patient: 'Karthik Raja (ECG Evaluation)' },
      { time: '02:30 PM', status: 'scheduled', patient: 'Anandhi R (Holter Results)' },
      { time: '03:00 PM', status: 'available', patient: 'Open OPD Slot' }
    ];
    container.innerHTML = slots.map(s => `
      <div style="background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:14px; border-left:4px solid ${s.status === 'completed' ? 'var(--success)' : (s.status === 'in_progress' ? 'var(--color-brand-teal)' : (s.status === 'available' ? 'var(--border-medium)' : 'var(--color-brand-primary)'))};">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <strong style="font-size:0.92rem;">${s.time}</strong>
          <span class="status-badge badge-${s.status}">${s.status.toUpperCase()}</span>
        </div>
        <div style="font-size:0.8rem; color:var(--text-secondary);">${escapeHtml(s.patient)}</div>
      </div>
    `).join('');
  },

  /* 4. Consultation Calendar */
  loadCalendar() {
    const grid = document.getElementById('doc-calendar-grid');
    if (!grid) return;
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    let html = days.map(d => `<div style="font-weight:700; font-size:0.8rem; padding:8px 0; color:var(--text-muted);">${d}</div>`).join('');
    for (let day = 1; day <= 30; day++) {
      const isWeekend = (day % 7 === 0);
      const isPast = day < 11;
      const isToday = day === 11;
      html += `
        <div style="border:1px solid var(--border-subtle); border-radius:var(--radius-sm); padding:10px 4px; min-height:64px; background:${isToday ? '#f0fdfa' : (isWeekend ? '#f8fafc' : 'var(--bg-surface)')}; border-color:${isToday ? 'var(--color-brand-teal)' : 'var(--border-subtle)'};">
          <div style="font-weight:${isToday ? '800' : '600'}; font-size:0.85rem; color:${isToday ? 'var(--color-brand-teal)' : 'inherit'};">${day}</div>
          <div style="font-size:0.68rem; color:${isWeekend ? 'var(--text-muted)' : '#0284c7'}; margin-top:4px;">
            ${isWeekend ? 'Clinic Off' : (isPast ? '18 Seen' : (isToday ? '14 Scheduled' : '10 Booked'))}
          </div>
        </div>
      `;
    }
    grid.innerHTML = html;
  },

  /* 5. Patients Directory */
  cachedPatients: [
    { id: 1, name: 'Arjun Sharma', mrn: 'CA-MRN-48912', city: 'Chennai', phone: '+91 98401 55210', blood: 'O+', allergies: 'Penicillin' },
    { id: 2, name: 'Suresh Kumar', mrn: 'AC-MRN-88219', city: 'Mumbai', phone: '+91 98201 54321', blood: 'B+', allergies: 'Sulfa' },
    { id: 3, name: 'Ananya Deshmukh', mrn: 'AC-MRN-77312', city: 'Pune', phone: '+91 97601 88888', blood: 'A+', allergies: 'None' },
    { id: 4, name: 'Karthik Swaminathan', mrn: 'AC-MRN-66120', city: 'Bengaluru', phone: '+91 99401 12345', blood: 'AB+', allergies: 'Aspirin' },
    { id: 5, name: 'Lakshmi Narayanan', mrn: 'AC-MRN-55419', city: 'Hyderabad', phone: '+91 98480 98765', blood: 'O-', allergies: 'None' }
  ],

  loadPatients() {
    this.renderPatientsList(this.cachedPatients);
  },

  filterPatients(term) {
    const q = (term || '').toLowerCase();
    const filtered = this.cachedPatients.filter(p => p.name.toLowerCase().includes(q) || p.mrn.toLowerCase().includes(q));
    this.renderPatientsList(filtered);
  },

  renderPatientsList(patients) {
    const tbody = document.getElementById('doc-patients-list-body');
    if (!tbody) return;
    tbody.innerHTML = patients.map(p => `
      <tr>
        <td><strong>${escapeHtml(p.name)}</strong></td>
        <td><span class="status-badge" style="background:#eff6ff; color:#1d4ed8;">${p.mrn}</span></td>
        <td>${escapeHtml(p.city)} • ${p.phone}</td>
        <td><span style="font-weight:700; color:var(--danger);">${p.blood}</span></td>
        <td><span class="doc-chip" style="background:#fee2e2; color:#991b1b;">⚠️ ${escapeHtml(p.allergies)}</span></td>
        <td style="text-align:right;">
          <button class="btn btn-secondary btn-sm" onclick="DoctorModule.openPatientProfile(${p.id})">Open Chart</button>
        </td>
      </tr>
    `).join('');
  },

  /* 6. Patient Records & History */
  loadPatientHistory() {
    const container = document.getElementById('doc-patient-history-viewer');
    if (!container) return;
    container.innerHTML = `
      <div style="background:var(--bg-surface-alt); padding:16px; border-radius:var(--radius-md); font-size:0.85rem;">
        <div style="font-weight:700; margin-bottom:8px;">Active Patient: Arjun Sharma (CA-MRN-48912)</div>
        <p style="color:var(--text-secondary); margin-bottom:10px;">Primary Diagnosis: Essential Hypertension (ICD-10 I10) with mild exertional dyspnea.</p>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-teal btn-sm" onclick="DoctorModule.openPatientProfile(1)">View Full EMR Record</button>
        </div>
      </div>
    `;
  },

  /* 7. Diagnostic Reports */
  loadReports() {
    const tbody = document.getElementById('doc-reports-table-body');
    if (!tbody) return;
    const reports = [
      { title: '12-Lead Electrocardiogram (ECG)', type: 'Diagnostic ECG', patient: 'Arjun Sharma (CA-MRN-48912)', facility: 'CareAura Apollo Chennai', date: '2026-03-02' },
      { title: 'Comprehensive Metabolic Panel (CMP)', type: 'Pathology', patient: 'Arjun Sharma (CA-MRN-48912)', facility: 'CareAura Apollo Chennai', date: '2026-03-01' },
      { title: 'Transthoracic 2D Echo with Doppler', type: 'Echocardiogram', patient: 'Arjun Sharma (CA-MRN-48912)', facility: 'CareAura Apollo Chennai', date: '2026-02-15' },
      { title: 'Lipid Profile Panel', type: 'Clinical Biochemistry', patient: 'Suresh Kumar (AC-MRN-88219)', facility: 'CareSync Andheri', date: '2026-02-20' }
    ];
    tbody.innerHTML = reports.map(r => `
      <tr>
        <td><strong>${escapeHtml(r.title)}</strong></td>
        <td><span class="doc-chip">${escapeHtml(r.type)}</span></td>
        <td>${escapeHtml(r.patient)}</td>
        <td>${escapeHtml(r.facility)}</td>
        <td>${r.date}</td>
        <td style="text-align:right;"><button class="btn btn-secondary btn-sm" onclick="showToast('Viewing verified hospital laboratory document...', 'info')">Review PDF</button></td>
      </tr>
    `).join('');
  },

  /* 8. Consultation Notes Archive */
  loadNotes() {
    const container = document.getElementById('doc-notes-archive-container');
    if (!container) return;
    container.innerHTML = `
      <div style="border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:16px; margin-bottom:12px; background:var(--bg-surface);">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
          <strong style="font-size:0.95rem;">Arjun Sharma (CA-MRN-48912)</strong>
          <span style="font-size:0.75rem; color:var(--text-muted);">2026-03-02 • OPD Routine</span>
        </div>
        <p style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:6px;"><strong>Assessment:</strong> Patient presented with borderline elevated systolic readings (142/88 mmHg). Recommended dietary sodium reduction and prescribed Telmisartan 40mg once daily.</p>
        <span class="status-badge badge-completed">Finalized & Digitally Signed</span>
      </div>
    `;
  },

  /* 9. Prescriptions */
  loadPrescriptions() {
    const tbody = document.getElementById('doc-prescriptions-table-body');
    if (!tbody) return;
    const rxs = [
      { date: '2026-03-02', patient: 'Arjun Sharma (CA-MRN-48912)', meds: 'Telmisartan 40mg (1-0-0), Atorvastatin 10mg (0-0-1)', instructions: 'Take with warm water after morning meal. Review in 30 days.' },
      { date: '2026-02-15', patient: 'Arjun Sharma (CA-MRN-48912)', meds: 'Amlodipine 5mg (1-0-0)', instructions: 'Monitor BP daily. Discontinued due to mild ankle edema.' }
    ];
    tbody.innerHTML = rxs.map(rx => `
      <tr>
        <td><strong>${rx.date}</strong></td>
        <td>${escapeHtml(rx.patient)}</td>
        <td style="color:var(--color-brand-primary); font-weight:600;">${escapeHtml(rx.meds)}</td>
        <td style="font-size:0.82rem; color:var(--text-secondary);">${escapeHtml(rx.instructions)}</td>
        <td style="text-align:right;"><button class="btn btn-secondary btn-sm" onclick="showToast('Printing authenticated prescription with Indian NMC digital sign...', 'info')">Print Rx</button></td>
      </tr>
    `).join('');
  },

  /* 11. Leave Management */
  submitLeaveRequest() {
    const type = document.getElementById('doc-leave-type')?.value;
    const start = document.getElementById('doc-leave-start')?.value;
    const end = document.getElementById('doc-leave-end')?.value;
    const reason = document.getElementById('doc-leave-reason')?.value.trim();

    if (!start || !end) {
      showToast('Please specify leave start and end dates.', 'error');
      return;
    }

    const container = document.getElementById('doc-leave-history-list');
    if (container) {
      container.innerHTML = `
        <div style="border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:14px; margin-bottom:8px; background:var(--bg-surface);">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <strong>${escapeHtml(type)}</strong>
            <span class="status-badge badge-confirmed">Approved by CMO</span>
          </div>
          <div style="font-size:0.8rem; color:var(--text-muted);">${start} to ${end}</div>
          <p style="font-size:0.82rem; color:var(--text-secondary); margin-top:4px;">${escapeHtml(reason || 'Planned clinic leave')}</p>
        </div>
      `;
    }
    showToast('Leave request recorded and submitted to Hospital Administration.', 'success');
  },

  loadLeaveManagement() {
    // Ready
  },

  /* 12. Waiting Room Queue */
  async loadQueue() {
    const container = document.getElementById('doc-queue-expanded-container');
    if (!container) return;
    try {
      const data = await api.get('/doctor/overview');
      const appts = (data.today_appointments || []).filter(a => a.status === 'scheduled' || a.status === 'in_progress');
      if (appts.length === 0) {
        container.innerHTML = '<p style="padding:24px; text-align:center; color:var(--text-muted);">Waiting room is currently clear. No patients waiting.</p>';
        return;
      }
      container.innerHTML = appts.map((a, idx) => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:16px; border:1px solid var(--border-subtle); border-radius:var(--radius-md); margin-bottom:12px; background:var(--bg-surface);">
          <div style="display:flex; align-items:center; gap:16px;">
            <div style="font-size:1.4rem; font-weight:800; color:var(--color-brand-primary);">#${idx + 1}</div>
            <div>
              <div style="font-weight:700; font-size:1rem;">${escapeHtml(a.patient_name)}</div>
              <div style="font-size:0.78rem; color:var(--text-muted);">MRN: ${a.mrn} • Time: ${a.scheduled_time}</div>
              <div style="font-size:0.82rem; color:var(--text-secondary); margin-top:2px;">Reason: ${escapeHtml(a.reason_for_visit || 'OPD consultation')}</div>
            </div>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn btn-teal btn-sm" onclick="DoctorModule.callInPatient(${a.id})">Call In</button>
            <button class="btn btn-secondary btn-sm" onclick="DoctorModule.markDelay(${a.id})">+10m Delay</button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<p style="color:var(--danger); padding:16px;">Queue load error: ${err.message}</p>`;
    }
  },

  /* 13. Notifications */
  loadNotifications() {
    const container = document.getElementById('doc-notifications-list');
    if (!container) return;
    container.innerHTML = `
      <div style="border-left:4px solid var(--color-brand-teal); background:var(--bg-surface); padding:14px; border-radius:var(--radius-sm); margin-bottom:10px;">
        <strong>⚡ Standby Slot Auto-Filled</strong>
        <p style="font-size:0.82rem; color:var(--text-secondary); margin-top:4px;">Patient standby waitlist engine automatically allocated 11:00 AM slot to Arjun Sharma following a cancellation.</p>
        <span style="font-size:0.7rem; color:var(--text-muted);">Today at 08:15 IST</span>
      </div>
      <div style="border-left:4px solid var(--color-brand-primary); background:var(--bg-surface); padding:14px; border-radius:var(--radius-sm); margin-bottom:10px;">
        <strong>📢 Hospital Protocol Update: Digital EMR Compliance</strong>
        <p style="font-size:0.82rem; color:var(--text-secondary); margin-top:4px;">All outpatient consultation notes must include ICD-10 diagnostic codes as per National Medical Commission (NMC) guidelines.</p>
        <span style="font-size:0.7rem; color:var(--text-muted);">Yesterday</span>
      </div>
    `;
  },

  /* 16. Clinic Settings */
  saveSettings() {
    const fee = document.getElementById('doc-setting-fee')?.value;
    const dur = document.getElementById('doc-setting-duration')?.value;
    const langs = document.getElementById('doc-setting-langs')?.value;
    showToast(`Saved clinic settings: ₹${fee} fee, ${dur}m duration, Languages: ${langs}`, 'success');
  },

  loadSettings() {
    // Initialized
  }
};


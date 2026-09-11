// AI Hospital Assistant Chatbot Module
const ChatbotModule = {
  currentConversationId: null,

  toggleDrawer() {
    const drawer = document.getElementById('chat-drawer');
    drawer.classList.toggle('open');
    if (drawer.classList.contains('open')) {
      this.loadConversations();
    }
  },

  async loadConversations(searchQuery = '') {
    try {
      const convs = await api.get('/chatbot/conversations', { query: searchQuery });
      const listEl = document.getElementById('chat-conv-list');
      if (!listEl) return;

      if (!convs || convs.length === 0) {
        listEl.innerHTML = `<div style="padding:10px; font-size:0.75rem; color:var(--text-muted); text-align:center;">No previous conversations found.</div>`;
        return;
      }

      listEl.innerHTML = convs.map(c => `
        <div class="chat-conv-item ${c.id === this.currentConversationId ? 'active' : ''}" onclick="ChatbotModule.openConversation(${c.id})">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:600; font-size:0.78rem; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:180px;">
              💬 ${escapeHtml(c.title)}
            </span>
            <span style="font-size:0.68rem; color:var(--text-muted);">${c.updated_at ? c.updated_at.split('T')[0] : ''}</span>
          </div>
          <div style="font-size:0.72rem; color:var(--text-muted); text-overflow:ellipsis; overflow:hidden; white-space:nowrap; margin-top:2px;">
            ${escapeHtml(c.last_message || 'No messages')}
          </div>
          <div style="display:flex; justify-content:flex-end; gap:6px; margin-top:4px;">
            <button class="btn btn-secondary btn-sm" style="padding:2px 6px; font-size:0.65rem;" onclick="event.stopPropagation(); ChatbotModule.promptRename(${c.id}, '${escapeHtml(c.title)}')">Rename</button>
            <button class="btn btn-outline-danger btn-sm" style="padding:2px 6px; font-size:0.65rem;" onclick="event.stopPropagation(); ChatbotModule.deleteConversation(${c.id})">Delete</button>
          </div>
        </div>
      `).join('');

      if (!this.currentConversationId && convs.length > 0) {
        this.openConversation(convs[0].id);
      }
    } catch (err) {
      console.error('Chatbot conversation load error:', err);
    }
  },

  async createNewConversation() {
    try {
      const res = await api.post('/chatbot/conversations', { title: 'New Hospital Inquiry' });
      this.currentConversationId = res.conversation_id;
      this.loadConversations();
      this.openConversation(res.conversation_id);
    } catch (err) {
      showToast('Could not start new chat: ' + err.message, 'error');
    }
  },

  async openConversation(convId) {
    this.currentConversationId = convId;
    try {
      const data = await api.get(`/chatbot/conversations/${convId}`);
      document.getElementById('chat-active-title').textContent = data.conversation.title;
      this.renderMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to open conversation:', err);
    }
  },

  renderCardHtml(cardType, cards) {
    if (!cards || cards.length === 0) return '';
    let cardsHtml = '';

    if (cardType === 'doctor_card') {
      cardsHtml = cards.map(c => `
        <div class="chat-card">
          <div style="display:flex; gap:10px; align-items:center; margin-bottom:6px;">
            <img src="${c.avatar_url || getInitialsAvatar(c.name, c.id)}" onerror="this.onerror=null; this.src=getInitialsAvatar('${escapeHtml(c.name)}', ${c.id});" style="width:40px; height:40px; border-radius:50%; object-fit:cover; border:2px solid #e0f2fe; flex-shrink:0;" alt="${escapeHtml(c.name)}"/>
            <div style="flex:1; min-width:0;">
              <div class="chat-card-title">${escapeHtml(c.name)}</div>
              <div class="chat-card-sub">${escapeHtml(c.department)} • ${escapeHtml(c.specialization)}</div>
            </div>
            <span class="status-badge badge-confirmed" style="white-space:nowrap;">₹${c.consultation_fee}</span>
          </div>
          <div class="chat-card-meta">
            <span class="doc-chip">🏥 ${escapeHtml(c.hospital)}</span>
            <span class="doc-chip">📍 ${escapeHtml(c.city)}</span>
            <span class="doc-chip">🗣️ ${escapeHtml(c.languages)}</span>
            <span class="doc-chip">⏱️ ${c.experience_years} yrs exp</span>
            <span class="doc-chip" style="color:var(--color-brand-teal);">🗓️ Next: ${c.next_available}</span>
          </div>
          <div class="chat-card-actions">
            <button class="btn btn-teal btn-sm" style="font-size:0.75rem; padding:4px 10px;" onclick="PatientModule.selectDoctorForBooking(${c.id}, '${escapeHtml(c.name)}', '${escapeHtml(c.department)}')">
              Book Slot (₹${c.consultation_fee})
            </button>
          </div>
        </div>
      `).join('');
    } else if (cardType === 'hospital_card') {
      cardsHtml = cards.map(c => `
        <div class="chat-card">
          <div style="display:flex; gap:10px; align-items:center; margin-bottom:6px;">
            <img src="${c.image_url || 'https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=600'}" style="width:44px; height:44px; border-radius:8px; object-fit:cover; flex-shrink:0;" alt="${escapeHtml(c.name)}"/>
            <div style="flex:1; min-width:0;">
              <div class="chat-card-title">${escapeHtml(c.name)}</div>
              <div class="chat-card-sub">📍 ${escapeHtml(c.locality || '')}, ${escapeHtml(c.city || '')}</div>
            </div>
            <span class="hosp-rating">★ ${c.rating || '4.8'}</span>
          </div>
          <div class="chat-card-meta">
            ${c.emergency_24x7 ? '<span class="doc-chip" style="background:#fee2e2; color:#991b1b; font-weight:700;">🚨 24x7 Emergency</span>' : ''}
            <span class="doc-chip">🛏️ ${c.bed_capacity || 200} Beds</span>
            <span class="doc-chip">Starting: ₹${c.base_fee || c.consultation_starting_fee || 500}</span>
            <span class="doc-chip">🕒 24x7 OPD</span>
          </div>
          <div class="chat-card-actions">
            <button class="btn btn-primary btn-sm" style="font-size:0.75rem; padding:4px 8px;" onclick="PatientModule.openHospitalModal(${c.id})">
              View Hospital
            </button>
            <button class="btn btn-teal btn-sm" style="font-size:0.75rem; padding:4px 8px;" onclick="PatientModule.openBookingModalForHospital(${c.id}, '${escapeHtml(c.name)}')">
              Book Appointment
            </button>
          </div>
        </div>
      `).join('');
    } else if (cardType === 'appointment_card') {
      cardsHtml = cards.map(c => `
        <div class="chat-card">
          <div class="chat-card-header">
            <div class="chat-card-title">Appointment #${c.appointment_number}</div>
            <span class="status-badge badge-${(c.status || 'scheduled').toLowerCase()}">${c.status}</span>
          </div>
          <div class="chat-card-sub">Doctor: <strong>${escapeHtml(c.doctor_name)}</strong> (${escapeHtml(c.department_name)})</div>
          <div class="chat-card-meta">
            <span class="doc-chip">🗓️ ${c.scheduled_date} at ${c.scheduled_time}</span>
            <span class="doc-chip">📍 ${escapeHtml(c.room_number || 'Main Clinic')}</span>
            <span class="doc-chip">${c.consultation_type}</span>
          </div>
          <div class="chat-card-actions">
            <button class="btn btn-secondary btn-sm" style="font-size:0.75rem; padding:4px 8px;" onclick="PatientModule.openRescheduleModal(${c.id}, '${c.scheduled_date}', '${c.scheduled_time}')">
              Reschedule
            </button>
            <button class="btn btn-outline-danger btn-sm" style="font-size:0.75rem; padding:4px 8px;" onclick="PatientModule.openCancelModal(${c.id})">
              Cancel
            </button>
          </div>
        </div>
      `).join('');
    }

    return `<div class="chat-card-wrap">${cardsHtml}</div>`;
  },

  renderMessages(messages) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    if (messages.length === 0) {
      container.innerHTML = `
        <div class="chat-bubble assistant">
          👋 Hello! I am your <strong>CareSync Clinical Assistant</strong>. How can I assist you with Indian hospital services, finding doctors, or managing appointments today?
        </div>
      `;
      return;
    }

    container.innerHTML = messages.map(m => {
      const isUser = m.sender_role === 'user';
      // Format simple markdown into clean HTML
      let formatted = escapeHtml(m.message_text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\n/g, '<br/>');

      let cardHtml = '';
      if (!isUser && (m.cards || m.metadata_json)) {
        let cList = m.cards || [];
        let cType = m.card_type;
        if ((!cList || cList.length === 0) && m.metadata_json) {
          try {
            const parsed = JSON.parse(m.metadata_json);
            cList = parsed.cards || [];
            cType = parsed.card_type;
          } catch (e) {}
        }
        cardHtml = this.renderCardHtml(cType, cList);
      }

      return `
        <div class="chat-bubble ${isUser ? 'user' : 'assistant'}">
          ${formatted}
          ${cardHtml}
          <div style="font-size:0.65rem; color:${isUser ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)'}; margin-top:6px; text-align:right;">
            ${m.timestamp ? m.timestamp.split('T')[1].substring(0, 5) : ''}
          </div>
        </div>
      `;
    }).join('');

    container.scrollTop = container.scrollHeight;
  },

  async sendMessage() {
    const input = document.getElementById('chat-input-field');
    const text = input.value.trim();
    if (!text) return;

    if (!this.currentConversationId) {
      await this.createNewConversation();
    }

    input.value = '';

    const container = document.getElementById('chat-messages-container');
    // Clear any previous error bubbles
    container.querySelectorAll('.chat-error-bubble').forEach(el => el.remove());

    // Append user message immediately
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.innerHTML = `${escapeHtml(text)}<div style="font-size:0.65rem; color:rgba(255,255,255,0.7); margin-top:4px; text-align:right;">Just now</div>`;
    container.appendChild(userBubble);

    // Typing indicator
    const typingBubble = document.createElement('div');
    typingBubble.className = 'chat-bubble assistant';
    typingBubble.id = 'chat-typing-indicator';
    typingBubble.innerHTML = 'Searching CareSync clinical directory...';
    container.appendChild(typingBubble);
    container.scrollTop = container.scrollHeight;

    try {
      const res = await api.post(`/chatbot/conversations/${this.currentConversationId}/messages`, { message: text });
      typingBubble.remove();
      
      const asstBubble = document.createElement('div');
      asstBubble.className = 'chat-bubble assistant';
      let formatted = escapeHtml(res.message.message_text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br/><br/>')
        .replace(/\n/g, '<br/>');

      let cardHtml = '';
      if (res.message.cards && res.message.cards.length > 0) {
        cardHtml = this.renderCardHtml(res.message.card_type, res.message.cards);
      } else if (res.message.metadata_json) {
        try {
          const parsed = JSON.parse(res.message.metadata_json);
          cardHtml = this.renderCardHtml(parsed.card_type, parsed.cards);
        } catch (e) {}
      }

      asstBubble.innerHTML = `${formatted}${cardHtml}<div style="font-size:0.65rem; color:var(--text-muted); margin-top:6px; text-align:right;">Just now</div>`;
      container.appendChild(asstBubble);
      container.scrollTop = container.scrollHeight;
      
      // Update sidebar conversation snippet
      this.loadConversations();
    } catch (err) {
      typingBubble.className = 'chat-bubble assistant chat-error-bubble';
      typingBubble.innerHTML = `
        <div style="color:var(--danger); font-size:0.85rem;">
          <p style="margin-bottom:6px; font-weight:600;">⚠️ Query error: ${escapeHtml(err.message)}</p>
          <button class="btn btn-secondary btn-sm" onclick="ChatbotModule.retryLastMessage('${escapeHtml(text)}')">↻ Retry Query</button>
        </div>
      `;
    }
  },

  retryLastMessage(text) {
    const input = document.getElementById('chat-input-field');
    if (input) input.value = text;
    this.sendMessage();
  },

  async clearConversation() {
    if (this.currentConversationId) {
      try {
        await api.delete(`/chatbot/conversations/${this.currentConversationId}`);
      } catch (e) {}
      this.currentConversationId = null;
    }
    await this.createNewConversation();
    showToast('Conversation cleared.', 'info');
  },

  async promptRename(convId, currTitle) {
    const newTitle = prompt('Enter new conversation title:', currTitle);
    if (newTitle && newTitle.trim()) {
      try {
        await api.put(`/chatbot/conversations/${convId}/rename`, { title: newTitle.trim() });
        this.loadConversations();
        if (convId === this.currentConversationId) {
          document.getElementById('chat-active-title').textContent = newTitle.trim();
        }
      } catch (err) {
        showToast('Rename failed: ' + err.message, 'error');
      }
    }
  },

  async deleteConversation(convId) {
    if (!confirm('Are you sure you want to delete this chat thread?')) return;
    try {
      await api.delete(`/chatbot/conversations/${convId}`);
      if (this.currentConversationId === convId) {
        this.currentConversationId = null;
      }
      this.loadConversations();
      showToast('Conversation deleted.', 'info');
    } catch (err) {
      showToast('Delete failed: ' + err.message, 'error');
    }
  },

  sendQuickPrompt(text) {
    const input = document.getElementById('chat-input-field');
    input.value = text;
    this.sendMessage();
  }
};

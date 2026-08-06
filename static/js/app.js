/* ═══════════════════════════════════════════════════════════════
   Мир Самозанятых v5.0 — Frontend Application
   Modules: API, WebSocket, Push, PWA, Theme, Voice, DragDrop, Toast
   ═══════════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  /* ═══════════════════════════════════════════════════════════════
     1. CONFIG
     ═══════════════════════════════════════════════════════════════ */
  const CONFIG = {
    API_BASE: window.location.origin,
    WS_URL: (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws',
    PUSH_PUBLIC_KEY: 'BEl62i...', // VAPID public key
    THEME_KEY: 'ms_theme',
    TOKEN_KEY: 'ms_access_token',
    REFRESH_KEY: 'ms_refresh_token',
    LOCALE: 'ru-RU',
  };

  /* ═══════════════════════════════════════════════════════════════
     2. API CLIENT
     ═══════════════════════════════════════════════════════════════ */
  const API = {
    async request(endpoint, options = {}) {
      const url = CONFIG.API_BASE + endpoint;
      const token = localStorage.getItem(CONFIG.TOKEN_KEY);
      const defaults = {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(token ? { 'Authorization': 'Bearer ' + token } : {}),
          ...(options.headers || {}),
        },
      };
      const response = await fetch(url, { ...defaults, ...options, headers: { ...defaults.headers, ...(options.headers || {}) } });

      if (response.status === 401) {
        const refreshed = await this.refreshToken();
        if (refreshed) return this.request(endpoint, options);
        Auth.logout();
        throw new Error('Сессия истекла. Пожалуйста, войдите снова.');
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      if (response.status === 204) return null;
      return response.json();
    },

    async refreshToken() {
      const refresh = localStorage.getItem(CONFIG.REFRESH_KEY);
      if (!refresh) return false;
      try {
        const res = await fetch(CONFIG.API_BASE + '/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
        if (data.refresh_token) localStorage.setItem(CONFIG.REFRESH_KEY, data.refresh_token);
        return true;
      } catch { return false; }
    },

    get(endpoint) { return this.request(endpoint, { method: 'GET' }); },
    post(endpoint, body) { return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) }); },
    put(endpoint, body) { return this.request(endpoint, { method: 'PUT', body: JSON.stringify(body) }); },
    patch(endpoint, body) { return this.request(endpoint, { method: 'PATCH', body: JSON.stringify(body) }); },
    del(endpoint) { return this.request(endpoint, { method: 'DELETE' }); },
  };

  /* ═══════════════════════════════════════════════════════════════
     3. AUTH
     ═══════════════════════════════════════════════════════════════ */
  const Auth = {
    isLoggedIn() { return !!localStorage.getItem(CONFIG.TOKEN_KEY); },
    getUser() {
      try { return JSON.parse(localStorage.getItem('ms_user') || 'null'); }
      catch { return null; }
    },
    setUser(user) { localStorage.setItem('ms_user', JSON.stringify(user)); },
    logout() {
      localStorage.removeItem(CONFIG.TOKEN_KEY);
      localStorage.removeItem(CONFIG.REFRESH_KEY);
      localStorage.removeItem('ms_user');
      window.location.href = '/login';
    },
    async login(email, password) {
      const data = await API.post('/api/v1/auth/login', { email, password });
      localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
      localStorage.setItem(CONFIG.REFRESH_KEY, data.refresh_token);
      this.setUser(data.user);
      return data;
    },
    async register(userData) {
      return API.post('/api/v1/auth/register', userData);
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     4. THEME MANAGER
     ═══════════════════════════════════════════════════════════════ */
  const Theme = {
    init() {
      const saved = localStorage.getItem(CONFIG.THEME_KEY);
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.set(saved || (prefersDark ? 'dark' : 'light'));

      // Theme toggle buttons
      document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
        btn.addEventListener('click', () => this.toggle());
      });
    },
    set(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem(CONFIG.THEME_KEY, theme);
      this.updateIcons(theme);
    },
    toggle() {
      const current = document.documentElement.getAttribute('data-theme');
      this.set(current === 'dark' ? 'light' : 'dark');
    },
    updateIcons(theme) {
      document.querySelectorAll('[data-theme-icon]').forEach(icon => {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     5. WEBSOCKET
     ═══════════════════════════════════════════════════════════════ */
  const WS = {
    socket: null,
    reconnectTimer: null,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000,
    listeners: new Map(),

    connect() {
      if (this.socket?.readyState === WebSocket.OPEN) return;
      const token = localStorage.getItem(CONFIG.TOKEN_KEY);
      const url = CONFIG.WS_URL + (token ? '?token=' + encodeURIComponent(token) : '');

      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log('WS connected');
        this.reconnectDelay = 1000;
        Toast.show('Соединение установлено', 'success');
      };

      this.socket.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          this.emit(msg.type, msg.data);
        } catch (err) {
          console.error('WS parse error:', err);
        }
      };

      this.socket.onclose = () => {
        console.log('WS disconnected');
        this.scheduleReconnect();
      };

      this.socket.onerror = (err) => {
        console.error('WS error:', err);
      };
    },

    scheduleReconnect() {
      if (this.reconnectTimer) return;
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
      }, this.reconnectDelay);
    },

    send(type, data) {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type, data }));
      }
    },

    on(type, handler) {
      if (!this.listeners.has(type)) this.listeners.set(type, new Set());
      this.listeners.get(type).add(handler);
      return () => this.listeners.get(type).delete(handler);
    },

    emit(type, data) {
      this.listeners.get(type)?.forEach(h => {
        try { h(data); } catch (e) { console.error(e); }
      });
    },

    disconnect() {
      if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null; }
      this.socket?.close();
      this.socket = null;
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     6. PUSH NOTIFICATIONS
     ═══════════════════════════════════════════════════════════════ */
  const Push = {
    async init() {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) return false;

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();

      if (sub) {
        await this.sendSubscriptionToServer(sub);
        return true;
      }
      return false;
    },

    async subscribe() {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(CONFIG.PUSH_PUBLIC_KEY),
      });
      await this.sendSubscriptionToServer(sub);
      Toast.show('Уведомления включены', 'success');
      return sub;
    },

    async unsubscribe() {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await sub.unsubscribe();
        await API.post('/api/v1/push/unsubscribe', { endpoint: sub.endpoint });
        Toast.show('Уведомления отключены', 'info');
      }
    },

    async sendSubscriptionToServer(sub) {
      await API.post('/api/v1/push/subscribe', {
        endpoint: sub.endpoint,
        keys: { p256dh: btoa(String.fromCharCode(...new Uint8Array(sub.getKey('p256dh')))),
                auth: btoa(String.fromCharCode(...new Uint8Array(sub.getKey('auth')))) },
      });
    },

    urlBase64ToUint8Array(base64String) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
      const raw = atob(base64);
      return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     7. PWA SERVICE WORKER
     ═══════════════════════════════════════════════════════════════ */
  const PWA = {
    async init() {
      if (!('serviceWorker' in navigator)) return;

      try {
        const reg = await navigator.serviceWorker.register('/sw.js');
        console.log('SW registered:', reg.scope);

        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              Toast.show('Доступно обновление! Перезагрузите страницу.', 'info', 0);
            }
          });
        });
      } catch (err) {
        console.error('SW registration failed:', err);
      }

      // Install prompt
      let deferredPrompt;
      window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        document.querySelectorAll('[data-pwa-install]').forEach(el => {
          el.style.display = 'inline-flex';
          el.addEventListener('click', async () => {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') Toast.show('Приложение установлено!', 'success');
            deferredPrompt = null;
          });
        });
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     8. TOAST NOTIFICATIONS
     ═══════════════════════════════════════════════════════════════ */
  const Toast = {
    container: null,

    init() {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    },

    show(message, type = 'info', duration = 4000) {
      if (!this.container) this.init();

      const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
      const toast = document.createElement('div');
      toast.className = `toast ${type}`;
      toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${this.escapeHtml(message)}</span>`;

      this.container.appendChild(toast);

      if (duration > 0) {
        setTimeout(() => {
          toast.classList.add('toast-exit');
          toast.addEventListener('animationend', () => toast.remove());
        }, duration);
      }

      return toast;
    },

    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     9. DRAG & DROP
     ═══════════════════════════════════════════════════════════════ */
  const DragDrop = {
    init(selector, options = {}) {
      const zones = document.querySelectorAll(selector);
      zones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
          e.preventDefault();
          zone.classList.add('dragover');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
        zone.addEventListener('drop', (e) => {
          e.preventDefault();
          zone.classList.remove('dragover');
          const files = Array.from(e.dataTransfer.files);
          options.onDrop?.(files, zone);
        });
        zone.addEventListener('click', () => {
          const input = document.createElement('input');
          input.type = 'file';
          input.multiple = options.multiple !== false;
          input.accept = options.accept || '*';
          input.onchange = (e) => options.onDrop?.(Array.from(e.target.files), zone);
          input.click();
        });
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     10. VOICE INPUT
     ═══════════════════════════════════════════════════════════════ */
  const Voice = {
    recognition: null,
    isListening: false,

    init() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        console.warn('Speech recognition not supported');
        return false;
      }
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'ru-RU';
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      return true;
    },

    start(onResult, onEnd) {
      if (!this.recognition && !this.init()) return false;

      this.recognition.onresult = (e) => {
        const transcript = Array.from(e.results)
          .map(r => r[0].transcript)
          .join('');
        onResult?.(transcript, e.results[e.results.length - 1].isFinal);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        onEnd?.();
      };

      this.recognition.onerror = (e) => {
        console.error('Voice error:', e.error);
        Toast.show('Ошибка распознавания речи', 'error');
        this.isListening = false;
        onEnd?.();
      };

      this.recognition.start();
      this.isListening = true;
      return true;
    },

    stop() {
      this.recognition?.stop();
      this.isListening = false;
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     11. MODAL MANAGER
     ═══════════════════════════════════════════════════════════════ */
  const Modal = {
    open(id) {
      const modal = document.getElementById(id);
      if (!modal) return;
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';

      // Close on overlay click
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.close(id);
      });

      // Close on Escape
      const escHandler = (e) => { if (e.key === 'Escape') this.close(id); };
      document.addEventListener('keydown', escHandler);
      modal._escHandler = escHandler;
    },

    close(id) {
      const modal = document.getElementById(id);
      if (!modal) return;
      modal.classList.remove('active');
      document.body.style.overflow = '';
      if (modal._escHandler) {
        document.removeEventListener('keydown', modal._escHandler);
        delete modal._escHandler;
      }
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     12. SIDEBAR
     ═══════════════════════════════════════════════════════════════ */
  const Sidebar = {
    init() {
      const toggle = document.querySelector('[data-sidebar-toggle]');
      const layout = document.querySelector('.app-layout');
      const overlay = document.querySelector('.sidebar-overlay');
      const sidebar = document.querySelector('.sidebar');

      if (toggle && layout) {
        toggle.addEventListener('click', () => {
          if (window.innerWidth <= 992) {
            sidebar?.classList.toggle('open');
            overlay?.classList.toggle('active');
          } else {
            layout.classList.toggle('collapsed');
          }
        });
      }

      overlay?.addEventListener('click', () => {
        sidebar?.classList.remove('open');
        overlay.classList.remove('active');
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     13. TABS
     ═══════════════════════════════════════════════════════════════ */
  const Tabs = {
    init() {
      document.querySelectorAll('[data-tabs]').forEach(container => {
        const tabs = container.querySelectorAll('[data-tab]');
        const panels = container.querySelectorAll('[data-tab-panel]');

        tabs.forEach(tab => {
          tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            container.querySelector(`[data-tab-panel="${target}"]`)?.classList.add('active');
          });
        });
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     14. FORM VALIDATION
     ═══════════════════════════════════════════════════════════════ */
  const Forms = {
    init() {
      document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
          if (!this.validate(form)) e.preventDefault();
        });

        form.querySelectorAll('[data-validate]').forEach(field => {
          field.addEventListener('blur', () => this.validateField(field));
          field.addEventListener('input', () => this.clearError(field));
        });
      });
    },

    validate(form) {
      let valid = true;
      form.querySelectorAll('[data-validate]').forEach(field => {
        if (!this.validateField(field)) valid = false;
      });
      return valid;
    },

    validateField(field) {
      const rules = field.dataset.validate.split('|');
      const group = field.closest('.form-group') || field.parentElement;
      let error = '';

      for (const rule of rules) {
        const [name, param] = rule.split(':');
        const value = field.value.trim();

        if (name === 'required' && !value) error = 'Обязательное поле';
        if (name === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) error = 'Некорректный email';
        if (name === 'min' && value.length < parseInt(param)) error = `Минимум ${param} символов`;
        if (name === 'max' && value.length > parseInt(param)) error = `Максимум ${param} символов`;
        if (name === 'phone' && value && !/^\+?[\d\s()-]{10,}$/.test(value)) error = 'Некорректный телефон';
        if (name === 'inn' && value && !/^\d{10}(\d{2})?$/.test(value)) error = 'Некорректный ИНН';
        if (name === 'match' && value !== document.getElementById(param)?.value) error = 'Поля не совпадают';
        if (error) break;
      }

      if (error) {
        group.classList.add('has-error');
        let errEl = group.querySelector('.form-error');
        if (!errEl) {
          errEl = document.createElement('div');
          errEl.className = 'form-error';
          group.appendChild(errEl);
        }
        errEl.textContent = error;
        return false;
      }

      group.classList.remove('has-error');
      return true;
    },

    clearError(field) {
      const group = field.closest('.form-group') || field.parentElement;
      group.classList.remove('has-error');
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     15. LAZY LOADING IMAGES
     ═══════════════════════════════════════════════════════════════ */
  const LazyLoad = {
    init() {
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target;
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
              observer.unobserve(img);
            }
          });
        }, { rootMargin: '50px' });

        document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
      } else {
        document.querySelectorAll('img[data-src]').forEach(img => { img.src = img.dataset.src; });
      }
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     16. INFINITE SCROLL
     ═══════════════════════════════════════════════════════════════ */
  const InfiniteScroll = {
    init(selector, loadMoreFn, options = {}) {
      const container = document.querySelector(selector);
      if (!container) return;

      const sentinel = document.createElement('div');
      sentinel.className = 'infinite-sentinel';
      sentinel.style.height = '20px';
      container.appendChild(sentinel);

      let loading = false;
      const observer = new IntersectionObserver(async (entries) => {
        if (entries[0].isIntersecting && !loading) {
          loading = true;
          sentinel.innerHTML = '<div class="spinner"></div>';
          try {
            const hasMore = await loadMoreFn();
            if (!hasMore) {
              sentinel.innerHTML = '<p class="text-muted text-center" style="padding:16px">Больше нет данных</p>';
              observer.disconnect();
            }
          } finally {
            loading = false;
            if (observer) sentinel.innerHTML = '';
          }
        }
      }, { rootMargin: options.margin || '200px' });

      observer.observe(sentinel);
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     17. CHAT INTERFACE
     ═══════════════════════════════════════════════════════════════ */
  const Chat = {
    init() {
      const container = document.querySelector('.chat-messages');
      const input = document.querySelector('.chat-input');
      const sendBtn = document.querySelector('.chat-send-btn');
      const voiceBtn = document.querySelector('.chat-voice-btn');

      if (!container) return;

      // Auto-resize textarea
      if (input) {
        input.addEventListener('input', () => {
          input.style.height = 'auto';
          input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.send();
          }
        });
      }

      sendBtn?.addEventListener('click', () => this.send());

      // Voice input
      voiceBtn?.addEventListener('click', () => {
        if (Voice.isListening) {
          Voice.stop();
          voiceBtn.classList.remove('animate-pulse');
        } else {
          voiceBtn.classList.add('animate-pulse');
          Voice.start((text, isFinal) => {
            if (input) input.value = text;
            if (isFinal) {
              this.send();
              voiceBtn.classList.remove('animate-pulse');
            }
          }, () => voiceBtn.classList.remove('animate-pulse'));
        }
      });

      // WebSocket messages
      WS.on('chat_message', (data) => this.appendMessage(data));
    },

    send() {
      const input = document.querySelector('.chat-input');
      const text = input?.value.trim();
      if (!text) return;

      this.appendMessage({ text, sender: 'user', time: new Date() });
      input.value = '';
      input.style.height = 'auto';

      WS.send('chat_message', { text });

      // For Svetlana AI
      if (document.querySelector('[data-svetlana-chat]')) {
        this.showTyping();
        API.post('/api/v1/svetlana/chat', { message: text })
          .then(res => {
            this.hideTyping();
            this.appendMessage({ text: res.response, sender: 'bot', time: new Date() });
          })
          .catch(err => {
            this.hideTyping();
            Toast.show(err.message, 'error');
          });
      }
    },

    appendMessage(msg) {
      const container = document.querySelector('.chat-messages');
      if (!container) return;

      const isOwn = msg.sender === 'user';
      const div = document.createElement('div');
      div.className = `chat-message ${isOwn ? 'own' : ''}`;
      div.innerHTML = `
        <div class="chat-message-avatar ${msg.sender === 'bot' ? 'bot' : 'user'}">${isOwn ? '👤' : '🤖'}</div>
        <div>
          <div class="chat-message-content">${this.escapeHtml(msg.text)}</div>
          <div class="chat-message-time">${this.formatTime(msg.time)}</div>
        </div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    },

    showTyping() {
      const container = document.querySelector('.chat-messages');
      if (!container) return;
      const div = document.createElement('div');
      div.className = 'chat-message typing-indicator';
      div.id = 'typing-indicator';
      div.innerHTML = `
        <div class="chat-message-avatar bot">🤖</div>
        <div class="chat-message-content" style="display:flex;gap:4px;align-items:center;padding:12px 16px;">
          <span style="width:8px;height:8px;background:var(--text-muted);border-radius:50%;animation:pulse 1s infinite;"></span>
          <span style="width:8px;height:8px;background:var(--text-muted);border-radius:50%;animation:pulse 1s infinite 0.2s;"></span>
          <span style="width:8px;height:8px;background:var(--text-muted);border-radius:50%;animation:pulse 1s infinite 0.4s;"></span>
        </div>
      `;
      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    },

    hideTyping() {
      document.getElementById('typing-indicator')?.remove();
    },

    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },

    formatTime(date) {
      return new Date(date).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     18. CALENDAR
     ═══════════════════════════════════════════════════════════════ */
  const Calendar = {
    currentDate: new Date(),
    selectedDate: null,
    events: [],

    init() {
      const container = document.querySelector('[data-calendar]');
      if (!container) return;
      this.render();

      container.addEventListener('click', (e) => {
        const dayEl = e.target.closest('.calendar-day');
        if (dayEl && !dayEl.classList.contains('other-month')) {
          container.querySelectorAll('.calendar-day.selected').forEach(d => d.classList.remove('selected'));
          dayEl.classList.add('selected');
          this.selectedDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), parseInt(dayEl.dataset.day));
          this.onDateSelect?.(this.selectedDate);
        }
      });
    },

    render() {
      const container = document.querySelector('[data-calendar]');
      if (!container) return;

      const year = this.currentDate.getFullYear();
      const month = this.currentDate.getMonth();
      const firstDay = new Date(year, month, 1).getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const daysInPrevMonth = new Date(year, month, 0).getDate();

      const monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
      const dayNames = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];

      let html = `
        <div class="flex items-center justify-between" style="margin-bottom:16px;">
          <h3>${monthNames[month]} ${year}</h3>
          <div class="flex gap-sm">
            <button class="btn btn-icon btn-ghost" data-cal-prev>◀</button>
            <button class="btn btn-icon btn-ghost" data-cal-next>▶</button>
          </div>
        </div>
        <div class="calendar-grid">
          ${dayNames.map(d => `<div class="calendar-day-header">${d}</div>`).join('')}
      `;

      // Previous month days
      for (let i = firstDay === 0 ? 6 : firstDay - 1; i > 0; i--) {
        html += `<div class="calendar-day other-month"><span class="day-number">${daysInPrevMonth - i + 1}</span></div>`;
      }

      // Current month days
      const today = new Date();
      for (let day = 1; day <= daysInMonth; day++) {
        const isToday = year === today.getFullYear() && month === today.getMonth() && day === today.getDate();
        const dayEvents = this.events.filter(e => {
          const d = new Date(e.date);
          return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
        });

        html += `
          <div class="calendar-day ${isToday ? 'today' : ''}" data-day="${day}">
            <span class="day-number">${day}</span>
            <div class="day-events">
              ${dayEvents.map(e => `<div class="day-event" style="background:${e.color || 'var(--c-primary)'}20;color:${e.color || 'var(--c-primary)'};">${e.title}</div>`).join('')}
            </div>
          </div>
        `;
      }

      // Next month days
      const totalCells = Math.ceil((firstDay === 0 ? 6 : firstDay - 1 + daysInMonth) / 7) * 7;
      const remaining = totalCells - (firstDay === 0 ? 6 : firstDay - 1) - daysInMonth;
      for (let day = 1; day <= remaining; day++) {
        html += `<div class="calendar-day other-month"><span class="day-number">${day}</span></div>`;
      }

      html += '</div>';
      container.innerHTML = html;

      container.querySelector('[data-cal-prev]')?.addEventListener('click', () => {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.render();
      });
      container.querySelector('[data-cal-next]')?.addEventListener('click', () => {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.render();
      });
    },

    setEvents(events) {
      this.events = events;
      this.render();
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     19. COPY TO CLIPBOARD
     ═══════════════════════════════════════════════════════════════ */
  const Clipboard = {
    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        Toast.show('Скопировано!', 'success');
        return true;
      } catch {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        Toast.show('Скопировано!', 'success');
        return true;
      }
    },

    init() {
      document.querySelectorAll('[data-copy]').forEach(el => {
        el.addEventListener('click', () => this.copy(el.dataset.copy));
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     20. CONFIRM DIALOG
     ═══════════════════════════════════════════════════════════════ */
  const Confirm = {
    show(message, options = {}) {
      return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay active';
        overlay.innerHTML = `
          <div class="modal" style="max-width:400px;">
            <div class="modal-body text-center" style="padding:32px;">
              <div style="font-size:48px;margin-bottom:16px;">${options.icon || '⚠️'}</div>
              <h3 style="margin-bottom:8px;">${options.title || 'Подтверждение'}</h3>
              <p class="text-secondary">${message}</p>
            </div>
            <div class="modal-footer" style="justify-content:center;gap:12px;">
              <button class="btn btn-secondary" data-confirm-cancel>${options.cancelText || 'Отмена'}</button>
              <button class="btn btn-danger" data-confirm-ok>${options.okText || 'Удалить'}</button>
            </div>
          </div>
        `;
        document.body.appendChild(overlay);

        overlay.querySelector('[data-confirm-ok]').addEventListener('click', () => {
          overlay.remove();
          resolve(true);
        });
        overlay.querySelector('[data-confirm-cancel]').addEventListener('click', () => {
          overlay.remove();
          resolve(false);
        });
        overlay.addEventListener('click', (e) => {
          if (e.target === overlay) { overlay.remove(); resolve(false); }
        });
      });
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     21. EXPORT UTILITIES
     ═══════════════════════════════════════════════════════════════ */
  const Export = {
    downloadCSV(data, filename) {
      const headers = Object.keys(data[0] || {});
      const csv = [headers.join(';'), ...data.map(row => headers.map(h => `"${(row[h] || '').toString().replace(/"/g, '\"')}"`).join(';'))].join('\n');
      this.downloadBlob(new Blob([\ufeff + csv], { type: 'text/csv;charset=utf-8;' }), filename);
    },

    downloadJSON(data, filename) {
      this.downloadBlob(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }), filename);
    },

    downloadBlob(blob, filename) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     22. ANIMATIONS ON SCROLL
     ═══════════════════════════════════════════════════════════════ */
  const ScrollAnimations = {
    init() {
      if (!('IntersectionObserver' in window)) return;
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1 });

      document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
    },
  };

  /* ═══════════════════════════════════════════════════════════════
     23. INITIALIZATION
     ═══════════════════════════════════════════════════════════════ */
  function init() {
    Theme.init();
    Sidebar.init();
    Tabs.init();
    Forms.init();
    Toast.init();
    LazyLoad.init();
    Clipboard.init();
    ScrollAnimations.init();
    Chat.init();
    Calendar.init();
    PWA.init();

    if (Auth.isLoggedIn()) {
      WS.connect();
      Push.init();
    }

    console.log('✅ Мир Самозанятых v5.0 initialized');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose global API
  window.MS = { API, Auth, Theme, WS, Push, Toast, Modal, DragDrop, Voice, Chat, Calendar, Clipboard, Confirm, Export, InfiniteScroll };
})();

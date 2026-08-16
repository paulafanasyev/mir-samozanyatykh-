/* ═══════════════════════════════════════════════════════════════════════════
   МИР Самозанятых v8.7.0 — Frontend JavaScript
   Auth | API Client | Theme Switcher | Svetlana AI | Mobile Menu
   ═══════════════════════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  // ── Config ────────────────────────────────────────────────────────────────
  const API_BASE = '';
  const TOKEN_KEY = 'ms_token';
  const REFRESH_KEY = 'ms_refresh';
  const THEME_KEY = 'ms_theme';
  const SVETLANA_HISTORY_KEY = 'svetlana_history';

  // ── DOM Ready ─────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', init);

  function init() {
    initTheme();
    initMobileMenu();
    initSvetlana();
    initAuth();
    initLogout();
    initPageSpecific();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // THEME SWITCHER
  // ═══════════════════════════════════════════════════════════════════════════
  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    applyTheme(theme);

    // Add theme toggle button to navbar
    const navContainer = document.querySelector('.nav-container');
    if (navContainer && !document.getElementById('themeToggle')) {
      const toggle = document.createElement('button');
      toggle.id = 'themeToggle';
      toggle.className = 'theme-toggle';
      toggle.setAttribute('aria-label', 'Переключить тему');
      toggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
      toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        toggle.innerHTML = next === 'dark' ? '☀️' : '🌙';
      });
      navContainer.appendChild(toggle);
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // MOBILE MENU
  // ═══════════════════════════════════════════════════════════════════════════
  function initMobileMenu() {
    const toggle = document.getElementById('navToggle');
    const menu = document.getElementById('navMenu');
    if (!toggle || !menu) return;

    // Create mobile menu overlay
    let mobileOverlay = document.getElementById('mobileMenuOverlay');
    if (!mobileOverlay) {
      mobileOverlay = document.createElement('div');
      mobileOverlay.id = 'mobileMenuOverlay';
      mobileOverlay.className = 'mobile-menu';
      mobileOverlay.innerHTML = menu.innerHTML;
      document.body.appendChild(mobileOverlay);
    }

    toggle.addEventListener('click', () => {
      mobileOverlay.classList.toggle('active');
      const spans = toggle.querySelectorAll('span');
      if (mobileOverlay.classList.contains('active')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
      } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '';
        spans[2].style.transform = '';
      }
    });

    // Close on link click
    mobileOverlay.querySelectorAll('a, button').forEach(el => {
      el.addEventListener('click', () => {
        mobileOverlay.classList.remove('active');
        const spans = toggle.querySelectorAll('span');
        spans[0].style.transform = '';
        spans[1].style.opacity = '';
        spans[2].style.transform = '';
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // AUTH
  // ═══════════════════════════════════════════════════════════════════════════
  function initAuth() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      // Show admin link if admin
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.role === 'admin') {
          const adminLink = document.getElementById('adminLink');
          if (adminLink) adminLink.style.display = 'list-item';
        }
      } catch(e) {}
    }

    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
          const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
          });
          const data = await res.json();

          if (res.ok) {
            localStorage.setItem(TOKEN_KEY, data.access_token);
            localStorage.setItem(REFRESH_KEY, data.refresh_token);
            showToast('Вход выполнен!', 'success');
            setTimeout(() => window.location.href = '/dashboard', 500);
          } else {
            showToast(data.detail || 'Ошибка входа', 'error');
          }
        } catch (err) {
          showToast('Ошибка сети', 'error');
        }
      });
    }

    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
      const passwordInput = document.getElementById('password');
      const strengthBar = document.getElementById('passwordStrength');

      if (passwordInput && strengthBar) {
        passwordInput.addEventListener('input', () => {
          const val = passwordInput.value;
          let strength = 0;
          if (val.length >= 8) strength++;
          if (/[A-Z]/.test(val)) strength++;
          if (/[0-9]/.test(val)) strength++;
          if (/[^A-Za-z0-9]/.test(val)) strength++;

          strengthBar.className = 'password-strength-bar';
          if (strength <= 1) strengthBar.classList.add('weak');
          else if (strength <= 2) strengthBar.classList.add('medium');
          else strengthBar.classList.add('strong');
        });
      }

      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
          email: document.getElementById('email').value,
          password: document.getElementById('password').value,
          name: document.getElementById('name').value,
          phone: document.getElementById('phone').value,
          inn: document.getElementById('inn').value
        };

        try {
          const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          const result = await res.json();

          if (res.ok) {
            showToast('Регистрация успешна!', 'success');
            setTimeout(() => window.location.href = '/login', 500);
          } else {
            showToast(result.detail || 'Ошибка регистрации', 'error');
          }
        } catch (err) {
          showToast('Ошибка сети', 'error');
        }
      });
    }
  }

  function initLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        showToast('Вы вышли из системы', 'info');
        setTimeout(() => window.location.href = '/', 500);
      });
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // API CLIENT
  // ═══════════════════════════════════════════════════════════════════════════
  async function api(endpoint, options = {}) {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    };

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = '/login';
      return;
    }

    return res;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SVETLANA AI
  // ═══════════════════════════════════════════════════════════════════════════
  function initSvetlana() {
    const widget = document.getElementById('svetlanaWidget');
    const toggle = document.getElementById('svetlanaToggle');
    const chat = document.getElementById('svetlanaChat');
    const close = document.getElementById('svetlanaClose');
    const input = document.getElementById('svetlanaInput');
    const send = document.getElementById('svetlanaSend');
    const messages = document.getElementById('svetlanaMessages');

    if (!toggle || !chat) return;

    // Load history
    const history = JSON.parse(localStorage.getItem(SVETLANA_HISTORY_KEY) || '[]');
    history.forEach(msg => addMessage(msg.text, msg.isUser, false));

    toggle.addEventListener('click', () => chat.classList.toggle('active'));
    close.addEventListener('click', () => chat.classList.remove('active'));

    function sendMessage(text) {
      if (!text.trim()) return;
      addMessage(text, true);
      input.value = '';

      // Show typing indicator
      const typing = document.createElement('div');
      typing.className = 'message bot';
      typing.innerHTML = '<div class="message-content">Печатает<span class="dots">...</span></div>';
      typing.id = 'typingIndicator';
      messages.appendChild(typing);
      messages.scrollTop = messages.scrollHeight;

      // Call API
      api('/api/svetlana/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text })
      }).then(res => res.json()).then(data => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
        addMessage(data.response, false);
      }).catch(() => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
        addMessage('Извините, произошла ошибка. Попробуйте позже.', false);
      });
    }

    send.addEventListener('click', () => sendMessage(input.value));
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage(input.value);
    });

    // Quick buttons
    document.querySelectorAll('.quick-btn').forEach(btn => {
      btn.addEventListener('click', () => sendMessage(btn.dataset.q));
    });

    function addMessage(text, isUser, save = true) {
      const msg = document.createElement('div');
      msg.className = `message ${isUser ? 'user' : 'bot'}`;
      const time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
      msg.innerHTML = `<div class="message-content">${escapeHtml(text)}</div><div class="message-time">${time}</div>`;
      messages.appendChild(msg);
      messages.scrollTop = messages.scrollHeight;

      if (save) {
        const history = JSON.parse(localStorage.getItem(SVETLANA_HISTORY_KEY) || '[]');
        history.push({ text, isUser, time: Date.now() });
        if (history.length > 100) history.shift();
        localStorage.setItem(SVETLANA_HISTORY_KEY, JSON.stringify(history));
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PAGE SPECIFIC
  // ═══════════════════════════════════════════════════════════════════════════
  function initPageSpecific() {
    const path = window.location.pathname;

    if (path === '/dashboard') initDashboard();
    if (path === '/contracts') initContracts();
    if (path === '/finance') initFinance();
    if (path === '/calculator') initCalculator();
    if (path === '/crm') initCRM();
    if (path === '/marketplace') initMarketplace();
    if (path === '/grants') initGrants();
    if (path === '/profile') initProfile();
    if (path === '/admin') initAdmin();
  }

  function initDashboard() {
    // Load stats
    api('/api/finance').then(r => r.json()).then(data => {
      const incomeEl = document.getElementById('dashIncome');
      const expenseEl = document.getElementById('dashExpense');
      const balanceEl = document.getElementById('dashBalance');
      if (incomeEl) incomeEl.textContent = formatMoney(data.total_income || 0);
      if (expenseEl) expenseEl.textContent = formatMoney(data.total_expense || 0);
      if (balanceEl) balanceEl.textContent = formatMoney(data.balance || 0);
    });

    api('/api/contracts').then(r => r.json()).then(data => {
      const el = document.getElementById('dashContracts');
      if (el) el.textContent = data.total || 0;
    });

    api('/api/achievements').then(r => r.json()).then(data => {
      const el = document.getElementById('dashAchievements');
      if (el) el.textContent = data.total || 0;
    });
  }

  function initContracts() {
    loadList('/api/contracts', 'contractsList', renderContract);

    const form = document.getElementById('contractForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
          title: document.getElementById('contractTitle').value,
          type: document.getElementById('contractType').value,
          client_name: document.getElementById('clientName').value,
          client_inn: document.getElementById('clientInn').value,
          amount: parseFloat(document.getElementById('contractAmount').value)
        };
        const res = await api('/api/contracts', { method: 'POST', body: JSON.stringify(data) });
        if (res.ok) {
          showToast('Договор создан!', 'success');
          form.reset();
          loadList('/api/contracts', 'contractsList', renderContract);
        }
      });
    }
  }

  function initFinance() {
    loadList('/api/finance', 'financeList', renderFinance);

    const form = document.getElementById('financeForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
          type: document.getElementById('financeType').value,
          amount: parseFloat(document.getElementById('financeAmount').value),
          category: document.getElementById('financeCategory').value,
          description: document.getElementById('financeDesc').value
        };
        const res = await api('/api/finance', { method: 'POST', body: JSON.stringify(data) });
        if (res.ok) {
          showToast('Запись добавлена!', 'success');
          form.reset();
          loadList('/api/finance', 'financeList', renderFinance);
        }
      });
    }
  }

  function initCalculator() {
    const form = document.getElementById('npdForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const amount = parseFloat(document.getElementById('npdAmount').value);
        const res = await api('/api/calculator/npd', {
          method: 'POST',
          body: JSON.stringify({ amount, region: 'default' })
        });
        const data = await res.json();
        document.getElementById('npdResult').innerHTML = `
          <div class="card">
            <p><strong>Сумма:</strong> ${formatMoney(data.amount)}</p>
            <p><strong>Ставка:</strong> ${(data.rate * 100).toFixed(0)}%</p>
            <p><strong>Налог:</strong> ${formatMoney(data.tax)}</p>
            <p><strong>На руки:</strong> <span style="color:var(--color-accent);font-weight:700">${formatMoney(data.net)}</span></p>
          </div>
        `;
      });
    }

    // CBR rates
    api('/api/cbr/rates').then(r => r.json()).then(data => {
      const el = document.getElementById('cbrRates');
      if (el) {
        el.innerHTML = `
          <div class="stats-grid">
            <div class="stat-box"><div class="label">USD</div><div class="value">${data.USD} ₽</div></div>
            <div class="stat-box"><div class="label">EUR</div><div class="value">${data.EUR} ₽</div></div>
            <div class="stat-box"><div class="label">CNY</div><div class="value">${data.CNY} ₽</div></div>
          </div>
          <p style="color:var(--color-text-muted);font-size:12px;margin-top:8px">Обновлено: ${new Date(data.updated_at).toLocaleString('ru-RU')}</p>
        `;
      }
    });
  }

  function initCRM() {
    loadList('/api/crm/clients', 'clientsList', renderClient);
  }

  function initMarketplace() {
    loadList('/api/marketplace/services', 'servicesList', renderService);
  }

  function initGrants() {
    loadList('/api/grants', 'grantsList', renderGrant);
  }

  function initProfile() {
    api('/api/auth/me').then(r => r.json()).then(data => {
      const fields = ['profileName', 'profileEmail', 'profilePhone', 'profileInn', 'profileSubscription'];
      const values = [data.name, data.email, data.phone, data.inn, data.subscription];
      fields.forEach((id, i) => {
        const el = document.getElementById(id);
        if (el) el.textContent = values[i] || '—';
      });
    });
  }

  function initAdmin() {
    api('/api/admin/stats').then(r => r.json()).then(data => {
      Object.keys(data).forEach(key => {
        const el = document.getElementById(`admin${key.charAt(0).toUpperCase() + key.slice(1)}`);
        if (el) el.textContent = data[key];
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // HELPERS
  // ═══════════════════════════════════════════════════════════════════════════
  async function loadList(endpoint, containerId, renderFn) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '<div class="skeleton" style="height:200px"></div>';

    try {
      const res = await api(endpoint);
      const data = await res.json();
      const items = data.items || [];

      if (items.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--color-text-muted);padding:40px">Нет данных</p>';
        return;
      }

      container.innerHTML = items.map(renderFn).join('');
    } catch (err) {
      container.innerHTML = '<p style="text-align:center;color:var(--color-error);padding:40px">Ошибка загрузки</p>';
    }
  }

  function renderContract(c) {
    return `
      <div class="card" style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <h4 style="font-weight:600">${escapeHtml(c.title)}</h4>
            <p style="color:var(--color-text-secondary);font-size:14px">${escapeHtml(c.client_name)} • ИНН: ${c.client_inn}</p>
          </div>
          <span class="badge-status ${c.status}">${c.status === 'active' ? 'Активен' : c.status === 'draft' ? 'Черновик' : 'Завершён'}</span>
        </div>
        <p style="margin-top:8px;font-size:18px;font-weight:700;color:var(--color-accent)">${formatMoney(c.amount)}</p>
      </div>
    `;
  }

  function renderFinance(f) {
    const isIncome = f.type === 'income';
    return `
      <div class="card" style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
        <div>
          <h4 style="font-weight:600">${escapeHtml(f.description || f.category)}</h4>
          <p style="color:var(--color-text-secondary);font-size:14px">${f.category} • ${new Date(f.date).toLocaleDateString('ru-RU')}</p>
        </div>
        <span style="font-size:18px;font-weight:700;color:${isIncome ? 'var(--color-success)' : 'var(--color-error)'}">
          ${isIncome ? '+' : '-'}${formatMoney(f.amount)}
        </span>
      </div>
    `;
  }

  function renderClient(c) {
    return `
      <div class="card" style="margin-bottom:12px">
        <h4 style="font-weight:600">${escapeHtml(c.name)}</h4>
        <p style="color:var(--color-text-secondary);font-size:14px">${c.email || ''} ${c.phone || ''}</p>
        <span class="badge-status ${c.status}">${c.status}</span>
      </div>
    `;
  }

  function renderService(s) {
    return `
      <div class="card" style="margin-bottom:12px">
        <h4 style="font-weight:600">${escapeHtml(s.title)}</h4>
        <p style="color:var(--color-text-secondary);font-size:14px">${escapeHtml(s.description || '')}</p>
        <p style="margin-top:8px;font-size:18px;font-weight:700;color:var(--color-accent)">${formatMoney(s.price)}</p>
      </div>
    `;
  }

  function renderGrant(g) {
    return `
      <div class="card" style="margin-bottom:12px">
        <h4 style="font-weight:600">${escapeHtml(g.title)}</h4>
        <p style="color:var(--color-text-secondary);font-size:14px">${escapeHtml(g.description || '')}</p>
        <p style="margin-top:8px;font-size:18px;font-weight:700;color:var(--color-accent)">${formatMoney(g.amount)}</p>
      </div>
    `;
  }

  function formatMoney(amount) {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(amount);
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // Expose for inline handlers
  window.MirApp = { api, showToast, formatMoney };
})();

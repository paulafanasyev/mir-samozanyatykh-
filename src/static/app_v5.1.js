/* ============================================
   Мир Самозанятых v5.1 — Svetlana AI v3.0
   Голосовой ввод, история диалогов, контекстная помощь
   ============================================ */

class SvetlanaAI {
  constructor() {
    this.chatOpen = false;
    this.messages = [];
    this.recognition = null;
    this.isRecording = false;
    this.knowledge = null;
    this.currentContext = null;
    this.userId = this.getUserId();
    this.init();
  }

  async init() {
    await this.loadKnowledge();
    this.createWidget();
    this.setupEventListeners();
    this.loadHistory();
    this.setupVoiceRecognition();
  }

  getUserId() {
    let id = localStorage.getItem('svetlana_user_id');
    if (!id) {
      id = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('svetlana_user_id', id);
    }
    return id;
  }

  async loadKnowledge() {
    try {
      const response = await fetch('/static/svetlana_knowledge_v3.json');
      this.knowledge = await response.json();
    } catch (e) {
      console.warn('Svetlana: Could not load knowledge base, using fallback');
      this.knowledge = this.getFallbackKnowledge();
    }
  }

  getFallbackKnowledge() {
    return {
      topics: {},
      quick_responses: {
        greeting: "Здравствуйте! Я Светлана, ваш ИИ-ассистент. Чем могу помочь?",
        unknown: "Извините, я пока не знаю ответа. Попробуйте переформулировать.",
        goodbye: "До свидания! Обращайтесь ещё.",
        thanks: "Пожалуйста! Рада помочь.",
        error: "Произошла ошибка. Попробуйте позже.",
        voice_not_supported: "Голосовой ввод недоступен. Используйте текст.",
        history_empty: "История пуста. Начните общение!",
        context_help: "💡 Совет: Если что-то непонятно — спросите меня!"
      }
    };
  }

  createWidget() {
    const widget = document.createElement('div');
    widget.className = 'svetlana-widget';
    widget.innerHTML = `
      <button class="svetlana-toggle" id="svetlanaToggle" aria-label="Открыть чат с Светланой">
        <span>💬</span>
      </button>
      <div class="svetlana-chat" id="svetlanaChat">
        <div class="svetlana-header">
          <h4><span class="svetlana-status"></span> 🤖 Светлана</h4>
          <button id="svetlanaClose" style="background:none;border:none;color:white;cursor:pointer;font-size:1.25rem;">✕</button>
        </div>
        <div class="svetlana-messages" id="svetlanaMessages"></div>
        <div class="quick-replies" id="quickReplies"></div>
        <div class="svetlana-input-area">
          <button class="svetlana-voice" id="svetlanaVoice" title="Голосовой ввод">🎤</button>
          <input type="text" class="svetlana-input" id="svetlanaInput" placeholder="Введите вопрос..." autocomplete="off">
          <button class="svetlana-send" id="svetlanaSend">➤</button>
        </div>
      </div>
    `;
    document.body.appendChild(widget);
  }

  setupEventListeners() {
    const toggle = document.getElementById('svetlanaToggle');
    const close = document.getElementById('svetlanaClose');
    const chat = document.getElementById('svetlanaChat');
    const input = document.getElementById('svetlanaInput');
    const send = document.getElementById('svetlanaSend');
    const voice = document.getElementById('svetlanaVoice');

    toggle.addEventListener('click', () => this.toggleChat());
    close.addEventListener('click', () => this.closeChat());

    send.addEventListener('click', () => this.sendMessage());
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });

    voice.addEventListener('click', () => this.toggleVoice());

    // Закрытие по клику вне чата
    document.addEventListener('click', (e) => {
      if (this.chatOpen && !chat.contains(e.target) && !toggle.contains(e.target)) {
        this.closeChat();
      }
    });
  }

  setupVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'ru-RU';
      this.recognition.continuous = false;
      this.recognition.interimResults = false;

      this.recognition.onstart = () => {
        this.isRecording = true;
        document.getElementById('svetlanaVoice').classList.add('recording');
        document.getElementById('svetlanaInput').placeholder = 'Говорите...';
      };

      this.recognition.onend = () => {
        this.isRecording = false;
        document.getElementById('svetlanaVoice').classList.remove('recording');
        document.getElementById('svetlanaInput').placeholder = 'Введите вопрос...';
      };

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('svetlanaInput').value = transcript;
        setTimeout(() => this.sendMessage(), 300);
      };

      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        this.isRecording = false;
        document.getElementById('svetlanaVoice').classList.remove('recording');
        this.addMessage('bot', this.knowledge?.quick_responses?.voice_not_supported || 'Голосовой ввод недоступен.');
      };
    }
  }

  toggleVoice() {
    if (!this.recognition) {
      this.addMessage('bot', this.knowledge?.quick_responses?.voice_not_supported || 'Голосовой ввод не поддерживается вашим браузером.');
      return;
    }
    if (this.isRecording) {
      this.recognition.stop();
    } else {
      this.recognition.start();
    }
  }

  toggleChat() {
    const chat = document.getElementById('svetlanaChat');
    this.chatOpen = !this.chatOpen;
    chat.classList.toggle('open', this.chatOpen);

    if (this.chatOpen && this.messages.length === 0) {
      this.addMessage('bot', this.knowledge?.quick_responses?.greeting || 'Здравствуйте! Я Светлана.');
    }

    if (this.chatOpen) {
      setTimeout(() => document.getElementById('svetlanaInput').focus(), 300);
    }
  }

  closeChat() {
    this.chatOpen = false;
    document.getElementById('svetlanaChat').classList.remove('open');
  }

  sendMessage() {
    const input = document.getElementById('svetlanaInput');
    const text = input.value.trim();
    if (!text) return;

    this.addMessage('user', text);
    input.value = '';
    this.processQuery(text);
  }

  addMessage(sender, text) {
    const container = document.getElementById('svetlanaMessages');
    const msg = document.createElement('div');
    msg.className = `message message-${sender}`;
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;

    this.messages.push({ sender, text, timestamp: new Date().toISOString() });
    this.saveHistory();
  }

  processQuery(query) {
    // Показываем индикатор загрузки
    const container = document.getElementById('svetlanaMessages');
    const loading = document.createElement('div');
    loading.className = 'message message-bot';
    loading.innerHTML = '<span class="skeleton" style="display:inline-block;width:60px;height:16px;"></span>';
    loading.id = 'svetlanaLoading';
    container.appendChild(loading);
    container.scrollTop = container.scrollHeight;

    // Имитируем задержку для естественности
    setTimeout(() => {
      loading.remove();
      const response = this.findAnswer(query);
      this.addMessage('bot', response.text);
      this.showQuickReplies(response.quickReplies);
    }, 600 + Math.random() * 400);
  }

  findAnswer(query) {
    if (!this.knowledge || !this.knowledge.topics) {
      return { text: this.knowledge?.quick_responses?.error || 'Ошибка загрузки базы знаний.', quickReplies: [] };
    }

    const lowerQuery = query.toLowerCase();

    // Приветствие
    if (/привет|здравствуй|добрый день|доброе утро|добрый вечер|хай|hi|hello/.test(lowerQuery)) {
      return { text: this.knowledge.quick_responses.greeting, quickReplies: this.getDefaultQuickReplies() };
    }

    // Прощание
    if (/пока|до свидания|спасибо|благодар|спс|thx/.test(lowerQuery)) {
      return { text: this.knowledge.quick_responses.thanks, quickReplies: [] };
    }

    // Поиск по ключевым словам
    let bestMatch = null;
    let bestScore = 0;

    for (const [key, topic] of Object.entries(this.knowledge.topics)) {
      let score = 0;
      const keywords = topic.keywords || [];

      for (const keyword of keywords) {
        if (lowerQuery.includes(keyword.toLowerCase())) {
          score += keyword.length; // Длинные ключевые слова важнее
        }
      }

      // Проверяем заголовок
      if (lowerQuery.includes(topic.title.toLowerCase().split(' ')[0])) {
        score += 20;
      }

      if (score > bestScore) {
        bestScore = score;
        bestMatch = topic;
      }
    }

    if (bestMatch && bestScore > 0) {
      return {
        text: bestMatch.content.trim(),
        quickReplies: bestMatch.quick_replies || []
      };
    }

    // Контекстная помощь
    if (this.currentContext) {
      return {
        text: this.getContextualResponse(lowerQuery),
        quickReplies: this.getContextQuickReplies()
      };
    }

    return {
      text: this.knowledge.quick_responses.unknown,
      quickReplies: this.getDefaultQuickReplies()
    };
  }

  getDefaultQuickReplies() {
    return [
      'Что такое НПД?',
      'Как зарегистрироваться?',
      'Какие налоги платить?',
      'Как получить грант?',
      'ПСН или НПД?',
      'Международные платежи'
    ];
  }

  getContextualResponse(query) {
    const contextResponses = {
      'register': 'Для регистрации как самозанятый необходимо: 1) Скачать приложение «Мой налог», 2) Пройти идентификацию через Госуслуги, 3) Выбрать вид деятельности, 4) Начать формировать чеки.',
      'login': 'Для входа используйте ваш email и пароль. Если забыли пароль — нажмите «Восстановить».',
      'calculator': 'Налоговый калькулятор поможет рассчитать вашу налоговую нагрузку. Введите сумму дохода и выберите источник.',
      'contract': 'При заполнении договора укажите: стороны, предмет, сумму, сроки, ответственность. Используйте наши шаблоны.',
      'profile': 'В профиле вы можете: изменить данные, настроить уведомления, подключить 2FA, просмотреть историю.',
      'payment': 'Для оплаты подписки выберите тариф и способ оплаты. Принимаем карты, ЮKassa, СБП.',
      'support': 'Наша поддержка работает 24/7. Напишите в чат или на email: it-laboratory@bk.ru'
    };

    for (const [key, response] of Object.entries(contextResponses)) {
      if (this.currentContext.includes(key)) {
        return response;
      }
    }

    return this.knowledge?.quick_responses?.context_help || '💡 Совет: Если что-то непонятно — спросите меня!';
  }

  getContextQuickReplies() {
    const contextMap = {
      'register': ['Как пройти идентификацию?', 'Сколько стоит регистрация?', 'Какие документы нужны?'],
      'login': ['Забыл пароль', 'Как включить 2FA?', 'Проблемы со входом'],
      'calculator': ['Как рассчитать налог?', 'Какие ставки?', 'Какой вычет положен?'],
      'contract': ['Шаблоны договоров', 'Как заполнить?', 'Юридическая проверка'],
      'profile': ['Изменить данные', 'Настройки', 'История операций'],
      'payment': ['Тарифы', 'Способы оплаты', 'Возврат средств'],
      'support': ['Написать в поддержку', 'FAQ', 'Телефон горячей линии']
    };

    for (const [key, replies] of Object.entries(contextMap)) {
      if (this.currentContext.includes(key)) {
        return replies;
      }
    }

    return this.getDefaultQuickReplies();
  }

  showQuickReplies(replies) {
    const container = document.getElementById('quickReplies');
    container.innerHTML = '';

    replies.forEach(reply => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply';
      btn.textContent = reply;
      btn.addEventListener('click', () => {
        document.getElementById('svetlanaInput').value = reply;
        this.sendMessage();
      });
      container.appendChild(btn);
    });
  }

  // Контекстная помощь для форм
  setContext(context) {
    this.currentContext = context;
    // Показываем подсказку
    const helpElements = document.querySelectorAll('[data-svetlana-help]');
    helpElements.forEach(el => {
      const helpText = el.getAttribute('data-svetlana-help');
      if (helpText) {
        const helpIcon = document.createElement('span');
        helpIcon.className = 'context-help';
        helpIcon.innerHTML = `
          <span class="context-help-icon">?</span>
          <span class="context-help-tooltip">${helpText}</span>
        `;
        el.appendChild(helpIcon);
      }
    });
  }

  // История диалогов
  saveHistory() {
    try {
      const history = {
        userId: this.userId,
        messages: this.messages.slice(-100), // Храним последние 100 сообщений
        lastUpdated: new Date().toISOString()
      };
      localStorage.setItem('svetlana_history', JSON.stringify(history));
    } catch (e) {
      console.warn('Svetlana: Could not save history');
    }
  }

  loadHistory() {
    try {
      const saved = localStorage.getItem('svetlana_history');
      if (saved) {
        const history = JSON.parse(saved);
        if (history.userId === this.userId && history.messages) {
          this.messages = history.messages;
        }
      }
    } catch (e) {
      console.warn('Svetlana: Could not load history');
    }
  }

  clearHistory() {
    this.messages = [];
    localStorage.removeItem('svetlana_history');
    const container = document.getElementById('svetlanaMessages');
    if (container) container.innerHTML = '';
  }

  // Экспорт истории
  exportHistory() {
    const history = {
      userId: this.userId,
      messages: this.messages,
      exportedAt: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(history, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `svetlana_history_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// ============================================
// UI Enhancements — Micro-animations & Parallax
// ============================================

class UIEnhancements {
  constructor() {
    this.init();
  }

  init() {
    this.setupNavbarScroll();
    this.setupParallax();
    this.setupFadeInOnScroll();
    this.setupCardHover();
    this.setupFormValidation();
    this.setupToastSystem();
  }

  setupNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    let lastScroll = 0;
    window.addEventListener('scroll', () => {
      const currentScroll = window.pageYOffset;

      if (currentScroll > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }

      // Hide/show on scroll direction
      if (currentScroll > lastScroll && currentScroll > 200) {
        navbar.style.transform = 'translateY(-100%)';
      } else {
        navbar.style.transform = 'translateY(0)';
      }

      lastScroll = currentScroll;
    });
  }

  setupParallax() {
    const parallaxElements = document.querySelectorAll('[data-parallax]');
    if (!parallaxElements.length) return;

    let ticking = false;

    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          const scrollY = window.pageYOffset;
          parallaxElements.forEach(el => {
            const speed = parseFloat(el.dataset.parallax) || 0.5;
            const yPos = -(scrollY * speed);
            el.style.transform = `translateY(${yPos}px)`;
          });
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  setupFadeInOnScroll() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.feature-card, .stat-card, .glass-card').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(30px)';
      el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
      observer.observe(el);
    });
  }

  setupCardHover() {
    document.querySelectorAll('.feature-card, .glass-card').forEach(card => {
      card.addEventListener('mouseenter', () => {
        card.style.transition = 'transform 0.3s ease-out, box-shadow 0.3s ease-out';
      });
    });
  }

  setupFormValidation() {
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => {
        let valid = true;
        form.querySelectorAll('[required]').forEach(field => {
          if (!field.value.trim()) {
            valid = false;
            field.style.borderColor = 'var(--danger)';
            field.style.boxShadow = '0 0 0 4px var(--danger-light)';

            // Shake animation
            field.style.animation = 'shake 0.5s ease-in-out';
            setTimeout(() => {
              field.style.animation = '';
            }, 500);
          } else {
            field.style.borderColor = '';
            field.style.boxShadow = '';
          }
        });

        if (!valid) {
          e.preventDefault();
          this.showToast('Пожалуйста, заполните все обязательные поля', 'error');
        }
      });

      // Real-time validation
      form.querySelectorAll('input, textarea, select').forEach(field => {
        field.addEventListener('blur', () => {
          if (field.hasAttribute('required') && !field.value.trim()) {
            field.style.borderColor = 'var(--danger)';
          } else {
            field.style.borderColor = '';
          }
        });
      });
    });
  }

  setupToastSystem() {
    // Create toast container if not exists
    if (!document.getElementById('toastContainer')) {
      const container = document.createElement('div');
      container.className = 'toast-container';
      container.id = 'toastContainer';
      document.body.appendChild(container);
    }
  }

  showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100px)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

// ============================================
// Mobile Menu
// ============================================

class MobileMenu {
  constructor() {
    this.init();
  }

  init() {
    const btn = document.querySelector('.mobile-menu-btn');
    const nav = document.querySelector('.nav-links');

    if (btn && nav) {
      btn.addEventListener('click', () => {
        nav.classList.toggle('active');
        btn.innerHTML = nav.classList.contains('active') ? '✕' : '☰';
      });

      // Close on link click
      nav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
          nav.classList.remove('active');
          btn.innerHTML = '☰';
        });
      });
    }
  }
}

// ============================================
// Calculator Module
// ============================================

class TaxCalculator {
  constructor() {
    this.rates = {
      individual: 0.04,
      legal: 0.06,
      it: 0.03
    };
    this.deduction = 10000;
    this.init();
  }

  init() {
    const form = document.getElementById('taxCalculator');
    if (!form) return;

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.calculate();
    });
  }

  calculate() {
    const income = parseFloat(document.getElementById('income').value) || 0;
    const type = document.getElementById('incomeType').value;
    const hasDeduction = document.getElementById('hasDeduction')?.checked ?? true;

    let rate = this.rates[type] || this.rates.individual;
    let tax = income * rate;

    // Apply deduction
    if (hasDeduction && this.deduction > 0) {
      const deductionUsed = Math.min(tax, this.deduction);
      tax -= deductionUsed;
    }

    const result = {
      income,
      rate: rate * 100,
      tax: Math.max(0, tax),
      netIncome: income - Math.max(0, tax)
    };

    this.displayResult(result);
  }

  displayResult(result) {
    const container = document.getElementById('calcResult');
    if (!container) return;

    container.innerHTML = `
      <div class="glass-card" style="padding: 1.5rem; margin-top: 1rem;">
        <h4>📊 Результат расчёта</h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem;">
          <div>
            <div style="font-size: 0.875rem; color: var(--neutral-500);">Доход</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-700);">${result.income.toLocaleString('ru-RU')} ₽</div>
          </div>
          <div>
            <div style="font-size: 0.875rem; color: var(--neutral-500);">Ставка</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-700);">${result.rate}%</div>
          </div>
          <div>
            <div style="font-size: 0.875rem; color: var(--neutral-500);">Налог</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--danger);">${result.tax.toLocaleString('ru-RU')} ₽</div>
          </div>
          <div>
            <div style="font-size: 0.875rem; color: var(--neutral-500);">На руки</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--success);">${result.netIncome.toLocaleString('ru-RU')} ₽</div>
          </div>
        </div>
      </div>
    `;
  }
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Svetlana
  window.svetlana = new SvetlanaAI();

  // Initialize UI enhancements
  window.ui = new UIEnhancements();

  // Initialize mobile menu
  window.mobileMenu = new MobileMenu();

  // Initialize calculator
  window.calculator = new TaxCalculator();

  // Setup context help for forms
  const currentPage = document.body.dataset.page;
  if (currentPage && window.svetlana) {
    window.svetlana.setContext(currentPage);
  }

  console.log('🤖 Светлана v3.0 инициализирована');
  console.log('🎨 Glassmorphism UI активирован');
});

// Shake animation keyframes (added via JS to avoid CSS clutter)
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-8px); }
    40% { transform: translateX(8px); }
    60% { transform: translateX(-4px); }
    80% { transform: translateX(4px); }
  }
`;
document.head.appendChild(shakeStyle);

/* ============================================
   Мир Самозанятых v7.0 — Frontend JavaScript
   Темы, анимации, мобильное меню, интерактивность
   ============================================ */

(function() {
  'use strict';

  /* ============================================
     THEME SYSTEM
     ============================================ */
  const ThemeManager = {
    key: 'mir-samozanyatykh-theme',

    init() {
      const saved = localStorage.getItem(this.key);
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const theme = saved || (prefersDark ? 'dark' : 'light');
      this.set(theme, false);

      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(this.key)) {
          this.set(e.matches ? 'dark' : 'light', true);
        }
      });
    },

    set(theme, animate = true) {
      document.documentElement.setAttribute('data-theme', theme);
      if (animate) {
        document.body.style.transition = 'background 0.3s ease, color 0.3s ease';
        setTimeout(() => { document.body.style.transition = ''; }, 300);
      }
    },

    toggle() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'light' ? 'dark' : 'light';
      this.set(next, true);
      localStorage.setItem(this.key, next);
    }
  };

  /* ============================================
     MOBILE MENU
     ============================================ */
  const MobileMenu = {
    init() {
      const btn = document.getElementById('mobileMenuBtn');
      const links = document.getElementById('navLinks');
      if (!btn || !links) return;

      btn.addEventListener('click', () => {
        const isOpen = links.classList.toggle('active');
        btn.setAttribute('aria-expanded', isOpen);
        btn.innerHTML = isOpen 
          ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`
          : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px;"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`;
      });

      // Close on link click
      links.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
          links.classList.remove('active');
          btn.setAttribute('aria-expanded', 'false');
        });
      });
    }
  };

  /* ============================================
     NAVBAR SCROLL EFFECT
     ============================================ */
  const NavbarScroll = {
    init() {
      const navbar = document.getElementById('navbar');
      if (!navbar) return;

      let ticking = false;
      window.addEventListener('scroll', () => {
        if (!ticking) {
          window.requestAnimationFrame(() => {
            navbar.classList.toggle('scrolled', window.scrollY > 10);
            ticking = false;
          });
          ticking = true;
        }
      });
    }
  };

  /* ============================================
     INTERSECTION OBSERVER — FADE IN ANIMATIONS
     ============================================ */
  const ScrollAnimations = {
    init() {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('fade-in-visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

      document.querySelectorAll('[data-animate]').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
      });
    }
  };

  // Add fade-in-visible style
  const style = document.createElement('style');
  style.textContent = '.fade-in-visible { opacity: 1 !important; transform: translateY(0) !important; }';
  document.head.appendChild(style);

  /* ============================================
     FORM VALIDATION HELPERS
     ============================================ */
  const FormHelpers = {
    init() {
      document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
          let valid = true;
          form.querySelectorAll('[required]').forEach(field => {
            if (!field.value.trim()) {
              valid = false;
              field.style.borderColor = 'var(--danger)';
              field.addEventListener('input', () => { field.style.borderColor = ''; }, { once: true });
            }
          });
          if (!valid) e.preventDefault();
        });
      });
    }
  };

  /* ============================================
     BUTTON RIPPLE EFFECT
     ============================================ */
  const RippleEffect = {
    init() {
      document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
          const rect = this.getBoundingClientRect();
          const ripple = document.createElement('span');
          const size = Math.max(rect.width, rect.height);
          ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            width: ${size}px;
            height: ${size}px;
            left: ${e.clientX - rect.left - size/2}px;
            top: ${e.clientY - rect.top - size/2}px;
            pointer-events: none;
            animation: ripple 0.6s ease-out;
          `;
          this.appendChild(ripple);
          setTimeout(() => ripple.remove(), 600);
        });
      });
    }
  };

  // Add ripple animation
  const rippleStyle = document.createElement('style');
  rippleStyle.textContent = `
    @keyframes ripple {
      from { transform: scale(0); opacity: 0.5; }
      to { transform: scale(2); opacity: 0; }
    }
  `;
  document.head.appendChild(rippleStyle);

  /* ============================================
     SKELETON LOADING
     ============================================ */
  const SkeletonLoader = {
    show(container) {
      container.innerHTML = `
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-text" style="width:90%"></div>
        <div class="skeleton skeleton-text" style="width:75%"></div>
        <div class="skeleton skeleton-text" style="width:60%"></div>
      `;
    },
    hide(container, content) {
      container.style.opacity = '0';
      setTimeout(() => {
        container.innerHTML = content;
        container.style.transition = 'opacity 0.3s ease';
        container.style.opacity = '1';
      }, 300);
    }
  };

  /* ============================================
     TOAST NOTIFICATIONS
     ============================================ */
  const Toast = {
    container: null,

    init() {
      this.container = document.createElement('div');
      this.container.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: var(--z-toast);
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      `;
      document.body.appendChild(this.container);
    },

    show(message, type = 'info', duration = 4000) {
      if (!this.container) this.init();

      const toast = document.createElement('div');
      toast.className = `alert alert-${type}`;
      toast.style.cssText = `
        min-width: 300px;
        max-width: 400px;
        box-shadow: var(--shadow-lg);
        animation: slideIn 0.3s ease-out;
      `;

      const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;flex-shrink:0;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;flex-shrink:0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        danger: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px;flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
      };

      toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
      this.container.appendChild(toast);

      setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
      }, duration);
    }
  };

  // Add slideOut animation
  const toastStyle = document.createElement('style');
  toastStyle.textContent = `
    @keyframes slideOut {
      from { opacity: 1; transform: translateX(0); }
      to { opacity: 0; transform: translateX(100px); }
    }
  `;
  document.head.appendChild(toastStyle);

  /* ============================================
     COPY TO CLIPBOARD
     ============================================ */
  const Clipboard = {
    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        Toast.show('Скопировано в буфер обмена', 'success', 2000);
      } catch (err) {
        Toast.show('Не удалось скопировать', 'danger', 2000);
      }
    }
  };

  /* ============================================
     LAZY LOADING IMAGES
     ============================================ */
  const LazyImages = {
    init() {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            observer.unobserve(img);
          }
        });
      });

      document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
    }
  };

  /* ============================================
     BACK TO TOP
     ============================================ */
  const BackToTop = {
    init() {
      const btn = document.createElement('button');
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px;"><polyline points="18 15 12 9 6 15"/></svg>';
      btn.className = 'btn btn-primary';
      btn.style.cssText = `
        position: fixed;
        bottom: 2rem;
        left: 2rem;
        z-index: 500;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        padding: 0;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
      `;
      btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
      document.body.appendChild(btn);

      window.addEventListener('scroll', () => {
        const show = window.scrollY > 500;
        btn.style.opacity = show ? '1' : '0';
        btn.style.visibility = show ? 'visible' : 'hidden';
      });
    }
  };

  /* ============================================
     SMOOTH SCROLL FOR ANCHOR LINKS
     ============================================ */
  const SmoothScroll = {
    init() {
      document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
          const target = document.querySelector(anchor.getAttribute('href'));
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        });
      });
    }
  };

  /* ============================================
     CONFIRMATION DIALOG
     ============================================ */
  const ConfirmDialog = {
    show(message, onConfirm) {
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay active';
      overlay.innerHTML = `
        <div class="modal" style="max-width: 400px; text-align: center;">
          <svg viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2" style="width:48px;height:48px;margin:0 auto 1rem;">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <h3 style="margin-bottom: 1rem; color: var(--text-primary);">${message}</h3>
          <div style="display: flex; gap: 1rem; justify-content: center;">
            <button class="btn btn-secondary" id="confirmCancel">Отмена</button>
            <button class="btn btn-danger" id="confirmOk">Подтвердить</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
      });

      overlay.querySelector('#confirmCancel').addEventListener('click', () => overlay.remove());
      overlay.querySelector('#confirmOk').addEventListener('click', () => {
        overlay.remove();
        onConfirm();
      });
    }
  };

  /* ============================================
     API HELPERS
     ============================================ */
  const API = {
    async request(url, options = {}) {
      const defaultOptions = {
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
      };

      try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        Toast.show(`Ошибка: ${error.message}`, 'danger');
        throw error;
      }
    },

    get(url) { return this.request(url, { method: 'GET' }); },
    post(url, data) { return this.request(url, { method: 'POST', body: JSON.stringify(data) }); },
    put(url, data) { return this.request(url, { method: 'PUT', body: JSON.stringify(data) }); },
    delete(url) { return this.request(url, { method: 'DELETE' }); }
  };

  /* ============================================
     INITIALIZATION
     ============================================ */
  document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    MobileMenu.init();
    NavbarScroll.init();
    ScrollAnimations.init();
    FormHelpers.init();
    RippleEffect.init();
    Toast.init();
    LazyImages.init();
    BackToTop.init();
    SmoothScroll.init();

    // Theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => ThemeManager.toggle());
    }

    console.log('Мир Самозанятых v7.0 initialized');
  });

  /* ============================================
     EXPORTS (for inline scripts)
     ============================================ */
  window.MirSamozanyatykh = {
    ThemeManager,
    Toast,
    Clipboard,
    API,
    ConfirmDialog,
    SkeletonLoader
  };

})();

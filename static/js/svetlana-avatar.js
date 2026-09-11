/* Svetlana avatar asset loader.
 * Existing Canvas rendering remains the verified fallback.
 * When a real avatar image is added to static/images/svetlana, this script
 * automatically switches to it without requiring template changes.
 */
(function () {
  'use strict';

  const root = document.documentElement;
  const base = '/static/images/svetlana/';
  const variants = [
    { selector: '.svetlana-avatar', className: 'svetlana-avatar-image', candidates: ['svetlana-light.webp', 'svetlana-current.webp', 'svetlana-dark.webp'] },
    { selector: '.svetlana-mini-avatar', className: 'svetlana-mini-avatar-image', candidates: ['svetlana-light.webp', 'svetlana-current.webp', 'svetlana-dark.webp'] }
  ];

  function preferredCandidates() {
    const dark = root.getAttribute('data-theme') === 'dark';
    const themeFile = dark ? 'svetlana-dark.webp' : 'svetlana-light.webp';
    return [themeFile, 'svetlana-current.webp', dark ? 'svetlana-light.webp' : 'svetlana-dark.webp'];
  }

  function findAvailableImage(candidates) {
    return new Promise((resolve) => {
      let index = 0;
      function next() {
        if (index >= candidates.length) {
          resolve(null);
          return;
        }
        const src = base + candidates[index++];
        const img = new Image();
        img.onload = () => resolve(src);
        img.onerror = next;
        img.src = src;
      }
      next();
    });
  }

  async function mount() {
    const source = await findAvailableImage(preferredCandidates());
    if (!source) {
      // No replacement asset yet: keep the existing Canvas implementation.
      root.removeAttribute('data-svetlana-avatar');
      return;
    }

    document.querySelectorAll('.svetlana-avatar, .svetlana-mini-avatar').forEach((container) => {
      let image = container.querySelector('img.svetlana-avatar-image, img.svetlana-mini-avatar-image');
      if (!image) {
        image = document.createElement('img');
        image.className = container.classList.contains('svetlana-mini-avatar')
          ? 'svetlana-mini-avatar-image'
          : 'svetlana-avatar-image';
        image.alt = 'Светлана — ИИ-помощник';
        image.decoding = 'async';
        image.loading = 'eager';
        container.appendChild(image);
      }
      image.dataset.avatarLoading = 'true';
      image.src = source;
      image.onload = () => {
        image.dataset.avatarLoading = 'false';
      };
    });

    root.setAttribute('data-svetlana-avatar', 'image');
  }

  function init() {
    mount();

    // Re-evaluate when the user changes light/dark theme.
    new MutationObserver((mutations) => {
      if (mutations.some((m) => m.attributeName === 'data-theme')) {
        mount();
      }
    }).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();

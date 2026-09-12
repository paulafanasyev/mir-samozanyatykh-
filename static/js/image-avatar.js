/**
 * Image Avatar Renderer
 * Рендеринг аватара через WebP изображения с поддержкой тем
 */

class ImageAvatarRenderer {
  constructor() {
    this.container = null;
    this.imageElement = null;
    this.themeObserver = null;
    this.isVisible = true;
    
    // Пути к изображениям
    this.imagePaths = {
      current: '/static/images/svetlana/svetlana-current.webp',
      light: '/static/images/svetlana/svetlana-light.webp',
      dark: '/static/images/svetlana/svetlana-dark.webp'
    };
    
    console.log('[ImageAvatarRenderer] Constructor initialized');
  }
  
  /**
   * Инициализация рендерера
   * @param {HTMLElement} container - контейнер для аватара
   */
  async init(container) {
    this.container = container;
    
    // Создаем элемент изображения
    this.imageElement = document.createElement('img');
    this.imageElement.className = 'svetlana-avatar-image';
    this.imageElement.alt = 'Светлана - AI ассистент';
    this.imageElement.style.display = 'block';
    this.imageElement.style.width = '100%';
    this.imageElement.style.height = 'auto';
    this.imageElement.style.objectFit = 'contain';
    this.imageElement.style.borderRadius = '1rem';
    
    // Устанавливаем начальное изображение
    this.updateTheme();
    
    // Добавляем в контейнер
    container.appendChild(this.imageElement);
    
    // Подписываемся на изменение темы
    this.setupThemeObserver();
    
    // Обработчик ошибки загрузки
    this.imageElement.onerror = () => {
      console.warn('[ImageAvatarRenderer] Failed to load image, trying fallback...');
      this.tryFallbackImage();
    };
    
    // Обработчик успешной загрузки
    this.imageElement.onload = () => {
      console.log('[ImageAvatarRenderer] Image loaded successfully');
    };
    
    console.log('[ImageAvatarRenderer] Initialized');
  }
  
  /**
   * Настройка наблюдателя за темой
   */
  setupThemeObserver() {
    this.themeObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          console.log('[ImageAvatarRenderer] Theme changed, updating image...');
          this.updateTheme();
        }
      });
    });
    
    this.themeObserver.observe(document.documentElement, { 
      attributes: true,
      attributeFilter: ['data-theme']
    });
  }
  
  /**
   * Обновление изображения в зависимости от темы
   */
  updateTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    let imagePath;
    
    if (currentTheme === 'dark') {
      imagePath = this.imagePaths.dark;
    } else {
      imagePath = this.imagePaths.light;
    }
    
    // Проверяем существование изображения перед загрузкой
    this.preloadImage(imagePath).then(exists => {
      if (exists) {
        this.imageElement.src = imagePath;
      } else {
        // Если специфичного изображения нет, используем универсальное
        this.imageElement.src = this.imagePaths.current;
      }
    }).catch(() => {
      this.imageElement.src = this.imagePaths.current;
    });
  }
  
  /**
   * Предварительная загрузка изображения для проверки существования
   * @param {string} src - путь к изображению
   * @returns {Promise<boolean>} - существует ли изображение
   */
  preloadImage(src) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = src;
    });
  }
  
  /**
   * Попытка загрузить fallback изображение
   */
  tryFallbackImage() {
    if (this.imageElement.src !== this.imagePaths.current) {
      console.log('[ImageAvatarRenderer] Trying fallback image...');
      this.imageElement.src = this.imagePaths.current;
    } else {
      console.error('[ImageAvatarRenderer] All images failed to load');
    }
  }
  
  /**
   * Рендеринг аватара в указанном состоянии
   * @param {string} state - состояние аватара
   */
  async render(state) {
    if (!this.imageElement) return;
    
    // Удаляем предыдущие классы состояний
    this.imageElement.classList.remove('state-idle', 'state-listening', 'state-thinking', 'state-speaking', 'state-error');
    
    // Добавляем класс текущего состояния
    this.imageElement.classList.add(`state-${state}`);
    
    // Применяем визуальные эффекты в зависимости от состояния
    switch(state) {
      case 'idle':
        this.imageElement.style.filter = 'none';
        this.imageElement.style.animation = 'breathing 3s ease-in-out infinite';
        break;
        
      case 'listening':
        this.imageElement.style.filter = 'brightness(1.05) contrast(1.02)';
        this.imageElement.style.animation = 'pulse-gentle 2s ease-in-out infinite';
        break;
        
      case 'thinking':
        this.imageElement.style.filter = 'grayscale(0.1) brightness(1.02)';
        this.imageElement.style.animation = 'subtle-glow 2.5s ease-in-out infinite';
        break;
        
      case 'speaking':
        this.imageElement.style.filter = 'brightness(1.08)';
        this.imageElement.style.animation = 'speaking-bounce 1.5s ease-in-out infinite';
        break;
        
      case 'error':
        this.imageElement.style.filter = 'sepia(0.3) brightness(0.95)';
        this.imageElement.style.animation = 'none';
        break;
        
      default:
        this.imageElement.style.filter = 'none';
        this.imageElement.style.animation = 'none';
    }
    
    console.log(`[ImageAvatarRenderer] Rendered state: ${state}`);
  }
  
  /**
   * Установить эмоцию
   * @param {string} emotion - название эмоции
   */
  async setEmotion(emotion) {
    console.log(`[ImageAvatarRenderer] Setting emotion: ${emotion}`);
    
    // Для статических изображений эмоции пока не поддерживаются
    // В будущем можно использовать спрайты или морфинг
    
    if (!this.imageElement) return;
    
    // Простая эмуляция через CSS фильтры
    switch(emotion) {
      case 'happy':
        this.imageElement.style.filter = 'brightness(1.1) saturate(1.1)';
        break;
      case 'sad':
        this.imageElement.style.filter = 'brightness(0.95) saturate(0.9)';
        break;
      case 'surprised':
        this.imageElement.style.filter = 'brightness(1.15) contrast(1.05)';
        break;
      default:
        this.imageElement.style.filter = 'none';
    }
  }
  
  /**
   * Установить визему для lip-sync
   * @param {string} viseme - код виземы
   */
  async setViseme(viseme) {
    // Для статических изображений lip-sync не поддерживается
    // В будущем можно использовать спрайты с разными позициями рта
    console.log(`[ImageAvatarRenderer] Viseme: ${viseme}`);
  }
  
  /**
   * Установить данные для lip-sync
   * @param {Uint8Array} audioData - аудио данные
   */
  async setLipSync(audioData) {
    // Не поддерживается для статических изображений
  }
  
  /**
   * Показать аватар
   */
  show() {
    this.isVisible = true;
    if (this.imageElement) {
      this.imageElement.style.display = 'block';
    }
  }
  
  /**
   * Скрыть аватар
   */
  hide() {
    this.isVisible = false;
    if (this.imageElement) {
      this.imageElement.style.display = 'none';
    }
  }
  
  /**
   * Очистка ресурсов
   */
  async destroy() {
    console.log('[ImageAvatarRenderer] Destroying...');
    
    if (this.themeObserver) {
      this.themeObserver.disconnect();
      this.themeObserver = null;
    }
    
    if (this.imageElement && this.imageElement.parentNode) {
      this.imageElement.parentNode.removeChild(this.imageElement);
    }
    
    this.imageElement = null;
    this.container = null;
  }
}

// Экспорт в глобальную область
window.ImageAvatarRenderer = ImageAvatarRenderer;

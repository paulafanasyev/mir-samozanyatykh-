/**
 * Avatar Renderer - Многоуровневая система рендеринга аватара
 * Архитектура: 3D → Image → Canvas Fallback
 */

class AvatarRenderer {
  constructor(containerId) {
    this.containerId = containerId;
    this.container = null;
    this.currentRenderer = null;
    this.fallbackRenderer = null;
    
    // Доступные рендереры в порядке приоритета
    this.avatarRenderers = {
      Realtime3DAvatar: null, // Будет подключен при наличии Three.js и GLB модели
      ImageAvatar: new window.ImageAvatarRenderer(),
      CanvasFallback: new window.CanvasAvatarRenderer()
    };
    
    console.log('[AvatarRenderer] Constructor initialized');
  }
  
  /**
   * Инициализация системы рендеринга
   */
  async init() {
    this.container = document.getElementById(this.containerId);
    if (!this.container) {
      console.error('[AvatarRenderer] Container not found:', this.containerId);
      return;
    }
    
    console.log('[AvatarRenderer] Starting initialization...');
    
    try {
      // Определяем лучший доступный рендерер
      await this.selectBestRenderer();
      
      if (!this.currentRenderer) {
        throw new Error('No available renderer');
      }
      
      // Инициализируем выбранный рендерер
      await this.currentRenderer.init(this.container);
      console.log(`[AvatarRenderer] Initialized with ${this.getCurrentRendererName()}`);
      
      // Инициализируем fallback на случай ошибки
      if (this.fallbackRenderer) {
        await this.fallbackRenderer.init(this.container);
        this.fallbackRenderer.hide();
        console.log('[AvatarRenderer] Fallback renderer ready');
      }
      
    } catch (error) {
      console.error('[AvatarRenderer] Initialization error:', error);
      
      // Пытаемся использовать fallback
      if (this.fallbackRenderer) {
        console.warn('[AvatarRenderer] Switching to fallback renderer...');
        this.currentRenderer = this.fallbackRenderer;
        await this.currentRenderer.init(this.container);
      }
    }
  }
  
  /**
   * Выбор лучшего доступного рендерера
   */
  async selectBestRenderer() {
    // 1. Проверяем поддержку 3D (Three.js + WebGL)
    if (this.is3DAvatarAvailable()) {
      console.log('[AvatarRenderer] 3D avatar available');
      // Пока не используем 3D, так как модель еще не загружена
      // this.currentRenderer = this.avatarRenderers.Realtime3DAvatar;
      // this.fallbackRenderer = this.avatarRenderers.ImageAvatar;
    }
    
    // 2. Проверяем доступность изображений
    if (this.isImageAvatarAvailable()) {
      console.log('[AvatarRenderer] Image avatar available');
      this.currentRenderer = this.avatarRenderers.ImageAvatar;
      this.fallbackRenderer = this.avatarRenderers.CanvasFallback;
      return;
    }
    
    // 3. Используем Canvas fallback
    console.log('[AvatarRenderer] Using Canvas fallback');
    this.currentRenderer = this.avatarRenderers.CanvasFallback;
  }
  
  /**
   * Проверка доступности 3D аватара
   */
  is3DAvatarAvailable() {
    // Проверяем наличие Three.js
    if (typeof THREE === 'undefined') {
      return false;
    }
    
    // Проверяем поддержку WebGL
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return false;
    } catch (e) {
      return false;
    }
    
    // Проверяем наличие GLB модели
    const modelPath = '/static/models/svetlana/svetlana.glb';
    // Здесь можно добавить проверку существования файла через fetch HEAD запрос
    
    return true; // Пока возвращаем true, но не используем 3D
  }
  
  /**
   * Проверка доступности image аватара
   */
  isImageAvatarAvailable() {
    // Проверяем наличие хотя бы одного изображения
    const avatarImages = [
      '/static/images/svetlana/svetlana-current.webp',
      '/static/images/svetlana/svetlana-light.webp',
      '/static/images/svetlana/svetlana-dark.webp'
    ];
    
    // Простая эвристика - считаем что изображения доступны
    // В продакшене можно добавить реальную проверку через Image onload
    return true;
  }
  
  /**
   * Получить имя текущего рендерера
   */
  getCurrentRendererName() {
    if (this.currentRenderer === this.avatarRenderers.Realtime3DAvatar) {
      return 'Realtime3DAvatar';
    } else if (this.currentRenderer === this.avatarRenderers.ImageAvatar) {
      return 'ImageAvatar';
    } else if (this.currentRenderer === this.avatarRenderers.CanvasFallback) {
      return 'CanvasFallback';
    }
    return 'Unknown';
  }
  
  /**
   * Рендеринг аватара в указанном состоянии
   * @param {string} state - состояние аватара
   */
  async render(state) {
    if (!this.currentRenderer) {
      console.error('[AvatarRenderer] No renderer available');
      return;
    }
    
    try {
      await this.currentRenderer.render(state);
    } catch (error) {
      console.error('[AvatarRenderer] Render error:', error);
      
      // Переключаемся на fallback
      if (this.fallbackRenderer && this.fallbackRenderer !== this.currentRenderer) {
        console.warn('[AvatarRenderer] Switching to fallback due to render error');
        this.currentRenderer.hide?.();
        this.currentRenderer = this.fallbackRenderer;
        this.fallbackRenderer.show();
        await this.currentRenderer.render(state);
      }
    }
  }
  
  /**
   * Установить эмоцию
   * @param {string} emotion - название эмоции
   */
  async setEmotion(emotion) {
    if (this.currentRenderer?.setEmotion) {
      await this.currentRenderer.setEmotion(emotion);
    }
  }
  
  /**
   * Установить визему для lip-sync
   * @param {string} viseme - код виземы
   */
  async setViseme(viseme) {
    if (this.currentRenderer?.setViseme) {
      await this.currentRenderer.setViseme(viseme);
    }
  }
  
  /**
   * Установить данные для lip-sync
   * @param {Uint8Array} audioData - аудио данные
   */
  async setLipSync(audioData) {
    if (this.currentRenderer?.setLipSync) {
      await this.currentRenderer.setLipSync(audioData);
    }
  }
  
  /**
   * Показать аватар
   */
  show() {
    this.currentRenderer?.show?.();
  }
  
  /**
   * Скрыть аватар
   */
  hide() {
    this.currentRenderer?.hide?.();
  }
  
  /**
   * Очистка ресурсов
   */
  async destroy() {
    console.log('[AvatarRenderer] Destroying...');
    
    if (this.currentRenderer?.destroy) {
      await this.currentRenderer.destroy();
    }
    
    if (this.fallbackRenderer?.destroy) {
      await this.fallbackRenderer.destroy();
    }
    
    this.currentRenderer = null;
    this.fallbackRenderer = null;
    this.container = null;
  }
}

// Экспорт в глобальную область
window.AvatarRenderer = AvatarRenderer;

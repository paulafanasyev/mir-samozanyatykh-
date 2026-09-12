/**
 * Lip-Sync System
 * Система синхронизации губ с аудио
 * Архитектура: audio → viseme → avatar
 */

class LipSyncSystem {
  constructor(avatarRenderer) {
    this.avatarRenderer = avatarRenderer;
    this.audioContext = null;
    this.analyser = null;
    this.isAnalyzing = false;
    this.animationFrame = null;
    
    // Поддерживаемые виземы (ARPAbet фонетический алфавит)
    this.supportedVisemes = [
      'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 
      'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 
      'OY', 'UH', 'UW', 'B', 'CH', 'D', 
      'DH', 'F', 'G', 'HH', 'JH', 'K', 
      'L', 'M', 'N', 'NG', 'P', 'R', 
      'S', 'SH', 'T', 'TH', 'V', 'W', 
      'Y', 'Z', 'ZH'
    ];
    
    // Карта визем к типам открытия рта
    this.visemeMap = this.createVisemeMap();
    
    // Текущая визема
    this.currentViseme = null;
    this.visemeTimeout = null;
    
    // Параметры анализа
    this.smoothingFactor = 0.3;
    this.lastVolume = 0;
    
    console.log('[LipSyncSystem] Constructor initialized');
  }
  
  /**
   * Создание карты визем
   */
  createVisemeMap() {
    return {
      // Широко открытый рот
      open_wide: ['AA', 'AE', 'AH', 'AO', 'AW', 'AY'],
      
      // Полуоткрытый рот
      open_mid: ['EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW'],
      
      // Закрытый рот (губы сомкнуты)
      closed: ['B', 'M', 'P'],
      
      // Зубы на губе
      teeth_lip: ['F', 'V'],
      
      // Округленный рот
      rounded: ['W', 'UW', 'OW'],
      
      // Узкий рот
      narrow: ['Y', 'IY', 'EH'],
      
      // Нейтральный
      neutral: ['CH', 'D', 'DH', 'G', 'HH', 'JH', 'K', 'L', 'N', 'NG', 'R', 'S', 'SH', 'T', 'TH', 'Z', 'ZH']
    };
  }
  
  /**
   * Инициализация системы
   */
  async init() {
    try {
      // Инициализируем Audio Context для анализа аудио
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioContext = new AudioContext();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.analyser.smoothingTimeConstant = this.smoothingFactor;
        
        console.log('[LipSyncSystem] Audio context initialized');
      } else {
        console.warn('[LipSyncSystem] Web Audio API not supported, using fallback');
      }
    } catch (error) {
      console.error('[LipSyncSystem] Failed to initialize audio context:', error);
    }
  }
  
  /**
   * Обработка аудио буфера для определения виземы
   * @param {AudioBuffer} audioBuffer - аудио данные
   */
  async processAudio(audioBuffer) {
    if (!this.analyser || !this.isAnalyzing) return;
    
    try {
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.analyser);
      source.connect(this.audioContext.destination);
      
      // Анализируем частоты для определения виземы
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.analyser.getByteFrequencyData(dataArray);
      
      // Определяем доминирующую частоту
      const dominantFreqIndex = this.findDominantFrequency(dataArray);
      
      // Преобразуем частоту в визему
      const viseme = this.frequencyToViseme(dominantFreqIndex, dataArray);
      
      // Устанавливаем визему на аватаре
      await this.setViseme(viseme);
      
      source.start(0);
    } catch (error) {
      console.error('[LipSyncSystem] Error processing audio:', error);
    }
  }
  
  /**
   * Поиск доминирующей частоты
   * @param {Uint8Array} dataArray - данные частот
   * @returns {number} индекс доминирующей частоты
   */
  findDominantFrequency(dataArray) {
    let maxAmplitude = 0;
    let dominantFreqIndex = 0;
    
    for (let i = 0; i < dataArray.length; i++) {
      if (dataArray[i] > maxAmplitude) {
        maxAmplitude = dataArray[i];
        dominantFreqIndex = i;
      }
    }
    
    return dominantFreqIndex;
  }
  
  /**
   * Преобразование частоты в визему
   * @param {number} freqIndex - индекс частоты
   * @param {Uint8Array} dataArray - полные данные частот
   * @returns {string} код виземы
   */
  frequencyToViseme(freqIndex, dataArray) {
    // Простая эвристика на основе частотных диапазонов
    // В реальности нужен ML модель или фонетический анализ
    
    const volume = this.calculateVolume(dataArray);
    
    // Если тихо - нейтральная визема
    if (volume < 20) {
      return 'neutral';
    }
    
    // Низкие частоты - округленные гласные
    if (freqIndex < 20) {
      const visemes = this.visemeMap.open_wide;
      return visemes[Math.floor(Math.random() * visemes.length)];
    }
    
    // Средние частоты - открытые гласные
    if (freqIndex < 60) {
      const visemes = this.visemeMap.open_mid;
      return visemes[Math.floor(Math.random() * visemes.length)];
    }
    
    // Высокие частоты - согласные
    if (freqIndex < 100) {
      const visemes = [...this.visemeMap.closed, ...this.visemeMap.teeth_lip];
      return visemes[Math.floor(Math.random() * visemes.length)];
    }
    
    // По умолчанию
    return 'AA';
  }
  
  /**
   * Расчет громкости аудио
   * @param {Uint8Array} dataArray - данные частот
   * @returns {number} уровень громкости
   */
  calculateVolume(dataArray) {
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    return sum / dataArray.length;
  }
  
  /**
   * Установка виземы
   * @param {string} viseme - код виземы
   */
  async setViseme(viseme) {
    if (this.currentViseme === viseme) return;
    
    this.currentViseme = viseme;
    
    // Передаем визему рендереру аватара
    if (this.avatarRenderer) {
      await this.avatarRenderer.setViseme(viseme);
    }
    
    // Автоматически сбрасываем визему через короткое время
    if (this.visemeTimeout) {
      clearTimeout(this.visemeTimeout);
    }
    
    this.visemeTimeout = setTimeout(() => {
      this.currentViseme = null;
      if (this.avatarRenderer) {
        this.avatarRenderer.setViseme(null);
      }
    }, 100); // Визема длится около 100мс
  }
  
  /**
   * Запуск анализа аудио
   */
  async startAnalysis() {
    if (this.isAnalyzing) return;
    
    this.isAnalyzing = true;
    console.log('[LipSyncSystem] Starting analysis...');
    
    // Запускаем цикл анализа
    this.analyzeLoop();
  }
  
  /**
   * Цикл анализа аудио
   */
  analyzeLoop() {
    if (!this.isAnalyzing || !this.analyser) return;
    
    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(dataArray);
    
    // Вычисляем громкость
    const volume = this.calculateVolume(dataArray);
    
    // Сглаживаем изменение громкости
    this.lastVolume = this.lastVolume * 0.7 + volume * 0.3;
    
    // Преобразуем громкость в открытие рта
    const mouthOpenness = Math.min(1.0, this.lastVolume / 100);
    
    // Передаем данные о громкости для lip-sync
    if (this.avatarRenderer) {
      this.avatarRenderer.setLipSync(dataArray);
    }
    
    this.animationFrame = requestAnimationFrame(() => this.analyzeLoop());
  }
  
  /**
   * Остановка анализа
   */
  async stopAnalysis() {
    if (!this.isAnalyzing) return;
    
    this.isAnalyzing = false;
    console.log('[LipSyncSystem] Stopping analysis...');
    
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }
    
    if (this.visemeTimeout) {
      clearTimeout(this.visemeTimeout);
      this.visemeTimeout = null;
    }
    
    // Сброс текущей виземы
    this.currentViseme = null;
    if (this.avatarRenderer) {
      await this.avatarRenderer.setViseme(null);
    }
  }
  
  /**
   * Тестирование визем
   */
  async testVisemes() {
    console.log('[LipSyncSystem] Testing visemes...');
    
    const testSequence = ['AA', 'EH', 'IH', 'OW', 'UW', 'B', 'M', 'F', 'S'];
    
    for (let i = 0; i < testSequence.length; i++) {
      setTimeout(() => {
        console.log(`[LipSyncSystem] Testing: ${testSequence[i]}`);
        this.setViseme(testSequence[i]);
      }, i * 300);
    }
  }
  
  /**
   * Очистка ресурсов
   */
  async destroy() {
    await this.stopAnalysis();
    
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
    
    this.analyser = null;
    this.avatarRenderer = null;
    
    console.log('[LipSyncSystem] Destroyed');
  }
}

// Экспорт в глобальную область
window.LipSyncSystem = LipSyncSystem;

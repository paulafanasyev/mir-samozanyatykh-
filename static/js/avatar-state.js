/**
 * Система состояний Светланы
 * Управляет визуальными состояниями аватара
 */

class SvetlanaState {
  constructor() {
    this.states = {
      IDLE: 'idle',
      LISTENING: 'listening',
      THINKING: 'thinking',
      SPEAKING: 'speaking',
      ERROR: 'error'
    };
    
    this.currentState = this.states.IDLE;
    this.previousState = null;
    this.stateCallbacks = {};
    
    this.init();
  }
  
  init() {
    this.updateUI();
  }
  
  /**
   * Установить новое состояние
   * @param {string} newState - одно из IDLE, LISTENING, THINKING, SPEAKING, ERROR
   */
  setState(newState) {
    if (this.isValidState(newState)) {
      this.previousState = this.currentState;
      this.currentState = newState;
      
      console.log(`[SvetlanaState] ${this.previousState} → ${newState}`);
      
      this.updateUI();
      
      // Вызываем callback для нового состояния
      if (this.stateCallbacks[newState]) {
        this.stateCallbacks[newState](newState, this.previousState);
      }
      
      // Вызываем общий callback
      if (this.stateCallbacks['*']) {
        this.stateCallbacks['*'](newState, this.previousState);
      }
    } else {
      console.error(`[SvetlanaState] Invalid state: ${newState}`);
    }
  }
  
  /**
   * Проверка валидности состояния
   */
  isValidState(state) {
    return Object.values(this.states).includes(state);
  }
  
  /**
   * Получить текущее состояние
   */
  getState() {
    return this.currentState;
  }
  
  /**
   * Получить предыдущее состояние
   */
  getPreviousState() {
    return this.previousState;
  }
  
  /**
   * Подписаться на изменение конкретного состояния
   * @param {string} state - состояние для подписки
   * @param {function} callback - функция обратного вызова
   */
  onStateChange(state, callback) {
    this.stateCallbacks[state] = callback;
  }
  
  /**
   * Подписаться на любое изменение состояния
   * @param {function} callback - функция обратного вызова
   */
  onAnyStateChange(callback) {
    this.stateCallbacks['*'] = callback;
  }
  
  /**
   * Обновить UI в соответствии с текущим состоянием
   */
  updateUI() {
    // Обновляем индикаторы состояния
    const indicators = document.querySelectorAll('.avatar-state-indicator');
    indicators.forEach(indicator => {
      // Удаляем все классы состояний
      Object.values(this.states).forEach(state => {
        indicator.classList.remove(state);
      });
      
      // Добавляем текущее состояние
      indicator.classList.add(this.currentState);
      indicator.setAttribute('data-state', this.currentState);
    });
    
    // Обновляем текстовое описание
    const descriptions = document.querySelectorAll('.avatar-state-description');
    const descriptionTexts = {
      [this.states.IDLE]: 'Готова к общению',
      [this.states.LISTENING]: 'Слушает...',
      [this.states.THINKING]: 'Думает...',
      [this.states.SPEAKING]: 'Говорит...',
      [this.states.ERROR]: 'Ошибка соединения'
    };
    
    descriptions.forEach(desc => {
      desc.textContent = descriptionTexts[this.currentState] || '';
    });
    
    // Обновляем ARIA атрибуты для доступности
    const avatarContainer = document.getElementById('svetlana-avatar-container');
    if (avatarContainer) {
      const ariaLabels = {
        [this.states.IDLE]: 'Светлана готова к общению',
        [this.states.LISTENING]: 'Светлана слушает ваш запрос',
        [this.states.THINKING]: 'Светлана обрабатывает запрос',
        [this.states.SPEAKING]: 'Светлана отвечает',
        [this.states.ERROR]: 'Ошибка, попробуйте позже'
      };
      avatarContainer.setAttribute('aria-label', ariaLabels[this.currentState]);
    }
  }
  
  /**
   * Получить текстовое описание состояния
   */
  getStateDescription(state = this.currentState) {
    const descriptions = {
      [this.states.IDLE]: 'Готова к общению',
      [this.states.LISTENING]: 'Слушает...',
      [this.states.THINKING]: 'Думает...',
      [this.states.SPEAKING]: 'Говорит...',
      [this.states.ERROR]: 'Ошибка соединения'
    };
    return descriptions[state] || '';
  }
}

// Экспорт в глобальную область
window.SvetlanaState = SvetlanaState;

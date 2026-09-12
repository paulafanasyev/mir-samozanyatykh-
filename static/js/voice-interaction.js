class VoiceInteraction {
  constructor(svetlanaState, avatarRenderer, lipSyncSystem) {
    this.svetlanaState = svetlanaState;
    this.avatarRenderer = avatarRenderer;
    this.lipSyncSystem = lipSyncSystem;
    
    this.recognition = null;
    this.isListening = false;
    this.audioContext = null;
    this.sessionId = null;
    
    // Состояния для управления голосовым взаимодействием
    this.voiceStates = {
      IDLE: 'idle',
      LISTENING: 'listening',
      PROCESSING: 'processing',
      SPEAKING: 'speaking'
    };
    
    this.init();
  }
  
  async init() {
    // Инициализируем Web Speech API если доступно
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'ru-RU'; // Русский язык по умолчанию
      
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.handleUserInput(transcript);
      };
      
      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        this.svetlanaState.setState(this.svetlanaState.states.ERROR);
        
        // Через короткое время возвращаемся к ожиданию
        setTimeout(() => {
          this.svetlanaState.setState(this.svetlanaState.states.IDLE);
        }, 2000);
      };
      
      this.recognition.onend = () => {
        if (this.isListening) {
          // Автоматически перезапускаем слушание если оно было активно
          this.startListening();
        }
      };
    } else {
      console.warn('Web Speech API not supported in this browser');
    }
    
    // Инициализируем систему lip-sync
    if (this.lipSyncSystem) {
      await this.lipSyncSystem.init();
    }
  }
  
  async toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      await this.startListening();
    }
  }
  
  async startListening() {
    if (!this.recognition) {
      console.error('Speech recognition not available');
      return;
    }
    
    try {
      this.isListening = true;
      this.svetlanaState.setState(this.svetlanaState.states.LISTENING);
      this.recognition.start();
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      this.svetlanaState.setState(this.svetlanaState.states.ERROR);
    }
  }
  
  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }
  
  async handleUserInput(text) {
    // Останавливаем слушание
    this.stopListening();
    
    // Переходим к обработке запроса
    this.svetlanaState.setState(this.svetlanaState.states.THINKING);
    
    // Отправляем текст в чат и получаем ответ
    try {
      const response = await this.sendToBackend(text);
      
      // Отображаем ответ в чате
      this.displayResponse(text, response);
      
      // Проигрываем ответ Светлане
      await this.speakResponse(response);
    } catch (error) {
      console.error('Error handling user input:', error);
      this.svetlanaState.setState(this.svetlanaState.states.ERROR);
      
      // Показываем сообщение об ошибке
      this.displayErrorResponse(error.message);
    }
  }
  
  async sendToBackend(userMessage) {
    // Отправляем сообщение на реальный backend API
    try {
      const response = await fetch('/api/svetlana/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Для cookies сессии
        body: JSON.stringify({ 
          message: userMessage,
          session_id: this.sessionId || undefined
        })
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Пользователь не авторизован, используем fallback ответ
          return this.getFallbackResponse(userMessage);
        }
        throw new Error(`Backend error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Сохраняем session_id для последующих запросов
      this.sessionId = data.session_id;
      
      return data.reply;
    } catch (error) {
      console.error('Error sending to backend:', error);
      // Fallback ответ при ошибке
      return this.getFallbackResponse(userMessage);
    }
  }
  
  getFallbackResponse(userMessage) {
    // Локальные ответы для демонстрации без авторизации
    const message = userMessage.toLowerCase();
    
    if (message.includes('привет') || message.includes('здравствуй')) {
      return 'Здравствуйте! Я Светлана, ваш ИИ-ассистент. Чем могу помочь?';
    }
    if (message.includes('налог') || message.includes('ндфл')) {
      return 'Самозанятые платят НПД: 4% с физлиц, 6% с юрлиц и ИП. Налоговый вычет 10 000 ₽ применяется автоматически.';
    }
    if (message.includes('вычет') || message.includes('10000')) {
      return 'Налоговый вычет 10 000 ₽ для самозанятых. Применяется в приложении Мой налог.';
    }
    if (message.includes('договор') || message.includes('контракт')) {
      return 'Я могу помочь с шаблонами: ГПД, счёт, акт выполненных работ, чек НПД.';
    }
    if (message.includes('тариф') || message.includes('цена') || message.includes('стоимость')) {
      return 'Тарифы: START (бесплатно), PRO (300 ₽/мес), BUSINESS (990 ₽/мес), ENTERPRISE (индивидуально).';
    }
    if (message.includes('регистрац') || message.includes('как стать')) {
      return 'Для регистрации самозанятым скачайте приложение Мой налог или обратитесь в ФНС.';
    }
    if (message.includes('штраф') || message.includes('пени')) {
      return 'Штраф за неуплату НПД — 20% от суммы + пени 1/300 ставки рефинансирования.';
    }
    if (message.includes('ип') || message.includes('индивидуальный предприниматель')) {
      return 'Самозанятость и ИП — разные режимы. Самозанятый не платит фиксированные взносы, но имеет ограничения по доходу (2.4 млн ₽/год).';
    }
    if (message.includes('грант') || message.includes('поддержк') || message.includes('субсидия')) {
      return 'В разделе Гранты вы найдёте актуальные программы поддержки.';
    }
    if (message.includes('crm') || message.includes('клиент') || message.includes('контакт')) {
      return 'CRM помогает управлять клиентами. Добавляйте контакты, отслеживайте статусы.';
    }
    if (message.includes('спасиб') || message.includes('благодар')) {
      return 'Всегда рада помочь! Обращайтесь ещё!';
    }
    if (message.includes('пока') || message.includes('до свидания')) {
      return 'До встречи! Успехов в вашей работе!';
    }
    
    return 'Я пока работаю в режиме базы знаний. Задайте вопрос о налогах, договорах, тарифах или грантах. Также я могу помочь с регистрацией самозанятого и информацией о грантах.';
  }
  
  displayResponse(userMessage, aiResponse) {
    // Находим чат и добавляем сообщения
    const chatContainer = document.querySelector('.chat-messages');
    if (!chatContainer) return;
    
    // Добавляем сообщение пользователя
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'message user-message';
    userMsgDiv.innerHTML = `
      <div class="message-content">${this.escapeHtml(userMessage)}</div>
      <div class="message-time">${this.getCurrentTime()}</div>
    `;
    chatContainer.appendChild(userMsgDiv);
    
    // Добавляем сообщение AI
    const aiMsgDiv = document.createElement('div');
    aiMsgDiv.className = 'message ai-message';
    aiMsgDiv.innerHTML = `
      <div class="message-content">${this.escapeHtml(aiResponse)}</div>
      <div class="message-time">${this.getCurrentTime()}</div>
    `;
    chatContainer.appendChild(aiMsgDiv);
    
    // Прокручиваем к последнему сообщению
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  
  displayErrorResponse(errorMessage) {
    const chatContainer = document.querySelector('.chat-messages');
    if (!chatContainer) return;
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message error-message';
    errorDiv.innerHTML = `
      <div class="message-content">Ошибка: ${this.escapeHtml(errorMessage)}</div>
      <div class="message-time">${this.getCurrentTime()}</div>
    `;
    chatContainer.appendChild(errorDiv);
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  
  async speakResponse(text) {
    // Используем Web Speech API для озвучивания ответа
    if ('speechSynthesis' in window) {
      this.svetlanaState.setState(this.svetlanaState.states.SPEAKING);
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      // При завершении речи возвращаемся к ожиданию
      utterance.onend = () => {
        this.svetlanaState.setState(this.svetlanaState.states.IDLE);
      };
      
      // Начинаем синхронизацию губ во время речи
      if (this.lipSyncSystem) {
        this.lipSyncSystem.startAnalysis();
      }
      
      speechSynthesis.speak(utterance);
    } else {
      // Если Web Speech API недоступен, просто возвращаемся к ожиданию
      setTimeout(() => {
        this.svetlanaState.setState(this.svetlanaState.states.IDLE);
      }, text.length * 50); // Приблизительное время для "прочтения" текста
    }
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  getCurrentTime() {
    const now = new Date();
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
  }
  
  async destroy() {
    this.stopListening();
    
    if (this.lipSyncSystem) {
      await this.lipSyncSystem.destroy();
    }
    
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
    }
  }
}

// Export для использования в других модулях
window.VoiceInteraction = VoiceInteraction;
